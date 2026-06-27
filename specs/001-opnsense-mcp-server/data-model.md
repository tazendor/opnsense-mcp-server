# Data Model: OPNsense MCP Server

## Overview

This server is a typed proxy — it does not own persistent state. Its entities are:

1. **Configuration** — how to connect to OPNsense and which transport to use.
2. **OPNsenseClient** — the authenticated async HTTP session.
3. **Domain Types** — TypedDicts mirroring OPNsense API response shapes.
4. **Error Types** — structured error payloads surfaced to MCP clients.

All domain types mirror OPNsense's documented JSON response structures exactly
(FR-004, FR-006). No fields are added, renamed, or removed.

---

## Config

```python
from dataclasses import dataclass, field
from typing import Literal

@dataclass
class Config:
    # Required
    url: str                                         # e.g. "https://192.168.1.1"
    api_key: str
    api_secret: str

    # TLS
    verify_tls: bool = True

    # Timeouts
    connect_timeout: float = 10.0                    # seconds
    read_timeout: float = 60.0                       # seconds

    # Transport
    transport: Literal["stdio", "http"] = "stdio"
    http_host: str = "127.0.0.1"
    http_port: int = 8000

    def __post_init__(self) -> None:
        if not self.url.startswith("https://"):
            raise ValueError("url must use https://")
        if not self.api_key:
            raise ValueError("api_key is required")
        if not self.api_secret:
            raise ValueError("api_secret is required")
        if self.connect_timeout <= 0:
            raise ValueError("connect_timeout must be positive")
        if self.read_timeout <= 0:
            raise ValueError("read_timeout must be positive")
        if not (1 <= self.http_port <= 65535):
            raise ValueError("http_port must be 1–65535")
```

**Loading order**: `Config.from_env()` reads environment variables;
`Config.from_toml(path)` reads a TOML file; both fall back to field defaults.
The server entry point merges both sources with env vars taking priority.

---

## OPNsenseClient

Not a data entity but a key design component. Documented here for type-contract clarity.

```python
import httpx
from typing import Any

class OPNsenseClient:
    """Authenticated async HTTP client for the OPNsense REST API."""

    def __init__(self, config: Config) -> None: ...

    async def __aenter__(self) -> "OPNsenseClient": ...
    async def __aexit__(self, *args: object) -> None: ...

    async def get(self, path: str) -> dict[str, Any]:
        """GET /api/{path}. Parses response as JSON. Raises OPNsenseAPIError on non-2xx."""

    async def get_text(self, path: str) -> str:
        """GET /api/{path}. Returns raw response body as a string without JSON parsing.
        Use for endpoints that return non-JSON content (e.g. XML config backup).
        Raises OPNsenseAPIError on non-2xx."""

    async def post(
        self,
        path: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """POST /api/{path} with JSON body. Raises OPNsenseAPIError on non-2xx."""
```

Both `get` and `post` log the request path and outcome before returning or raising.
`OPNsenseAPIError` carries `status_code: int` and `body: dict[str, Any]`.

---

## Error Types

```python
from dataclasses import dataclass

@dataclass
class OPNsenseAPIError(Exception):
    status_code: int
    body: dict[str, Any]       # raw OPNsense error response
    path: str                  # API path that failed
    method: str                # "GET" or "POST"
```

The MCP tool layer catches `OPNsenseAPIError` and returns a structured error string
to the MCP client containing `status_code`, `path`, and the OPNsense `body` — no
information is discarded or reworded.

Connection-level errors (`httpx.ConnectTimeout`, `httpx.ReadTimeout`,
`httpx.ConnectError`) are caught and re-raised as human-readable `ToolError` messages
identifying which timeout was exceeded.

---

## Domain Types

All types below are `TypedDict` definitions. They mirror OPNsense's documented JSON
response structure for the current stable release. Fields marked `# optional` may be
absent depending on OPNsense version or configuration.

### System

```python
class SystemStatus(TypedDict):
    # From GET /api/core/dashboard/get
    versions: dict[str, str]       # e.g. {"product_version": "24.7.4"}
    cpu: dict[str, Any]            # CPU usage breakdown
    memory: dict[str, Any]         # Memory usage breakdown
    uptime: str

class FirmwareStatus(TypedDict):
    # From GET /api/firmware/status/check
    status: str                    # "OK" | "update" | ...
    product_version: str
    product_latest: str            # optional
    updates: list[dict[str, Any]]  # optional; list of available updates
```

### Firewall Rules

```python
class FirewallRuleRow(TypedDict):
    # From POST /api/firewall/filter/search_rule (rows array)
    uuid: str
    enabled: str                   # "0" | "1"
    description: str
    action: str                    # "pass" | "block" | "reject"
    protocol: str
    source_net: str
    destination_net: str
    destination_port: str          # optional

class FirewallRuleDetail(TypedDict):
    # From GET /api/firewall/filter/get_rule/{uuid}
    rule: dict[str, Any]           # full rule object with all OPNsense fields
```

### Firewall Aliases

```python
class AliasRow(TypedDict):
    # From GET /api/firewall/alias/get (aliases.alias object values)
    name: str
    type: str                      # "host" | "network" | "port" | "url" | ...
    description: str
    content: str                   # newline-separated entries
    enabled: str                   # "0" | "1"

class AliasAddResult(TypedDict):
    result: str                    # "saved" on success
    uuid: str                      # UUID of new alias
```

### Interfaces

```python
class InterfaceName(TypedDict):
    # From GET /api/diagnostics/interface/getInterfaceNames
    # Map of internal name → friendly name, e.g. {"em0": "WAN"}
    pass  # returned as dict[str, str]

class InterfaceConfig(TypedDict):
    # From GET /api/diagnostics/interface/getInterfaceConfig
    # Each key is an interface name; value is a full config object
    macaddr: str
    ipaddr: str          # optional
    subnet: str          # optional
    status: str          # e.g. "up" | "down"
    mtu: str             # optional
```

### Routes

```python
class RouteRow(TypedDict):
    # From POST /api/routes/routes/searchroute (rows array)
    uuid: str
    disabled: str          # "0" | "1"
    network: str           # CIDR, e.g. "10.0.0.0/8"
    gateway: str
    descr: str             # optional
```

### DHCP

```python
class DHCPLease(TypedDict):
    # From POST /api/dhcpv4/leases/searchLease (rows array)
    ip: str
    mac: str
    hostname: str          # optional
    type: str              # "static" | "dynamic"
    starts: str            # optional; lease start time
    ends: str              # optional; lease end time
    status: str            # optional; "active" | "expired" | ...
```

### DNS Resolver (Unbound)

```python
class HostOverrideRow(TypedDict):
    # From GET /api/unbound/settings/searchHostOverride (rows array)
    uuid: str
    enabled: str           # "0" | "1"
    host: str
    domain: str
    rr: str                # record type: "A" | "AAAA" | "MX" | ...
    server: str            # IP address for A/AAAA records
    description: str       # optional

class UnboundSettings(TypedDict):
    # From GET /api/unbound/settings/get — nested settings object
    # Structure mirrors OPNsense's full Unbound configuration
    general: dict[str, Any]
```

### Services

```python
class ServiceStatus(TypedDict):
    # From GET /api/{module}/service/status
    status: str            # "running" | "stopped"
    name: str              # optional; human-readable service name

class ServiceActionResult(TypedDict):
    # From POST /api/{module}/service/start|stop|restart
    response: str          # OPNsense free-text confirmation
```

---

## Supported Service Modules (v1)

The `services` domain tools accept a `module` parameter constrained to:

| Module name | OPNsense service |
|---|---|
| `unbound` | DNS Resolver |
| `dhcpv4` | DHCP server (IPv4) |
| `firmware` | Firmware updater |
| `ids` | Intrusion Detection System |
| `cron` | Cron scheduler |

These are the service modules present in all standard OPNsense installations and
documented in the OPNsense REST API for the current stable release.

---

## Logging Record

Every API call produces a log entry (FR-014). The log record carries:

```python
class APILogRecord(TypedDict):
    timestamp: str          # ISO 8601
    method: str             # "GET" | "POST"
    path: str               # relative OPNsense API path
    status_code: int | None # None on connection error
    outcome: str            # "success" | "error" | "timeout"
    error_message: str      # optional; present when outcome != "success"
```

Startup, shutdown, and credential validation results are also logged as plain-text
messages at the appropriate level.
