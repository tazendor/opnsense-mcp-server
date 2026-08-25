# MCP Tool Contracts: DHCP Domain (supersedes 001's contract)

Kea-backed DHCPv4. Corrects endpoint drift from 001's contract doc (which described
legacy `dhcpv4/*` ISC-dhcpd-style paths that don't match the shipped Kea-backed
implementation) and adds static-mapping and settings writes (FR-004). Static mapping
mutations are staged; `dhcp_apply` reconfigures Kea. DHCPv6 remains out of scope.

---

## Tool: `dhcp_lease_list` *(existing, unchanged)*

**OPNsense endpoint**: `POST /api/kea/leases4/search`

## Tool: `dhcp_settings_get` *(existing, unchanged)*

**OPNsense endpoint**: `GET /api/kea/dhcpv4/get`

## Tool: `dhcp_static_list` *(existing; corrected endpoint)*

**OPNsense endpoint**: `GET /api/kea/dhcpv4/search_reservation`

*(001's contract doc listed `GET /api/dhcpv4/settings/searchStaticMap` — inaccurate; the
shipped code already calls the Kea path correctly, only the doc was stale.)*

---

## Tool: `dhcp_static_add`

**Description**: Add a DHCPv4 static reservation (MAC → fixed IP). Staged until
`dhcp_apply` is called.

**OPNsense endpoint**: `POST /api/kea/dhcpv4/add_reservation`

**Input schema**:
```json
{"type": "object", "properties": {"reservation": {"type": "object",
  "properties": {
    "subnet":       {"type": "string", "description": "Subnet UUID this reservation belongs to"},
    "hw_address":   {"type": "string", "description": "MAC address"},
    "ip_address":   {"type": "string"},
    "hostname":     {"type": "string"},
    "description":  {"type": "string"}
  },
  "required": ["subnet", "hw_address", "ip_address"]}},
 "required": ["reservation"]}
```

**Output**: `{"result": "saved", "uuid": "<new-uuid>"}`.

## Tool: `dhcp_static_update`

**OPNsense endpoint**: `POST /api/kea/dhcpv4/set_reservation/{uuid}`

**Input schema**: `{"type": "object", "properties": {"uuid": {"type": "string"}, "reservation": {"type": "object"}}, "required": ["uuid", "reservation"]}`

## Tool: `dhcp_static_delete`

**OPNsense endpoint**: `POST /api/kea/dhcpv4/del_reservation/{uuid}`

**Input schema**: `{"type": "object", "properties": {"uuid": {"type": "string"}}, "required": ["uuid"]}`

---

## Tool: `dhcp_settings_update`

**Description**: Update DHCPv4 service settings (subnets, ranges, DNS options).
Staged until `dhcp_apply` is called.

**OPNsense endpoint**: `POST /api/kea/dhcpv4/set`

**Input schema**: `{"type": "object", "properties": {"settings": {"type": "object"}}, "required": ["settings"]}`

**Output**: `{"result": "saved"}`.

## Tool: `dhcp_apply`

**Description**: Reconfigure and restart the Kea DHCPv4 service to apply all staged
changes (reservations, subnets, settings). Equivalent to `service_restart(module="kea")`,
provided as a same-named counterpart for stage-then-apply consistency with the other
domains (see `ids.md` for the same rationale).

**OPNsense endpoint**: `POST /api/kea/service/reconfigure`

**Notes**: causes a brief DHCP service interruption while Kea reloads.
