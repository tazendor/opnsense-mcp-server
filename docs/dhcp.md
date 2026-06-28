# MCP Tool Contracts: DHCP Domain

Tools in this domain expose OPNsense DHCPv4 lease information and service control.
DHCPv6 is out of scope for v1.

---

## Tool: `dhcp_lease_list`

**Description**: List current DHCPv4 leases — both dynamic (assigned automatically)
and static (MAC-bound).

**OPNsense endpoint**: `POST /api/dhcpv4/leases/searchLease`

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "current":      {"type": "integer", "default": 1},
    "rowCount":     {"type": "integer", "default": -1},
    "searchPhrase": {"type": "string",  "default": ""},
    "inactive":     {"type": "integer", "enum": [0, 1], "default": 0,
                     "description": "1 to include expired/released leases"}
  },
  "required": []
}
```

**Output**: `{"rows": [...], "rowCount": N, "total": N, "current": 1}` where each row
matches `DHCPLease` from the data model.

---

## Tool: `dhcp_settings_get`

**Description**: Retrieve the DHCPv4 service configuration (subnet definitions,
range settings, DNS options, and static mappings).

**OPNsense endpoint**: `GET /api/dhcpv4/settings/get`

**Input schema**:
```json
{"type": "object", "properties": {}, "required": []}
```

**Output**: Full DHCP settings object as returned by OPNsense, containing
interface-keyed subnet configurations.

---

## Tool: `dhcp_static_list`

**Description**: List all static DHCP lease mappings (MAC address to fixed IP).

**OPNsense endpoint**: `GET /api/dhcpv4/settings/searchStaticMap`

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

**Output**: `{"rows": [...], "rowCount": N, "total": N}` where each row contains
`mac`, `ipaddr`, `hostname`, `descr`.
