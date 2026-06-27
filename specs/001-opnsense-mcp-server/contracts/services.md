# MCP Tool Contracts: Services Domain

Tools in this domain control the start, stop, restart, and status of core OPNsense
services. The `module` parameter identifies the service using its OPNsense API module
name.

**Supported modules** (v1 scope; defined by FR-011 and data-model.md):

| `module` value | Service |
|---|---|
| `unbound` | DNS Resolver (Unbound) |
| `dhcpv4` | DHCPv4 server |
| `firmware` | Firmware updater daemon |
| `ids` | Intrusion Detection System (Suricata) |
| `cron` | Cron scheduler |

Calling a tool with a `module` value not in this list returns a validation error
before any request is sent to OPNsense (FR-003).

---

## Tool: `service_status`

**Description**: Retrieve the running/stopped status of a core OPNsense service.

**OPNsense endpoint**: `GET /api/{module}/service/status`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "module": {
      "type": "string",
      "enum": ["unbound", "dhcpv4", "firmware", "ids", "cron"],
      "description": "OPNsense service module name"
    }
  },
  "required": ["module"]
}
```

**Output**: JSON object matching `ServiceStatus` from the data model.
Example: `{"status": "running"}`.

---

## Tool: `service_start`

**Description**: Start a core OPNsense service. Has no effect if the service is
already running.

**OPNsense endpoint**: `POST /api/{module}/service/start`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "module": {
      "type": "string",
      "enum": ["unbound", "dhcpv4", "firmware", "ids", "cron"]
    }
  },
  "required": ["module"]
}
```

**Output**: JSON object matching `ServiceActionResult` from the data model.
Example: `{"response": "OK"}`.

---

## Tool: `service_stop`

**Description**: Stop a core OPNsense service. Has no effect if the service is
already stopped.

**OPNsense endpoint**: `POST /api/{module}/service/stop`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "module": {
      "type": "string",
      "enum": ["unbound", "dhcpv4", "firmware", "ids", "cron"]
    }
  },
  "required": ["module"]
}
```

**Output**: JSON object matching `ServiceActionResult`.

---

## Tool: `service_restart`

**Description**: Restart a core OPNsense service. Stops then starts the service,
applying any pending configuration changes.

**OPNsense endpoint**: `POST /api/{module}/service/restart`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "module": {
      "type": "string",
      "enum": ["unbound", "dhcpv4", "firmware", "ids", "cron"]
    }
  },
  "required": ["module"]
}
```

**Output**: JSON object matching `ServiceActionResult`.
