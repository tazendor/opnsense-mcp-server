# MCP Tool Contracts: DNS Resolver Domain (Unbound)

Tools in this domain manage the OPNsense DNS Resolver (Unbound). Host override
mutations are staged until `dns_apply` is called.

---

## Tool: `dns_settings_get`

**Description**: Retrieve the full Unbound DNS Resolver configuration.

**OPNsense endpoint**: `GET /api/unbound/settings/get`

**Input schema**:
```json
{"type": "object", "properties": {}, "required": []}
```

**Output**: Full Unbound settings object as returned by OPNsense, containing
the `unbound` key with nested general and forwarding settings.

---

## Tool: `dns_host_override_list`

**Description**: List all DNS host overrides configured in the Unbound resolver.

**OPNsense endpoint**: `GET /api/unbound/settings/searchHostOverride`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "current":      {"type": "integer", "default": 1},
    "rowCount":     {"type": "integer", "default": -1},
    "searchPhrase": {"type": "string",  "default": ""}
  },
  "required": []
}
```

**Output**: `{"rows": [...], "rowCount": N, "total": N}` where each row matches
`HostOverrideRow` from the data model.

---

## Tool: `dns_host_override_add`

**Description**: Add a DNS host override. Staged until `dns_apply` is called.

**OPNsense endpoint**: `POST /api/unbound/settings/addHostOverride`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "host": {
      "type": "object",
      "properties": {
        "enabled":     {"type": "string", "enum": ["0", "1"], "default": "1"},
        "host":        {"type": "string", "description": "Hostname (without domain)"},
        "domain":      {"type": "string", "description": "Domain name"},
        "rr":          {"type": "string", "enum": ["A", "AAAA", "MX"],
                        "description": "Record type"},
        "server":      {"type": "string", "description": "IP address (for A/AAAA records)"},
        "mxprio":      {"type": "string", "description": "MX priority (for MX records)"},
        "mx":          {"type": "string", "description": "MX target hostname (for MX records)"},
        "description": {"type": "string"}
      },
      "required": ["host", "domain", "rr"]
    }
  },
  "required": ["host"]
}
```

**Output**: `{"result": "saved", "uuid": "<new-uuid>"}` on success.

**Error cases**: 400 (missing required fields, invalid IP address format).

---

## Tool: `dns_host_override_update`

**Description**: Update an existing DNS host override by UUID.

**OPNsense endpoint**: `POST /api/unbound/settings/setHostOverride/{uuid}`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "uuid": {"type": "string"},
    "host": {"type": "object", "description": "Partial host override object"}
  },
  "required": ["uuid", "host"]
}
```

**Output**: `{"result": "saved"}` on success.

**Error cases**: 404 (UUID not found), 400 (validation failure).

---

## Tool: `dns_host_override_delete`

**Description**: Delete a DNS host override by UUID.

**OPNsense endpoint**: `POST /api/unbound/settings/delHostOverride/{uuid}`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "uuid": {"type": "string"}
  },
  "required": ["uuid"]
}
```

**Output**: `{"result": "deleted"}` on success.

**Error cases**: 404 (UUID not found).

---

## Tool: `dns_apply`

**Description**: Reconfigure and restart the Unbound DNS Resolver to apply all staged
changes (host override additions, updates, and deletions).

**OPNsense endpoint**: `POST /api/unbound/service/reconfigure`

**Input schema**:
```json
{"type": "object", "properties": {}, "required": []}
```

**Output**: `{"status": "ok"}` on success.

**Notes**: This operation causes a brief DNS outage while Unbound reloads. Applies all
pending Unbound configuration changes, not just host overrides.
