# Quickstart: OPNsense MCP Server Validation

This guide walks through end-to-end validation of each user story after implementation.
It is a validation/run guide — not a tutorial. See `contracts/` for tool schemas and
`data-model.md` for type definitions.

## Prerequisites

- OPNsense instance accessible over HTTPS from the development machine.
- OPNsense API key and secret created under **System → Access → Users → Edit →
  API keys** with appropriate privileges.
- Python 3.12+ installed.
- `uv` installed: `curl -Lsf https://astral.sh/uv/install.sh | sh`

## Installation

```bash
# From the repository root
uv sync
```

## Configuration

### Option A: Environment variables (recommended for local testing)

```bash
export OPNSENSE_URL="https://192.168.1.1"
export OPNSENSE_API_KEY="your-api-key"
export OPNSENSE_API_SECRET="your-api-secret"
export OPNSENSE_VERIFY_TLS="false"          # for self-signed certs only
export OPNSENSE_TRANSPORT="stdio"           # or "http"
```

### Option B: Config file

Create `~/.config/opnsense-mcp/config.toml`:

```toml
url = "https://192.168.1.1"
api_key = "your-api-key"
api_secret = "your-api-secret"
verify_tls = false
transport = "stdio"
```

## Running the server

### stdio mode (for Claude Desktop / Claude Code)

```bash
uv run opnsense-mcp
```

Add to Claude Desktop's `claude_desktop_config.json`:

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

### HTTP/SSE mode (for remote clients)

```bash
OPNSENSE_TRANSPORT=http OPNSENSE_HTTP_PORT=8000 uv run opnsense-mcp
```

Verify the server is running:
```bash
curl http://127.0.0.1:8000/sse
# Expected: SSE event stream response headers (HTTP 200 text/event-stream)
```

## Running the test suite

```bash
# Unit tests only (no OPNsense instance required)
uv run pytest -m "not integration" -v

# Integration tests (requires OPNSENSE_* env vars pointing to a live instance)
uv run pytest -m integration -v

# Full suite with quality gates
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src/
uv run pytest
```

---

## Validating User Story 1: Query Firewall & System Status

**Via MCP client (Claude Code / Desktop)**:

1. Ask: *"What is the current firmware version and uptime of the firewall?"*
   - Expected: `system_status` tool called; response includes `product_version` and `uptime`.

2. Ask: *"List all network interfaces and their IP addresses."*
   - Expected: `interface_config` tool called; each interface name maps to its IP and status.

3. Simulate OPNsense being unreachable (set `OPNSENSE_URL` to an invalid host):
   - Expected: Tool call returns a clear timeout error message, not a hang or generic error.

**Via integration test**:
```bash
uv run pytest tests/integration/test_system.py -v
```
Expected: All tests pass; `system_status` returns a dict with `versions` key.

---

## Validating User Story 2: Manage Firewall Rules & Aliases

1. Ask: *"List all firewall rules."*
   - Expected: `firewall_rule_list` called; returns list of rules (may be empty).

2. Ask: *"Add a firewall rule to block all traffic from 203.0.113.0/24 to any destination."*
   - Expected: `firewall_rule_add` called with correct action/source; returns a UUID.

3. Ask: *"List firewall rules again and confirm the new rule appears."*
   - Expected: Rule with the described source appears in the list.

4. Ask: *"Apply the firewall changes."*
   - Expected: `firewall_rule_apply` called; OPNsense confirms success.

5. Ask: *"Delete the rule we just created."* (provide UUID from step 2)
   - Expected: `firewall_rule_delete` called; followed by `firewall_rule_apply` to commit.

**Via integration test**:
```bash
uv run pytest tests/integration/test_firewall.py -v
```
Expected: Create → list → verify → apply → delete → apply cycle completes without errors.

---

## Validating User Story 3: Manage Network Configuration

1. Ask: *"Show all active DHCP leases."*
   - Expected: `dhcp_lease_list` called; returns list (may be empty in test environment).

2. Ask: *"Add a DNS host override: resolve 'test.example.com' to 192.0.2.1."*
   - Expected: `dns_host_override_add` called with `host=test`, `domain=example.com`,
     `rr=A`, `server=192.0.2.1`; returns UUID.

3. Ask: *"Apply the DNS changes."*
   - Expected: `dns_apply` called; OPNsense confirms success.

4. Ask: *"Remove the test host override we just added."* (provide UUID)
   - Expected: `dns_host_override_delete` then `dns_apply` called.

**Via integration test**:
```bash
uv run pytest tests/integration/test_dns.py -v
```

---

## Validating User Story 4: Secure Server Configuration & Deployment

**Valid credentials (startup success)**:
```bash
uv run opnsense-mcp
# Expected: Server starts, logs "Startup complete", ready for connections
```

**Missing API key (startup failure)**:
```bash
OPNSENSE_API_KEY="" uv run opnsense-mcp
# Expected: Exits immediately with error: "api_key is required"
```

**Wrong credentials (startup failure)**:
```bash
OPNSENSE_API_KEY="wrong" OPNSENSE_API_SECRET="wrong" uv run opnsense-mcp
# Expected: Exits with error identifying 401 Unauthorized from OPNsense during startup check
```

**Self-signed certificate (TLS disabled)**:
```bash
OPNSENSE_VERIFY_TLS=false uv run opnsense-mcp
# Expected: Connects successfully; logs "TLS verification disabled" warning
```

**HTTP/SSE port conflict**:
```bash
# Occupy port 8000 first, then start the server on the same port
nc -l 8000 &
OPNSENSE_TRANSPORT=http OPNSENSE_HTTP_PORT=8000 uv run opnsense-mcp
# Expected: Exits with error identifying port 8000 is already in use
```

---

## Verifying Diagnostic Logging (FR-014)

After running any tool call, verify the server produced a log record:

```
# Expected log entry format (exact format defined in implementation)
2026-06-27T12:00:00Z GET  /api/core/dashboard/get  status=200  outcome=success
2026-06-27T12:00:01Z POST /api/firewall/filter/add_rule  status=400  outcome=error  message="..."
```

All calls, their status codes, and outcomes MUST appear in the log output accessible
to the operator (stderr or log file, per FR-014).
