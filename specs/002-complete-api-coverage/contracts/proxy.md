# MCP Tool Contracts: Web Proxy Domain (Squid)

Module `proxy`, plugin `os-squid`. **Scope note** (research.md §5): base `os-squid` has no
per-rule ACL array to CRUD — the actual access controls are flat CSV-list fields inside
general settings. The `Acl` policy-engine controller requires a second plugin
(`os-OPNProxy` + `os-redis`) and is out of scope for this spec (revisit later if there's
demand). Settings mutations are staged; `proxy_apply` reconfigures the service.

---

## Tool: `proxy_settings_get`

**Description**: Retrieve the full Squid proxy configuration — general, cache, traffic
shaping, parent proxy, forwarding/ACL (`allowedSubnets`, `unrestricted`, `bannedHosts`,
`whiteList`, `blackList`, `safePorts`, `sslPorts`), ICAP, and auth settings.

**OPNsense endpoint**: `GET /api/proxy/settings/get`

**Output**: Full settings object as OPNsense returns it.

## Tool: `proxy_settings_update`

**Description**: Update Squid proxy configuration, including access control lists
(FR-014). Staged until `proxy_apply` is called.

**OPNsense endpoint**: `POST /api/proxy/settings/set`

**Input schema**: `{"type": "object", "properties": {"proxy": {"type": "object"}}, "required": ["proxy"]}`

**Output**: `{"result": "saved"}`.

---

## Tool: `proxy_remote_blacklist_list` / `_get` / `_add` / `_update` / `_delete` / `_toggle`

Downloadable blacklist feed definitions. `/api/proxy/settings/{search_remote_blacklist|get_remote_blacklist|add_remote_blacklist|set_remote_blacklist|toggle_remote_blacklist|del_remote_blacklist}[/{uuid}]`.

**`password` (feed-fetch credential) redacted on every read** — not asymmetric key
material, but sensitive; redacted per the spirit of FR-017 (research.md §5).

## Tool: `proxy_pac_rule_list` / `_get` / `_add` / `_update` / `_delete`
## Tool: `proxy_pac_proxy_list` / `_get` / `_add` / `_update` / `_delete`
## Tool: `proxy_pac_match_list` / `_get` / `_add` / `_update` / `_delete`

PAC (proxy auto-config) generation rules — three related sub-objects, each with the
standard search/get/add/set/del shape over
`/api/proxy/settings/{search_pac_rule|...}`, `{...pac_proxy...}`, `{...pac_match...}`.
Standard risk, staged.

---

## Tool: `proxy_service_start` / `_stop` / `_restart`

Standard risk. `POST /api/proxy/service/{start|stop|restart}`.

## Tool: `proxy_service_reset`

**Description**: Clear the Squid cache.

**OPNsense endpoint**: `POST /api/proxy/service/reset`

## Tool: `proxy_apply`

**Description**: Reconfigure Squid to apply all staged settings/ACL/blacklist/PAC
changes.

**OPNsense endpoint**: `POST /api/proxy/service/reconfigure`

**Notes**: brief proxy service interruption while it reloads, same caveat as `dns_apply`.
