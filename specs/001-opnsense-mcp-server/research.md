# Research: OPNsense MCP Server

## 1. MCP Python SDK

**Decision**: Use `FastMCP` from the `mcp` package (official Anthropic MCP Python SDK).

**Rationale**: FastMCP is the high-level API that handles tool registration, input schema
generation from type annotations, transport switching (stdio/SSE), and error formatting.
The low-level `Server` API requires significant boilerplate for the same result.

**Tool registration pattern**:

```python
# Domain modules expose a register_tools() function accepting mcp + client
def register_tools(mcp: FastMCP, client: OPNsenseClient) -> None:
    @mcp.tool()
    async def firewall_rule_list() -> str:
        """List all firewall filter rules."""
        return json.dumps(await client.post("/api/firewall/filter/search_rule", {}))
```

This closure pattern keeps tool logic testable independently of the MCP layer: unit tests
call the underlying async function directly; integration tests exercise the registered tool.

**Lifespan / client sharing**: The `OPNsenseClient` (an `httpx.AsyncClient` wrapper) is
created once, shared across all tools via closure capture, and torn down when the server
stops. FastMCP lifespan hooks or a simple async context manager at startup handles this.

**Transport selection**: `FastMCP.run(transport="stdio")` or `FastMCP.run(transport="sse")`
selects the transport at startup based on the configured value.

**Alternatives considered**:
- Low-level `mcp.Server`: rejected — excessive boilerplate for no benefit here.
- Writing a custom MCP protocol implementation: rejected — YAGNI, SDK handles all edge cases.

---

## 2. Async HTTP Client

**Decision**: `httpx.AsyncClient` with HTTP Basic Auth and explicit timeout object.

**Rationale**: httpx is async-native, cleanly typed, and supports all OPNsense authentication
and TLS requirements with a minimal, idiomatic API. It is the de-facto standard for async
HTTP in modern Python.

```python
import httpx

async with httpx.AsyncClient(
    base_url=config.url,
    auth=httpx.BasicAuth(config.api_key, config.api_secret),
    verify=config.verify_tls,
    timeout=httpx.Timeout(
        connect=config.connect_timeout,
        read=config.read_timeout,
    ),
) as client:
    ...
```

**OPNsense authentication**: HTTP Basic Auth where username = API key,
password = API secret. OPNsense rejects requests with missing or wrong credentials
with HTTP 401.

**TLS**: `verify=False` disables certificate verification for self-signed certs
(configurable); `verify=True` is the secure default.

**Error mapping**:

| httpx exception | MCP error surfaced |
|-----------------|--------------------|
| `ConnectTimeout` | Connection timeout exceeded |
| `ReadTimeout` | Read timeout exceeded |
| `ConnectError` | OPNsense unreachable |
| HTTP 4xx/5xx | Status code + response body forwarded |

**Alternatives considered**:
- `aiohttp`: rejected — less idiomatic API, weaker type stubs, no stdlib-style timeout object.
- `requests` (sync): rejected — blocks the event loop; incompatible with async MCP server.

---

## 3. Configuration Loading

**Decision**: Python `dataclass` with `__post_init__` validation, loading from environment
variables first, then a TOML file, then defaults.

**Rationale**: `tomllib` is stdlib in Python 3.11+ (target is 3.12+). A dataclass with
`__post_init__` covers all validation needs without pulling in Pydantic.

**Priority order**: environment variables → TOML file → defaults.

**Environment variables**:

| Variable | Description | Default |
|---|---|---|
| `OPNSENSE_URL` | OPNsense base URL (HTTPS required) | — (required) |
| `OPNSENSE_API_KEY` | OPNsense API key | — (required) |
| `OPNSENSE_API_SECRET` | OPNsense API secret | — (required) |
| `OPNSENSE_VERIFY_TLS` | `true`/`false` | `true` |
| `OPNSENSE_CONNECT_TIMEOUT` | Seconds (float) | `10.0` |
| `OPNSENSE_READ_TIMEOUT` | Seconds (float) | `60.0` |
| `OPNSENSE_TRANSPORT` | `stdio` or `http` | `stdio` |
| `OPNSENSE_HTTP_HOST` | Bind host for HTTP transport | `127.0.0.1` |
| `OPNSENSE_HTTP_PORT` | Bind port for HTTP transport | `8000` |

**TOML config file**: `~/.config/opnsense-mcp/config.toml` (keys match env var names
lowercased, without the `OPNSENSE_` prefix).

**Alternatives considered**:
- Pydantic `BaseSettings`: rejected — adds a third-party dependency for functionality
  achievable with stdlib; violates Principle II (prefer stdlib).
- CLI arguments only: rejected — doesn't support the "no source code modification"
  requirement (FR-009) well.

---

## 4. Test Tooling

**Decision**: `pytest` + `pytest-asyncio` + `respx` for httpx mocking.

**Rationale**:
- `pytest-asyncio` allows `async def` test functions natively.
- `respx` is the canonical mock library for `httpx`; it intercepts at the transport layer,
  so tests exercise the full client code path without making real network calls.
- Unit tests call domain functions directly with a `respx`-mocked httpx client.
- Integration tests require `OPNSENSE_*` environment variables pointing to a live instance;
  skipped automatically when variables are absent.

**Test configuration** (`pyproject.toml`):
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

**Marker for integration tests**:
```python
pytestmark = pytest.mark.integration
```

Filtered out in default runs: `pytest -m "not integration"`.

**Alternatives considered**:
- `pytest-httpx`: rejected — `respx` has a cleaner API for pattern-based route mocking
  and is more widely used with `httpx`.
- Manual `unittest.mock.patch`: rejected — doesn't integrate with httpx's transport layer.

---

## 5. OPNsense API Patterns

**Apply/reconfigure pattern**: Many OPNsense API domains use a two-phase model: mutations
(add/update/delete) stage changes in OPNsense's internal state, and a separate `apply` or
`reconfigure` call commits them to the running configuration. Each domain has its own apply
endpoint. MCP tools expose both phases as distinct tools (per FR-002 / FR-006 — no invented
abstractions).

**Search endpoints**: Most list operations use `POST` with a search payload
(`current`, `rowCount`, `searchPhrase`). Default `rowCount=-1` returns all records.

**UUID references**: Create operations return a UUID; update and delete operations accept
the UUID as a path parameter. Tools that create resources return the UUID in their response
so callers can immediately reference the created resource.

**Service control**: Core services (unbound, dhcpv4, etc.) each expose
`/api/{module}/service/start`, `/stop`, `/restart`, `/status` endpoints. The `services`
domain tools parameterise over a fixed set of documented service module names.

**Supported service modules** (scope for v1):
`unbound`, `dhcpv4`, `firmware`, `ids`, `cron`

---

## 6. Package Management

**Decision**: `uv` with `pyproject.toml` and `uv.lock`.

**Rationale**: `uv` is the fastest Python package manager, produces a lock file, and is
the modern standard for Python project management. Aligns with Principle II (idiomatic
Python tooling).

**Project layout**: `src/` layout (PEP 517/518). Package name: `opnsense_mcp`.
Entry point: `opnsense-mcp` CLI command.
