# OPNsense MCP Server

A Python [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes the OPNsense REST API to AI clients such as Claude Desktop and Claude Code.

## What it does

The server proxies 42 OPNsense API endpoints across seven domains as MCP tools, letting AI clients query and mutate firewall state through natural language.

| Domain | Tools | Capabilities |
|--------|-------|--------------|
| System | 3 | Status, firmware check, config backup |
| Firewall | 17 | Rule and alias CRUD, NAT port forwards, apply |
| Interfaces | 4 | Interface list, config, ARP/NDP tables |
| DHCP | 3 | Lease list, settings, static mappings |
| Routes | 5 | Static route CRUD and apply |
| DNS | 6 | Unbound settings and host override CRUD |
| Services | 4 | Start/stop/restart/status for core modules |

Mutating operations follow OPNsense's staged-then-apply model: changes are staged by `_add`/`_update`/`_delete` tools and committed by the corresponding `_apply` tool.

## Requirements

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)
- OPNsense 24.x with API access enabled

## Installation

```bash
git clone <repo>
cd opnsense-mcp-server
uv sync
```

## Configuration

### Environment variables

```bash
export OPNSENSE_URL="https://192.168.1.1"       # required; must be https://
export OPNSENSE_API_KEY="your-api-key"           # required
export OPNSENSE_API_SECRET="your-api-secret"     # required
export OPNSENSE_VERIFY_TLS="false"               # only for self-signed certs
export OPNSENSE_TRANSPORT="stdio"                # or "http"
```

### Config file

Create `~/.config/opnsense-mcp/config.toml`:

```toml
url = "https://192.168.1.1"
api_key = "your-api-key"
api_secret = "your-api-secret"
verify_tls = false   # omit or set true for valid certificates
transport = "stdio"  # or "http"
```

Environment variables override config file values.

## Running

### stdio (Claude Desktop / Claude Code)

```bash
uv run opnsense-mcp
```

Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "opnsense": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/opnsense-mcp-server", "opnsense-mcp"],
      "env": {
        "OPNSENSE_URL": "https://192.168.1.1",
        "OPNSENSE_API_KEY": "...",
        "OPNSENSE_API_SECRET": "..."
      }
    }
  }
}
```

### HTTP (remote clients)

```bash
OPNSENSE_TRANSPORT=http OPNSENSE_HTTP_PORT=8000 uv run opnsense-mcp
```

The server validates credentials against OPNsense on startup and exits with a non-zero status if it cannot connect or authenticate, so bad configuration is caught before any client connects.

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

- HTTPS is enforced; the server refuses to start with an `http://` URL.
- Credentials are read from environment or config file and never logged.
- Every API call is logged to stderr with method, path, status code, and outcome for auditability.
- When `OPNSENSE_VERIFY_TLS=false`, a warning is printed at startup.
