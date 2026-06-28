# OPNsense MCP Server

[![CI](https://github.com/tazendor/opnsense-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/tazendor/opnsense-mcp-server/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/tazendor-opnsense-mcp)](https://pypi.org/project/tazendor-opnsense-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Built with SpecKit](https://img.shields.io/badge/built%20with-SpecKit-6f42c1)](https://github.com/github/spec-kit)

**GitHub**: https://github.com/tazendor/opnsense-mcp-server

A Python [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes the OPNsense REST API to AI clients such as Claude Desktop and Claude Code.

## What it does

The server proxies 43 OPNsense API endpoints across eight domains as MCP tools, letting AI clients query and mutate firewall state through natural language.

| Domain | Tools | Capabilities |
|--------|-------|--------------|
| System | 3 | Status, firmware check, config backup |
| Firewall | 17 | Rule and alias CRUD, NAT port forwards, apply |
| Interfaces | 4 | Interface list, config, ARP/NDP tables |
| DHCP | 3 | Lease list, settings, static mappings |
| Routes | 5 | Static route CRUD and apply |
| DNS | 6 | Unbound settings and host override CRUD |
| IDS | 1 | Ruleset list |
| Services | 4 | Start/stop/restart/status for core modules |

Mutating operations follow OPNsense's staged-then-apply model: changes are staged by `_add`/`_update`/`_delete` tools and committed by the corresponding `_apply` tool.

## Requirements

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)
- OPNsense **26.1+** with API access enabled

> **Compatibility**: Tested against OPNsense 26.1.10. The 26.x release series
> made breaking REST API changes — Kea replaced ISC DHCPv4 (`kea/*` paths),
> port-forward NAT moved to Destination NAT (`firewall/d_nat/*`), and the system
> status endpoint changed. Older releases are not supported.

## Installation

```bash
pip install tazendor-opnsense-mcp
```

Or from source:

```bash
git clone https://github.com/tazendor/opnsense-mcp-server.git
cd opnsense-mcp-server
uv sync
```

## Configuration

### Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPNSENSE_URL` | yes | — | OPNsense base URL; must start with `https://` |
| `OPNSENSE_API_KEY` | yes | — | OPNsense API key |
| `OPNSENSE_API_SECRET` | yes | — | OPNsense API secret |
| `OPNSENSE_VERIFY_TLS` | no | `true` | Set `false` to skip TLS verification (self-signed certs) |
| `OPNSENSE_TRANSPORT` | no | `stdio` | `stdio` or `http` |
| `OPNSENSE_HTTP_HOST` | no | `127.0.0.1` | Bind address for HTTP transport |
| `OPNSENSE_HTTP_PORT` | no | `8000` | Port for HTTP transport |
| `OPNSENSE_CONNECT_TIMEOUT` | no | `10.0` | Seconds to wait for OPNsense TCP connection |
| `OPNSENSE_READ_TIMEOUT` | no | `60.0` | Seconds to wait for OPNsense API response |

### Config file

Create `~/.config/opnsense-mcp/config.toml`:

```toml
url = "https://192.168.1.1"
api_key = "your-api-key"
api_secret = "your-api-secret"
verify_tls = false      # omit or set true for valid certificates
transport = "stdio"     # or "http"
http_host = "127.0.0.1"
http_port = 8000
connect_timeout = 10.0
read_timeout = 60.0
```

Environment variables override config file values. The config file is optional — environment variables alone are sufficient.

## Running

### stdio transport (Claude Desktop / Claude Code)

stdio is the default and recommended transport. The MCP client launches the server as a subprocess and communicates over stdin/stdout. No network port is opened.

```bash
uv run opnsense-mcp
```

**Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "opnsense": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/opnsense-mcp-server", "opnsense-mcp"],
      "env": {
        "OPNSENSE_URL": "https://192.168.1.1",
        "OPNSENSE_API_KEY": "your-api-key",
        "OPNSENSE_API_SECRET": "your-api-secret"
      }
    }
  }
}
```

**Claude Code** — add to `.mcp.json` in your project root, or `~/.claude/mcp.json` for global use:

```json
{
  "mcpServers": {
    "opnsense": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/opnsense-mcp-server", "opnsense-mcp"],
      "env": {
        "OPNSENSE_URL": "https://192.168.1.1",
        "OPNSENSE_API_KEY": "your-api-key",
        "OPNSENSE_API_SECRET": "your-api-secret"
      }
    }
  }
}
```

If you installed via `pip install tazendor-opnsense-mcp`, replace the `uv run --project ...` invocation with the installed entry point:

```json
{
  "mcpServers": {
    "opnsense": {
      "command": "opnsense-mcp",
      "env": {
        "OPNSENSE_URL": "https://192.168.1.1",
        "OPNSENSE_API_KEY": "your-api-key",
        "OPNSENSE_API_SECRET": "your-api-secret"
      }
    }
  }
}
```

### Streamable HTTP transport

HTTP transport runs the server as a long-lived process that listens for MCP connections over HTTP. Use this when you want multiple clients to share a single server instance, or when stdio is not practical (e.g. a remote host or a containerised deployment).

Start the server:

```bash
OPNSENSE_TRANSPORT=http \
OPNSENSE_HTTP_HOST=127.0.0.1 \
OPNSENSE_HTTP_PORT=8000 \
uv run opnsense-mcp
```

The server binds at `http://<HTTP_HOST>:<HTTP_PORT>/mcp`. With the defaults above that is `http://127.0.0.1:8000/mcp`.

> **Security**: HTTP mode does not enforce payload size limits, rate limiting, or
> client authentication. The server prints a warning to this effect at startup.
> For anything beyond local use, place the server behind a reverse proxy (nginx,
> Caddy, etc.) that adds those controls and restricts access to trusted clients.

**Claude Code** — add to `.mcp.json`:

```json
{
  "mcpServers": {
    "opnsense": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

**Other MCP clients** — connect to `http://127.0.0.1:8000/mcp` using the [MCP Streamable HTTP](https://modelcontextprotocol.io/docs/concepts/transports#streamable-http) transport. The server follows the standard MCP session handshake: send an `initialize` request, then a `notifications/initialized` notification (both carrying the `mcp-session-id` header returned by the server), then issue tool calls.

## Development

```bash
# Run unit and contract tests (no OPNsense instance needed)
uv run pytest -m "not integration"

# Run integration tests against a live instance
OPNSENSE_URL=https://... OPNSENSE_API_KEY=... OPNSENSE_API_SECRET=... \
  uv run pytest -m integration -v

# Quality gates
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy --strict src/
```

All unit and contract tests pass without a live OPNsense instance (`pytest -m "not integration"`).

## Security notes

- **HTTPS enforced**: the server refuses to start with an `http://` URL.
- **Credentials never logged**: `api_key` and `api_secret` flow only into the HTTP `Authorization` header and are absent from all log output.
- **Structured audit log**: every OPNsense API call is logged to stderr as a JSON line with stable fields — `ts` (UTC ISO-8601), `method`, `path`, `status_code`, `outcome`. Example:
  ```json
  {"ts":"2026-06-28T12:00:00+00:00","method":"GET","path":"core/system/status","status_code":200,"outcome":"success"}
  ```
- **Input validation**: UUID and alias-name parameters are validated against strict allowlist patterns before being interpolated into API paths, preventing path-traversal attempts.
- **TLS verification warning**: when `OPNSENSE_VERIFY_TLS=false`, a warning is printed at startup.
- **HTTP transport warning**: when HTTP transport is enabled, a warning is printed at startup listing the controls that are not enforced (payload limits, rate limiting, client authentication). See the [Streamable HTTP transport](#streamable-http-transport) section for hardening guidance.
