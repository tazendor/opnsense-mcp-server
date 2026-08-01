# MCP Tool Contracts: Captive Portal Domain

Core module `captiveportal`. Zone settings mutations are staged; `captiveportal_apply`
reconfigures the service. Session management acts on live state (no staging).
`Access` (end-client logon page) and `Voucher` controllers are out of scope — this domain
covers administrator-facing portal management (FR-015), not the client-facing captive
portal experience itself.

---

## Tool: `captiveportal_zone_list` / `_get` / `_add` / `_update` / `_delete` / `_toggle`

`/api/captiveportal/settings/{search_zones|get_zone|add_zone|set_zone|toggle_zone|del_zone}[/{uuid}]`,
object key `zone`: `enabled`, `zoneid`, `interfaces`, `authservers`, `idletimeout`,
`hardtimeout`, `concurrentlogins`, `certificate`, `allowedAddresses`,
`allowedMACAddresses`, `template`, `description`.

Standard risk, staged — a zone's *configuration* isn't the same as forcibly disconnecting
its current users (that's the high-risk operation below).

---

## Tool: `captiveportal_session_list`

**Description**: List active captive portal sessions, optionally filtered to one zone.

**OPNsense endpoint**: `GET /api/captiveportal/session/list/{zoneid}` (omit `zoneid` for
all zones — the tool also exposes `GET /api/captiveportal/session/search` for the
filterable/paginated variant).

**Output**: Array of sessions: `sessionId`, `userName`, `ipAddress`, `macAddress`,
`startTime`.

## Tool: `captiveportal_zone_names`

**OPNsense endpoint**: `GET /api/captiveportal/session/zones` — lookup helper (zoneid →
description), useful for resolving which zone a session belongs to.

## Tool: `captiveportal_session_connect`

**Description**: Manually register a session (rare — normally sessions are created by a
client logging in through the portal itself). Standard risk.

**OPNsense endpoint**: `POST /api/captiveportal/session/connect`

## Tool: `captiveportal_session_disconnect`

**Description**: Disconnect a single captive portal session. Proceeds directly — no
confirmation required (FR-015, US4 AC3).

**OPNsense endpoint**: `POST /api/captiveportal/session/disconnect`

**Input schema**: `{"type": "object", "properties": {"session_id": {"type": "string"}, "zone_id": {"type": "string"}}, "required": ["session_id", "zone_id"]}`

---

## Tool: `captiveportal_session_disconnect_zone`

**Description**: Disconnect **every** active session in a zone. High-risk — gated by
`confirmation.md` (FR-015, US4 AC4). **No single OPNsense endpoint does this**
(research.md §6, verified against source and docs: `SessionController::disconnectAction`
only ever takes one `sessionId`). This tool's confirmed-execution step performs the fan-out
itself: enumerate the zone's sessions via `session/list/{zoneid}`, then call
`session/disconnect` once per `sessionId` found. The client-visible contract is still a
single high-risk operation with one preview and one confirmation, matching FR-008 — the
multi-call fan-out is an internal implementation detail, not something the MCP client
orchestrates.

**Input schema**: `{"type": "object", "properties": {"zone_id": {"type": "string"}, "confirm": {"type": "string"}}, "required": ["zone_id"]}`

**Preview description example**: `"Will disconnect N active session(s) in zone <zoneid>: <usernames/IPs>."` — the count and list are computed from a `session/list` call made *during the preview step* (read-only, doesn't count as contacting OPNsense with a mutating request — FR-008 only forbids the *mutating* request before confirmation).

**Output on confirmed execution**: `{"disconnected": ["<sessionId>", ...], "failed": [...]}`
— since this loops over N individual calls, partial failure is possible and must be
reported per-session rather than as a single pass/fail.

---

## Tool: `captiveportal_service_start` / `_stop` / `_restart`

Standard risk. `POST /api/captiveportal/service/{start|stop|restart}`.

## Tool: `captiveportal_apply`

**OPNsense endpoint**: `POST /api/captiveportal/service/reconfigure`.
