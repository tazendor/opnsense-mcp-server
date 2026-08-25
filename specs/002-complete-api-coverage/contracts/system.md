# MCP Tool Contracts: System Domain (supersedes 001's contract)

Adds high-risk system operations (FR-018), all gated by `confirmation.md`. Also corrects
001's `system_status`/`system_firmware_status` endpoint drift.

---

## Tool: `system_status` *(existing; corrected endpoint)*

**OPNsense endpoint**: `GET /api/core/system/status`

*(001's contract doc said `GET /api/core/dashboard/get` — inaccurate; shipped code
already calls the correct path, only the doc was stale.)*

## Tool: `system_firmware_status` *(existing; corrected endpoint)*

**OPNsense endpoint**: `GET /api/core/firmware/status`

*(001's contract doc said `GET /api/firmware/status/check` — inaccurate, same as above.)*

## Tool: `system_config_backup` *(existing, unchanged)*

**OPNsense endpoint**: `GET /api/core/backup/download/this`

---

## Tool: `system_reboot`

**Description**: Reboot the firewall. High-risk — gated by `confirmation.md` (FR-018,
US6 AC1). Uses the plain system reboot, not the firmware-flow variant (research.md §8 —
`core/firmware/reboot` is a distinct action used only after a firmware operation and is
not used here).

**OPNsense endpoint**: `POST /api/core/system/reboot`

**Preview description**: `"Will reboot the firewall now. All active connections and VPN
tunnels will drop; the management session driving this tool call will also disconnect if
it depends on this firewall's own connectivity."`

**Output**: `{"status": "ok"}` — fire-and-forget, no progress polling.

## Tool: `system_halt`

**Description**: Power off the firewall. High-risk — gated by `confirmation.md` (FR-018,
US6 AC1). Requires physical or out-of-band access to power back on.

**OPNsense endpoint**: `POST /api/core/system/halt`

---

## Tool: `system_firmware_check`

**Description**: Poll for available updates. Standard risk (read-only trigger + poll,
no state change to the running system).

**OPNsense endpoint**: `POST /api/core/firmware/check` (kick off), `GET /api/core/firmware/status` (poll result — same tool as `system_firmware_status` above).

## Tool: `system_firmware_update`

**Description**: Trigger a minor/patch update within the current major series (e.g.
26.7→26.7.2). High-risk — gated by `confirmation.md` (FR-018, US6 AC3).

**OPNsense endpoint**: `POST /api/core/firmware/update`

**Preview description**: built from the pending-version info already available via
`system_firmware_status` (FR-009 — describe effect in evaluable terms).

**Output**: `{"msg_uuid": "..."}` — async; poll via `system_firmware_upgrade_status`.

## Tool: `system_firmware_upgrade`

**Description**: Trigger a major version upgrade (e.g. 26.7→next major). High-risk —
distinct tool from `system_firmware_update` since it's a distinct, higher-blast-radius
OPNsense action (research.md §8).

**OPNsense endpoint**: `POST /api/core/firmware/upgrade`

## Tool: `system_firmware_upgrade_status`

**Description**: Poll progress of an in-flight update/upgrade.

**OPNsense endpoint**: `GET /api/core/firmware/upgradestatus`

## Tool: `system_firmware_log`

**OPNsense endpoint**: `POST /api/core/firmware/log`

---

## Tool: `system_config_restore`

**Description**: Restore a previous configuration revision. **Narrowed from the literal
spec text** — see `research.md` "Discovered Spec Conflicts": there is no OPNsense REST
endpoint that accepts an arbitrary uploaded `config.xml` and restores it (that flow only
exists as a legacy, non-API, session/CSRF-protected HTML form). This tool instead restores
an **existing backup revision** already known to OPNsense (the automatic per-save history
it keeps, or a remote OPNcentral-managed backup) — still high-risk, still gated by
`confirmation.md`, still satisfying the spirit of FR-018 ("full configuration restore is
dangerous, must be confirmed"), but scoped to what the API actually supports. **Requires
spec owner sign-off before implementation** (tracked as an open item, not silently
implemented).

**OPNsense endpoints**:
- `GET /api/core/backup/providers` — list backup sources (local history, remote hosts).
- `GET /api/core/backup/backups/{host}` — list available revisions for a source
  (`host` empty/omitted = local).
- `GET /api/core/backup/diff` — preview the diff between current config and a candidate
  revision (used to build the FR-009 preview description).
- `POST /api/core/backup/revert_backup` — perform the restore.

**Input schema**:
```json
{"type": "object", "properties": {
  "host": {"type": "string", "default": ""},
  "backup": {"type": "string", "description": "Backup filename/identifier from core/backup/backups"},
  "confirm": {"type": "string"}
}, "required": ["backup"]}
```

**Preview description**: built from `core/backup/diff` — summarizes what will change,
per FR-009.

## Tool: `system_config_backup_list`

**Description**: List available configuration backup revisions (supports choosing a
`backup` value for `system_config_restore`, and general auditing). Standard risk,
read-only.

**OPNsense endpoint**: `GET /api/core/backup/backups/{host}` (`host` empty for local).
