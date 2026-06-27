# MCP Tool Contracts: Firewall Domain

Tools in this domain cover firewall filter rules, aliases, and NAT rules.
OPNsense uses a two-phase model: mutations stage changes; `apply` commits them.

---

## Firewall Rules

### Tool: `firewall_rule_list`

**Description**: List all firewall filter rules.

**OPNsense endpoint**: `POST /api/firewall/filter/search_rule`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "current":      {"type": "integer", "description": "Page number (1-based)", "default": 1},
    "rowCount":     {"type": "integer", "description": "Rows per page; -1 = all", "default": -1},
    "searchPhrase": {"type": "string",  "description": "Filter by description or address", "default": ""}
  },
  "required": []
}
```

**Output**: `{"rows": [...], "rowCount": N, "total": N, "current": 1}` where each row
matches `FirewallRuleRow` from the data model.

---

### Tool: `firewall_rule_get`

**Description**: Retrieve full details of a single firewall rule by UUID.

**OPNsense endpoint**: `GET /api/firewall/filter/get_rule/{uuid}`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "uuid": {"type": "string", "description": "Firewall rule UUID"}
  },
  "required": ["uuid"]
}
```

**Output**: `{"rule": {...}}` matching `FirewallRuleDetail` from the data model.

**Error cases**: 404 (UUID not found).

---

### Tool: `firewall_rule_add`

**Description**: Add a new firewall filter rule. Changes are staged until
`firewall_rule_apply` is called.

**OPNsense endpoint**: `POST /api/firewall/filter/add_rule`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "rule": {
      "type": "object",
      "description": "Rule object matching OPNsense firewall filter rule schema",
      "properties": {
        "enabled":          {"type": "string", "enum": ["0", "1"]},
        "action":           {"type": "string", "enum": ["pass", "block", "reject"]},
        "description":      {"type": "string"},
        "interface":        {"type": "string"},
        "direction":        {"type": "string", "enum": ["in", "out"]},
        "ipprotocol":       {"type": "string", "enum": ["inet", "inet6"]},
        "protocol":         {"type": "string"},
        "source_net":       {"type": "string"},
        "destination_net":  {"type": "string"},
        "destination_port": {"type": "string"}
      },
      "required": ["enabled", "action", "interface", "direction"]
    }
  },
  "required": ["rule"]
}
```

**Output**: `{"result": "saved", "uuid": "<new-uuid>"}` on success.

**Error cases**: 400 (validation failure with field-level detail from OPNsense).

---

### Tool: `firewall_rule_update`

**Description**: Update an existing firewall filter rule by UUID. Changes are staged
until `firewall_rule_apply` is called.

**OPNsense endpoint**: `POST /api/firewall/filter/set_rule/{uuid}`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "uuid": {"type": "string", "description": "Firewall rule UUID"},
    "rule": {"type": "object", "description": "Partial or full rule object; fields present override existing values"}
  },
  "required": ["uuid", "rule"]
}
```

**Output**: `{"result": "saved"}` on success.

**Error cases**: 404 (UUID not found), 400 (validation failure).

---

### Tool: `firewall_rule_delete`

**Description**: Delete a firewall filter rule by UUID. Changes are staged until
`firewall_rule_apply` is called.

**OPNsense endpoint**: `POST /api/firewall/filter/del_rule/{uuid}`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "uuid": {"type": "string", "description": "Firewall rule UUID"}
  },
  "required": ["uuid"]
}
```

**Output**: `{"result": "deleted"}` on success.

**Error cases**: 404 (UUID not found).

---

### Tool: `firewall_rule_apply`

**Description**: Apply all staged firewall filter rule changes to the running
configuration. Must be called after add/update/delete operations to take effect.

**OPNsense endpoint**: `POST /api/firewall/filter/apply`

**Input schema**:
```json
{"type": "object", "properties": {}, "required": []}
```

**Output**: `{"status": "ok"}` on success.

---

## Firewall Aliases

### Tool: `firewall_alias_list`

**Description**: List all firewall aliases.

**OPNsense endpoint**: `GET /api/firewall/alias/get`

**Input schema**:
```json
{"type": "object", "properties": {}, "required": []}
```

**Output**: `{"aliases": {"alias": {<uuid>: <AliasRow>, ...}}}` as returned by OPNsense.

---

### Tool: `firewall_alias_get_uuid`

**Description**: Look up the UUID of a firewall alias by name.

**OPNsense endpoint**: `GET /api/firewall/alias/getAliasUUID/{name}`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string", "description": "Alias name"}
  },
  "required": ["name"]
}
```

**Output**: `{"uuid": "<alias-uuid>"}` on success, `{"uuid": ""}` if not found.

---

### Tool: `firewall_alias_add`

**Description**: Add a new firewall alias. Changes are staged until
`firewall_alias_apply` is called.

**OPNsense endpoint**: `POST /api/firewall/alias/add_item`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "alias": {
      "type": "object",
      "properties": {
        "name":        {"type": "string"},
        "type":        {"type": "string", "enum": ["host", "network", "port", "url", "geoip", "networkgroup", "mac"]},
        "description": {"type": "string"},
        "content":     {"type": "string", "description": "Newline-separated entries"},
        "enabled":     {"type": "string", "enum": ["0", "1"]}
      },
      "required": ["name", "type", "content"]
    }
  },
  "required": ["alias"]
}
```

**Output**: `{"result": "saved", "uuid": "<new-uuid>"}` on success.

---

### Tool: `firewall_alias_update`

**Description**: Update an existing firewall alias by UUID.

**OPNsense endpoint**: `POST /api/firewall/alias/set_item/{uuid}`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "uuid":  {"type": "string"},
    "alias": {"type": "object", "description": "Partial alias object"}
  },
  "required": ["uuid", "alias"]
}
```

**Output**: `{"result": "saved"}` on success.

---

### Tool: `firewall_alias_delete`

**Description**: Delete a firewall alias by UUID.

**OPNsense endpoint**: `POST /api/firewall/alias/del_item/{uuid}`

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

---

### Tool: `firewall_alias_apply`

**Description**: Apply all staged alias changes to the running configuration.

**OPNsense endpoint**: `POST /api/firewall/alias/reconfigure`

**Input schema**:
```json
{"type": "object", "properties": {}, "required": []}
```

**Output**: `{"status": "ok"}` on success.

---

## NAT Rules

### Tool: `firewall_nat_list`

**Description**: List all NAT (port-forward) rules.

**OPNsense endpoint**: `POST /api/firewall/nat/searchrule`

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

**Output**: `{"rows": [...], "rowCount": N, "total": N, "current": 1}`.

---

### Tool: `firewall_nat_add`

**Description**: Add a NAT rule. Staged until `firewall_nat_apply`.

**OPNsense endpoint**: `POST /api/firewall/nat/addrule`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "rule": {"type": "object", "description": "NAT rule object per OPNsense firewall NAT schema"}
  },
  "required": ["rule"]
}
```

**Output**: `{"result": "saved", "uuid": "<new-uuid>"}`.

---

### Tool: `firewall_nat_update`

**Description**: Update a NAT rule by UUID.

**OPNsense endpoint**: `POST /api/firewall/nat/setrule/{uuid}`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "uuid": {"type": "string"},
    "rule": {"type": "object"}
  },
  "required": ["uuid", "rule"]
}
```

**Output**: `{"result": "saved"}`.

---

### Tool: `firewall_nat_delete`

**Description**: Delete a NAT rule by UUID.

**OPNsense endpoint**: `POST /api/firewall/nat/delrule/{uuid}`

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

**Output**: `{"result": "deleted"}`.

---

### Tool: `firewall_nat_apply`

**Description**: Apply all staged NAT rule changes.

**OPNsense endpoint**: `POST /api/firewall/nat/apply`

**Input schema**:
```json
{"type": "object", "properties": {}, "required": []}
```

**Output**: `{"status": "ok"}`.
