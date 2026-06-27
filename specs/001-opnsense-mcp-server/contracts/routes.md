# MCP Tool Contracts: Routes Domain

Tools in this domain manage OPNsense static routes.
Mutations are staged until `route_apply` is called.

---

## Tool: `route_list`

**Description**: List all configured static routes.

**OPNsense endpoint**: `POST /api/routes/routes/searchroute`

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

**Output**: `{"rows": [...], "rowCount": N, "total": N, "current": 1}` where each row
matches `RouteRow` from the data model.

---

## Tool: `route_add`

**Description**: Add a new static route. Staged until `route_apply` is called.

**OPNsense endpoint**: `POST /api/routes/routes/addroute`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "route": {
      "type": "object",
      "properties": {
        "network":  {"type": "string", "description": "Destination network in CIDR notation, e.g. '10.0.0.0/8'"},
        "gateway":  {"type": "string", "description": "Gateway name or IP"},
        "descr":    {"type": "string", "description": "Optional description"},
        "disabled": {"type": "string", "enum": ["0", "1"], "default": "0"}
      },
      "required": ["network", "gateway"]
    }
  },
  "required": ["route"]
}
```

**Output**: `{"result": "saved", "uuid": "<new-uuid>"}` on success.

**Error cases**: 400 (invalid network/gateway format).

---

## Tool: `route_update`

**Description**: Update an existing static route by UUID.

**OPNsense endpoint**: `POST /api/routes/routes/setroute/{uuid}`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "uuid":  {"type": "string"},
    "route": {"type": "object", "description": "Partial route object; provided fields override existing values"}
  },
  "required": ["uuid", "route"]
}
```

**Output**: `{"result": "saved"}` on success.

**Error cases**: 404 (UUID not found), 400 (validation failure).

---

## Tool: `route_delete`

**Description**: Delete a static route by UUID.

**OPNsense endpoint**: `POST /api/routes/routes/delroute/{uuid}`

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

## Tool: `route_apply`

**Description**: Apply all staged static route changes to the running routing table.
Must be called after add/update/delete operations to take effect.

**OPNsense endpoint**: `POST /api/routes/routes/reconfigure`

**Input schema**:
```json
{"type": "object", "properties": {}, "required": []}
```

**Output**: `{"status": "ok"}` on success.
