# MCP Tool Contracts: IDS/IPS Domain (Suricata)

This contract covers both the pre-existing `ids_ruleset_list` tool (shipped without a
contract document — FR-002, US1 AC5) and the new ruleset/rule toggle write tools (FR-005).
Toggling takes effect immediately in the config store; `ids_apply` (via the existing
`service_restart` tool with `module="ids"`, see `services.md`) reloads Suricata to apply it.

---

## Tool: `ids_ruleset_list`

**Description**: List all available IDS/IPS rulesets and their enabled/disabled status.

**OPNsense endpoint**: `GET /api/ids/settings/listRulesets`

**Input schema**: `{"type": "object", "properties": {}, "required": []}`

**Output**: JSON object of ruleset filename → metadata including `enabled` status, as
OPNsense returns it.

**Error cases**: 401 (invalid credentials).

---

## Tool: `ids_ruleset_toggle`

**Description**: Enable or disable one or more IDS/IPS rulesets by filename. Takes effect
after the IDS service is restarted (`service_restart` with `module="ids"`, or
`ids_apply`).

**OPNsense endpoint**: `POST /api/ids/settings/toggle_ruleset`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "filenames": {"type": "string", "description": "Comma-separated ruleset filename(s)"},
    "enabled": {"type": "integer", "enum": [0, 1],
      "description": "Omit to toggle current state; 0/1 to force disabled/enabled"}
  },
  "required": ["filenames"]
}
```

**Output**: `{"result": "ok"}` on success.

**Error cases**: 400 (unknown filename).

**Notes**: standard risk, staged in the sense that it doesn't take effect on the running
Suricata process until reload — matches the existing DNS/Firewall/Routes stage-then-apply
convention even though OPNsense's IDS API doesn't itself distinguish a separate "staged"
state internally.

---

## Tool: `ids_rule_toggle`

**Description**: Enable or disable one or more individual IDS/IPS rules by SID (finer
grain than a whole ruleset — FR-005's "if individually addressable in the current stable
API": confirmed yes).

**OPNsense endpoint**: `POST /api/ids/settings/toggle_rule`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "sids": {"type": "string", "description": "Comma-separated rule SID(s)"},
    "enabled": {"type": "integer", "enum": [0, 1]}
  },
  "required": ["sids"]
}
```

**Output**: `{"result": "ok"}` on success.

## Tool: `ids_apply`

**Description**: Reconfigure and restart Suricata to apply staged ruleset/rule toggles.
Equivalent to `service_restart(module="ids")` — provided as a same-named counterpart to
`dns_apply`/`route_apply` etc. for consistency, since the spec's stage-then-apply
convention (US1) expects every write-capable domain to have its own `_apply` tool rather
than requiring the caller to know the generic `service_restart` module name.

**OPNsense endpoint**: `POST /api/ids/service/reconfigure`
