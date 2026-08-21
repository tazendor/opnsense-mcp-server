# OPNsense MCP Server

[![CI](https://github.com/tazendor/opnsense-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/tazendor/opnsense-mcp-server/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/tazendor-opnsense-mcp)](https://pypi.org/project/tazendor-opnsense-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Built with SpecKit](https://img.shields.io/badge/built%20with-SpecKit-6f42c1)](https://github.com/github/spec-kit)

**GitHub**: https://github.com/tazendor/opnsense-mcp-server

A Python [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes the OPNsense REST API to AI clients such as Claude Desktop and Claude Code.

## What it does

The server exposes **223 OPNsense API operations as MCP tools across 14 subsystems**, letting AI clients inspect and administer firewall state through natural language. The complete generated inventory is in [`docs/mcp-tools.md`](docs/mcp-tools.md).

| Subsystem | Tools | Capabilities |
|-----------|------:|--------------|
| System | 12 | Status, configuration backup/restore, firmware operations, reboot/halt |
| Firewall | 17 | Rule and alias CRUD, destination NAT port forwards, apply |
| Interfaces | 10 | Interface state/tables and assignment CRUD/apply |
| Routes | 5 | Static route CRUD and apply |
| DHCP | 8 | Kea leases, settings, static mappings, apply |
| DNS / Unbound | 6 | Settings and host-override CRUD/apply |
| IDS / IPS | 4 | Ruleset/rule toggles and apply |
| Services | 4 | Start, stop, restart, and status for supported modules |
| OpenVPN | 24 | Instances, client overrides, sessions, routes, and static keys |
| IPsec | 50 | Connections, children, credentials, pools, endpoints, and sessions |
| WireGuard | 24 | Servers, clients, key material, service control, and status |
| Web Proxy (Squid) | 28 | Settings, PAC objects, remote blacklists, and service control |
| Captive Portal | 15 | Zones, sessions, and service control |
| Trust / Certificates | 16 | CAs, certificates, CRLs, settings, and certificate export/revocation |

Most mutating operations follow OPNsense's staged-then-apply model: changes are staged by `_add`/`_update`/`_delete` tools and committed by the corresponding `_apply` tool. The server additionally protects 13 high-risk operations with an explicit preview → confirmation-token → execute flow; see [High-risk operations](#high-risk-operations).

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
| `OPNSENSE_CONFIRM_TTL` | no | `120.0` | Lifetime in seconds for high-risk-operation confirmation tokens |

### Config file

Create `~/.config/opnsense-mcp/config.toml`:

```toml
url = "https://opnsense.example.invalid"
api_key = "your-api-key"
api_secret = "your-api-secret"
verify_tls = false      # omit or set true for valid certificates
transport = "stdio"     # or "http"
http_host = "127.0.0.1"
http_port = 8000
connect_timeout = 10.0
read_timeout = 60.0
confirm_ttl_seconds = 120.0
```

Environment variables override config-file values. The config file is optional — environment variables alone are sufficient.

## High-risk operations

Thirteen operations that can interrupt connectivity, destroy configuration, revoke trust, or disconnect groups of users require two calls:

1. Call the high-risk tool without `confirm`. The server validates the request, returns a single-use `confirm_token`, records an audit preview, and makes **no request** to OPNsense.
2. Repeat the exact same tool and arguments with `confirm` set to that token before it expires (120 seconds by default). The token is bound to that tool and argument set, cannot be reused, and is lost if the server restarts.

This confirmation flow covers system restore/firmware/reboot/halt, interface reassignment, selected VPN teardown operations, certificate revocation, and bulk captive-portal session disconnects. The full tool inventory marks each high-risk tool.

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
        "OPNSENSE_URL": "https://opnsense.example.invalid",
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
        "OPNSENSE_URL": "https://opnsense.example.invalid",
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
        "OPNSENSE_URL": "https://opnsense.example.invalid",
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
> For anything beyond local use, place the server behind a reverse proxy that adds
> those controls. A `Caddyfile.example` is included in the repository — copy it
> to `Caddyfile`, replace the placeholders, and run `caddy run`. It configures
> HTTP Basic auth, a 1 MB request body limit, and per-IP rate limiting.

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

## Docker

The repository contains a multi-stage Docker image. The builder uses `uv` with Python 3.12; the current runtime image is `python:3.14-slim-bookworm`. Only the built virtual environment is copied into the runtime image, which runs as non-root `appuser` (UID 1000). HTTP transport defaults to `192.0.2.1:8000` inside the container.

### Build

```bash
docker build -t opnsense-mcp .
```

### Run HTTP transport

Create an environment file outside the repository (it contains the OPNsense API credential), restrict its permissions, and pass it to Docker. It must at least provide `OPNSENSE_URL`, `OPNSENSE_API_KEY`, and `OPNSENSE_API_SECRET`; set `OPNSENSE_VERIFY_TLS=true` unless a deliberately trusted local certificate requires otherwise.

```bash
docker run -d \
  --name opnsense-mcp \
  -p 127.0.0.1:8000:8000 \
  --env-file /secure/path/opnsense-mcp.env \
  --read-only --tmpfs /tmp \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  opnsense-mcp
```

The current repository does not ship a Compose file or `.env.example`. The command above publishes only on loopback; for LAN or Internet-facing use, place an authenticated reverse proxy in front of the server. See [`Caddyfile.example`](Caddyfile.example) for a hardening example.

### stdio via Docker

You can run the server in stdio mode so that a client such as Claude Desktop or Claude Code spawns it as a subprocess:

```json
{
  "mcpServers": {
    "opnsense": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--read-only", "--tmpfs", "/tmp",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges:true",
        "-e", "OPNSENSE_TRANSPORT=stdio",
        "--env-file", "/secure/path/opnsense-mcp.env",
        "opnsense-mcp",
        "opnsense-mcp"
      ]
    }
  }
}
```

The `-i` flag keeps stdin open so the MCP protocol can flow through it. Omit `-p` — no port is needed in stdio mode.

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
- **Structured audit log**: every OPNsense API call is logged to stderr as a JSON line with stable fields — `ts` (UTC ISO-8601), `req_id` (UUID v4 per request), `method`, `path`, `status_code`, `outcome`. Example:
  ```json
  {"ts":"2026-06-28T12:00:00+00:00","req_id":"a3f1c2d4-...","method":"GET","path":"core/system/status","status_code":200,"outcome":"success"}
  ```
- **Input validation**: UUID and alias-name parameters are validated against strict allowlist patterns before being interpolated into API paths, preventing path-traversal attempts.
- **TLS verification warning**: when `OPNSENSE_VERIFY_TLS=false`, a warning is printed at startup.
- **HTTP transport warning**: when HTTP transport is enabled, a warning is printed at startup listing the controls that are not enforced (payload limits, rate limiting, client authentication). See the [Streamable HTTP transport](#streamable-http-transport) section for hardening guidance.
