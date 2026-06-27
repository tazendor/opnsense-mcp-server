# Implementation Plan: OPNsense MCP Server

**Branch**: `001-opnsense-mcp-server` | **Date**: 2026-06-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-opnsense-mcp-server/spec.md`

## Summary

A Python MCP server that proxies the documented OPNsense REST API as typed MCP tools.
The server authenticates with OPNsense via API key/secret over HTTPS, exposes tools for
System, Firewall (rules + aliases + NAT), Interfaces, Routes, DHCP, DNS Resolver, and
Services domains, supports both stdio and HTTP/SSE transports, and logs every API call
and its outcome. No caching; no invented behavior; all tool shapes derive from OPNsense's
documented API for the current stable release.

**Key technical choices** (see `research.md` for rationale):
- MCP layer: `FastMCP` from the `mcp` Python SDK
- HTTP client: `httpx.AsyncClient` with `httpx.BasicAuth` and `httpx.Timeout`
- Configuration: stdlib `dataclass` + `tomllib`; env vars override config file
- Testing: `pytest` + `pytest-asyncio` + `respx` (httpx mock)
- Packaging: `uv`, `src/` layout, `pyproject.toml`

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**:
- `mcp` ≥ 1.0 (FastMCP, stdio and SSE transports)
- `httpx` ≥ 0.27 (async HTTP client with BasicAuth and Timeout)

**Dev Dependencies**:
- `pytest` ≥ 8.0
- `pytest-asyncio` ≥ 0.23
- `respx` ≥ 0.21 (httpx mock)
- `mypy` ≥ 1.10
- `ruff` ≥ 0.5

**Storage**: N/A — stateless proxy; no persistent storage.

**Testing**: `pytest` with `pytest-asyncio`; unit tests mock httpx via `respx`;
integration tests require live OPNsense instance (marked `pytest.mark.integration`,
skipped when `OPNSENSE_*` env vars absent).

**Target Platform**: macOS 13+, Linux (wherever Claude Desktop/Code runs);
CPython 3.12+ required.

**Project Type**: MCP server (subprocess daemon for stdio; ASGI service for HTTP/SSE).

**Performance Goals**:
- Tool call overhead ≤ 50 ms above OPNsense API latency (no processing beyond auth,
  request forwarding, and error wrapping).
- Server startup ≤ 5 s with valid credentials (SC-004).
- Startup failure (invalid credentials) ≤ 10 s (SC-004).

**Constraints**:
- `mypy --strict` zero errors on every commit.
- `ruff check` zero lint errors; `ruff format` enforced.
- No caching of OPNsense state (FR-004 — all data reflects live state).
- No behaviour beyond what OPNsense REST API documents (FR-006).
- HTTPS only for OPNsense connections (FR-007).

**Scale/Scope**: Single OPNsense instance per server process. stdio: 1 MCP client.
HTTP/SSE: multiple concurrent clients (FastMCP handles concurrency).

## Constitution Check

*GATE: Must pass before implementation. Re-checked after Phase 1 design.*

### I. Simplicity First ✅

- No caching, no abstraction layers beyond the necessary `OPNsenseClient` wrapper.
- Domain modules each expose a `register_tools(mcp, client)` function — three lines
  to add a new tool. No factory patterns, no plugin system.
- Config is a plain dataclass, not a Pydantic model — stdlib sufficient.
- Tools are thin closures: forward request, return response, log outcome.

### II. Idiomatic Python ✅

- Python 3.12+; `src/` layout; `pyproject.toml`.
- stdlib `tomllib` (not a third-party TOML library); `dataclasses`; `typing`.
- `ruff` enforces PEP 8 and formatting; no manual style rules.
- `httpx` and `mcp` are the only runtime dependencies.

### III. Full Type Safety ✅

- All tool functions, client methods, and config fields are fully type-annotated.
- `mypy --strict` is a quality gate (no bypass allowed).
- OPNsense response shapes are `TypedDict`; the `Any` from raw JSON is narrowed
  at the client boundary before propagating into domain code.
- `OPNsenseAPIError` is a typed dataclass, not a bare `Exception`.

### IV. Specification-Driven Development ✅

- Every MCP tool corresponds to exactly one documented OPNsense REST API endpoint
  (see `contracts/`).
- No tool implements OPNsense behaviour not documented in the current stable API.
- Scope (v1 domains, service modules) is defined in the spec and not extended
  during implementation without a spec amendment.

### V. Test-Driven Development ✅ (mandatory)

- Tests are written first for every domain module (see task ordering in tasks.md).
- Unit tests mock `OPNsenseClient` directly; tools are callable as plain async
  functions independent of the MCP layer.
- Integration tests cover the full stack against a live OPNsense instance.
- Contract tests verify tool input schemas match the contracts in `contracts/`.
- The TDD cycle (red → green → refactor) is enforced per task.

**Complexity Tracking**: No violations. No justification required.

## Project Structure

### Documentation (this feature)

```text
specs/001-opnsense-mcp-server/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: Technology decisions and rationale
├── data-model.md        # Phase 1: Entity types and client design
├── quickstart.md        # Phase 1: End-to-end validation guide
├── contracts/
│   ├── system.md        # MCP tool contracts: System domain
│   ├── firewall.md      # MCP tool contracts: Firewall domain
│   ├── interfaces.md    # MCP tool contracts: Interfaces domain
│   ├── routes.md        # MCP tool contracts: Routes domain
│   ├── dhcp.md          # MCP tool contracts: DHCP domain
│   ├── dns.md           # MCP tool contracts: DNS Resolver domain
│   └── services.md      # MCP tool contracts: Services domain
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
src/
└── opnsense_mcp/
    ├── __init__.py
    ├── __main__.py          # CLI entry point: parse transport arg, start server
    ├── config.py            # Config dataclass + from_env() + from_toml()
    ├── client.py            # OPNsenseClient (httpx.AsyncClient wrapper)
    ├── errors.py            # OPNsenseAPIError, ToolError
    ├── server.py            # create_server(config) → FastMCP with all tools registered
    └── tools/
        ├── __init__.py
        ├── system.py        # register_tools(mcp, client) for system domain
        ├── firewall.py      # register_tools for firewall domain
        ├── interfaces.py    # register_tools for interfaces domain
        ├── routes.py        # register_tools for routes domain
        ├── dhcp.py          # register_tools for DHCP domain
        ├── dns.py           # register_tools for DNS domain
        └── services.py      # register_tools for services domain

tests/
├── conftest.py              # Shared fixtures: mock_client, test_config
├── unit/
│   ├── test_config.py       # Config loading, validation, env var precedence
│   ├── test_client.py       # OPNsenseClient: auth, timeouts, error mapping
│   ├── test_errors.py       # Error type construction and formatting
│   └── tools/
│       ├── test_system.py
│       ├── test_firewall.py
│       ├── test_interfaces.py
│       ├── test_routes.py
│       ├── test_dhcp.py
│       ├── test_dns.py
│       └── test_services.py
├── integration/
│   ├── conftest.py          # Skip marker when OPNSENSE_* vars absent
│   ├── test_system.py
│   ├── test_firewall.py
│   ├── test_network.py      # interfaces + routes + DHCP
│   └── test_dns.py
└── contract/
    └── test_tool_schemas.py # Verify tool input schemas match contracts/

pyproject.toml               # Project metadata, dependencies, ruff + mypy config
uv.lock                      # Locked dependency versions
```

**Structure Decision**: Single project, `src/` layout (PEP 517/518). No frontend.
No separate backend/API split — the MCP server IS the API. Tools are co-located
with the domain they cover (one module per domain).

## Tool Inventory

Total MCP tools exposed (v1):

| Domain | Tools | Count |
|---|---|---|
| System | `system_status`, `system_firmware_status`, `system_config_backup` | 3 |
| Firewall rules | `firewall_rule_list/get/add/update/delete/apply` | 6 |
| Firewall aliases | `firewall_alias_list/get_uuid/add/update/delete/apply` | 6 |
| Firewall NAT | `firewall_nat_list/add/update/delete/apply` | 5 |
| Interfaces | `interface_list/config/arp_table/ndp_table` | 4 |
| Routes | `route_list/add/update/delete/apply` | 5 |
| DHCP | `dhcp_lease_list/settings_get/static_list` | 3 |
| DNS | `dns_settings_get/host_override_list/add/update/delete/apply` | 6 |
| Services | `service_status/start/stop/restart` | 4 |
| **Total** | | **42** |
