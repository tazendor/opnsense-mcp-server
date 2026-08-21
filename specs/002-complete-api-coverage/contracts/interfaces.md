# MCP Tool Contracts: Interfaces Domain (extends 001's contract)

001's four read-only diagnostic tools (`interface_list`, `interface_config`,
`interface_arp_table`, `interface_ndp_table`) are unchanged — see 001's contract for
those. This document adds interface **assignment** (physical device ↔ logical interface),
the one piece of FR-018/US6 AC4 that OPNsense's API actually supports.

**Scope correction from the literal spec text** — see `research.md` §8 "Discovered Spec
Conflicts": enabling/disabling an interface, or editing its IP/media/MTU configuration,
is **not exposed by any current OPNsense REST API** — verified against source
(`Interfaces\Api\AssignmentController`, merged 2026-06-07) and a still-open upstream issue
(`opnsense/core#10568`) tracking that gap. This is not a "not yet verified" uncertainty;
it's a deliberate upstream scope boundary. **Requires spec owner sign-off**: US6 AC4 as
literally written ("interface be reassigned or disabled") cannot be fully satisfied;
reassignment only is proposed as the achievable scope.

---

## Tool: `interface_assignment_list`

**Description**: List current physical-device-to-logical-interface assignments
(e.g. `igb2` → `opt3`).

**OPNsense endpoint**: `GET /api/interfaces/assignment/search_item`

**Output**: `{"rows": [...], "rowCount": N, "total": N}`, each row: `descr`, `identifier`,
`if` (physical device name), `lock`.

## Tool: `interface_assignment_get`

**OPNsense endpoint**: `GET /api/interfaces/assignment/get_item/{ifname}`

---

## Tool: `interface_assignment_add`

**Description**: Assign a physical device to a new logical interface. Staged until
`interface_apply` is called.

**OPNsense endpoint**: `POST /api/interfaces/assignment/add_item`

**Input schema**: `{"type": "object", "properties": {"assignment": {"type": "object",
  "properties": {"descr": {"type": "string"}, "if": {"type": "string"}}, "required": ["if"]}},
 "required": ["assignment"]}`

## Tool: `interface_assignment_update`

**Description**: Reassign the physical device backing an existing logical interface
(e.g. re-point `opt3` from `igb2` to `igb5`). **High-risk — gated by `confirmation.md`**
(FR-018, US6 AC4): this can disconnect the interface carrying the MCP client's own
management traffic, and the server cannot know in advance which interface that is (spec
Edge Case).

**OPNsense endpoint**: `POST /api/interfaces/assignment/set_item/{ifname}`

**Preview description**: `"Will reassign logical interface <ifname> from physical device
<current_if> to <new_if>. If <ifname> carries this connection's own management traffic,
this session will be disconnected."`

## Tool: `interface_assignment_delete`

**Description**: Remove a logical interface assignment. High-risk — gated by
`confirmation.md` (same rationale as update; also the closest available equivalent to
"disable," since true enable/disable isn't exposed — see scope correction above).

**OPNsense endpoint**: `POST /api/interfaces/assignment/del_item/{ifnames}`

**Error cases**: OPNsense itself rejects deletion if the interface is part of a group,
bridge, GRE, or GIF tunnel, or is locked — surfaced as-is (FR-003 edge case: don't invent
a different explanation).

## Tool: `interface_apply`

**Description**: Apply staged interface assignment changes (relink or delete pending
operations) and reload the packet filter.

**OPNsense endpoint**: `POST /api/interfaces/assignment/reconfigure`

**Notes**: per OPNsense's own implementation, this is a two-step internal process
(interface relink, then filter reload) already handled server-side by this single
endpoint — the MCP tool doesn't need to orchestrate that itself.
