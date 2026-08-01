# MCP Tool Contracts: System Domain

**Superseded by 002-complete-api-coverage**: the `system_status` and
`system_firmware_status` endpoints below have drifted from the shipped implementation
(actual code calls `core/system/status` and `core/firmware/status`, not the paths below),
and 002 adds high-risk system operations (reboot, halt, firmware upgrade, config restore,
interface reassignment) — see `specs/002-complete-api-coverage/contracts/system.md` for
the corrected, current contract.

Tools in this domain expose OPNsense system status, firmware, and configuration backup.

---

## Tool: `system_status`

**Description**: Retrieve current system status including firmware version, CPU usage,
memory usage, and uptime.

**OPNsense endpoint**: `GET /api/core/dashboard/get`

**Input schema**:
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```
No parameters.

**Output**: JSON object matching `SystemStatus` from the data model. Contains
`versions`, `cpu`, `memory`, and `uptime` keys as returned by OPNsense.

**Error cases**: 401 (invalid credentials), 503 (OPNsense temporarily unavailable).

---

## Tool: `system_firmware_status`

**Description**: Check the current firmware version and whether updates are available.

**OPNsense endpoint**: `GET /api/firmware/status/check`

**Input schema**:
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```
No parameters.

**Output**: JSON object matching `FirmwareStatus` from the data model. Contains
`status`, `product_version`, `product_latest`, and `updates` keys.

**Error cases**: 401 (invalid credentials), 503.

---

## Tool: `system_config_backup`

**Description**: Download the current OPNsense configuration as an XML document.
Use this to take a snapshot before making changes.

**OPNsense endpoint**: `GET /api/core/backup/download/this`

**Input schema**:
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```
No parameters.

**Output**: XML text string containing the full OPNsense configuration. Returned as
a string (not JSON) since the OPNsense endpoint returns `application/xml`.

**Error cases**: 401 (invalid credentials), 403 (API user lacks backup privilege).
