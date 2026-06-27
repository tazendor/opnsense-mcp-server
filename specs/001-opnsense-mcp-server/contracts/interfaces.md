# MCP Tool Contracts: Interfaces Domain

Tools in this domain expose OPNsense network interface information.
These are read-only diagnostic tools — interface assignment changes are out of scope for v1.

---

## Tool: `interface_list`

**Description**: List the names and identifiers of all network interfaces configured
on OPNsense (e.g., WAN, LAN, OPT1).

**OPNsense endpoint**: `GET /api/diagnostics/interface/getInterfaceNames`

**Input schema**:
```json
{"type": "object", "properties": {}, "required": []}
```

**Output**: A JSON object mapping internal interface identifiers to their friendly names.
Example: `{"em0": "WAN", "em1": "LAN", "em2": "OPT1"}`.

---

## Tool: `interface_config`

**Description**: Retrieve the full configuration and status of all network interfaces,
including MAC address, IP address, subnet mask, link state, and MTU.

**OPNsense endpoint**: `GET /api/diagnostics/interface/getInterfaceConfig`

**Input schema**:
```json
{"type": "object", "properties": {}, "required": []}
```

**Output**: A JSON object where each key is an interface name and the value is an
interface config object matching `InterfaceConfig` from the data model.

---

## Tool: `interface_arp_table`

**Description**: Retrieve the current ARP table — the mapping of IP addresses to
MAC addresses for devices on locally connected networks.

**OPNsense endpoint**: `GET /api/diagnostics/interface/getArp`

**Input schema**:
```json
{"type": "object", "properties": {}, "required": []}
```

**Output**: Array of ARP entries, each containing `ip`, `mac`, `intf` (interface),
and `expired` fields as returned by OPNsense.

---

## Tool: `interface_ndp_table`

**Description**: Retrieve the current NDP (Neighbor Discovery Protocol) table —
the IPv6 equivalent of the ARP table.

**OPNsense endpoint**: `GET /api/diagnostics/interface/getNdp`

**Input schema**:
```json
{"type": "object", "properties": {}, "required": []}
```

**Output**: Array of NDP entries, each containing `ipv6`, `mac`, and `intf` fields
as returned by OPNsense.
