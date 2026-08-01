# MCP Tool Contracts: OpenVPN Domain

Wraps OPNsense's unified **Instances** model (server+client, distinguished by `role`) —
see `research.md` §2 for why the legacy servers/clients split is not used. Instance and
static-key mutations follow the stage-then-apply pattern; `openvpn_apply` reconfigures the
service. Instance-level start/stop/restart act immediately (spec Assumptions: service
control is standard risk). Tearing down (deleting) an instance's configuration goes through
`openvpn_instance_delete` → staged → `openvpn_apply`, which is a standard write, not a
high-risk one — only removing an *in-use, currently-connected* tunnel's config would be
disruptive, and the spec treats config-level teardown/disable generically as high-risk only
where explicitly listed (VPN config teardown is FR-007's own listed high-risk case) — see
Note under `openvpn_instance_delete` below.

---

## Tool: `openvpn_instance_list`

**Description**: List all configured OpenVPN instances (servers and clients).

**OPNsense endpoint**: `GET /api/openvpn/instances/search`

**Input schema**: `{"type": "object", "properties": {}, "required": []}`

**Output**: `{"rows": [...], "rowCount": N, "total": N}`, each row an `Instance` (see
`data-model.md`).

---

## Tool: `openvpn_instance_get`

**Description**: Retrieve one OpenVPN instance by UUID.

**OPNsense endpoint**: `GET /api/openvpn/instances/get/{uuid}`

**Input schema**: `{"type": "object", "properties": {"uuid": {"type": "string"}}, "required": ["uuid"]}`

**Output**: `{"instance": {...}}`.

---

## Tool: `openvpn_instance_add`

**Description**: Add a new OpenVPN instance (server or client role). Staged until
`openvpn_apply` is called.

**OPNsense endpoint**: `POST /api/openvpn/instances/add`

**Input schema**:
```json
{"type": "object", "properties": {"instance": {"type": "object",
  "description": "role, dev_type, proto, port, local, remote, topology, cert, ca, tls_key, authmode, etc."}},
 "required": ["instance"]}
```

**Output**: `{"result": "saved", "uuid": "<new-uuid>"}`.

---

## Tool: `openvpn_instance_update`

**OPNsense endpoint**: `POST /api/openvpn/instances/set/{uuid}`

**Input schema**: `{"type": "object", "properties": {"uuid": {"type": "string"}, "instance": {"type": "object"}}, "required": ["uuid", "instance"]}`

**Output**: `{"result": "saved"}`.

---

## Tool: `openvpn_instance_delete`

**OPNsense endpoint**: `POST /api/openvpn/instances/del/{uuid}`

**Input schema**: `{"type": "object", "properties": {"uuid": {"type": "string"}}, "required": ["uuid"]}`

**Output**: `{"result": "deleted"}`.

**Note**: standard risk (staged, not gated by `confirmation.md`) — matches spec Assumptions
("service-level start/stop/restart... standard risk; only configuration-level
teardown/disable... treated as high-risk" together with FR-007 listing "VPN configuration
teardown/disable" as high-risk). Read literally, FR-007 does put VPN config teardown in the
high-risk list — **this tool is therefore gated by `confirmation.md`**, not standard. Corrected
here from an earlier draft: `openvpn_instance_delete` (and the IPsec/WireGuard equivalents
below) take the `confirm` parameter from `confirmation.md`.

---

## Tool: `openvpn_static_key_list` / `_get` / `_add` / `_update` / `_delete`

Same CRUD shape as instances, over `/api/openvpn/instances/{search_static_key|get_static_key|add_static_key|set_static_key|del_static_key}[/{uuid}]`,
object key `statickey` (`mode`, `key`, `description`). **`key` is redacted on every read**
(`_list`/`_get`) per FR-017 — see `research.md` §2.

## Tool: `openvpn_static_key_generate`

**Description**: Generate a new static/TLS key server-side (does not persist it — caller
must then `_add` it if they want to keep it).

**OPNsense endpoint**: `GET /api/openvpn/instances/gen_key/{type}` (`type` = `secret` |
`auth-token` | `tls-auth` | `tls-crypt` | `tls-crypt-v2-server`)

**Output**: `{"key": "<generated material>"}` — **not redacted**: this is the one-shot
generation response the caller explicitly asked for, analogous to the Trust domain's
`private_key_location=local` case (see `trust.md`). The tool's docstring says so
explicitly.

---

## Tool: `openvpn_client_override_list` / `_get` / `_add` / `_update` / `_delete`

Per-client config overrides (CSO). CRUD over `/api/openvpn/client_overwrites/{search|get|add|set|del}[/{uuid}]`,
object key `cso`. Staged; standard risk (adding/removing a per-client override is not
teardown of the instance itself).

---

## Tool: `openvpn_session_list`

**Description**: List currently connected OpenVPN sessions (live status, not config).

**OPNsense endpoint**: `GET /api/openvpn/service/search_sessions`

**Output**: Array of session rows as OPNsense reports them (client CN, real/virtual IP,
bytes in/out, connected-since).

## Tool: `openvpn_route_list`

**OPNsense endpoint**: `GET /api/openvpn/service/search_routes`

## Tool: `openvpn_session_kill`

**Description**: Disconnect a single connected client session (not a config change —
the client can reconnect immediately if its config is still valid). Standard risk: this
is the VPN analogue of the Captive Portal single-session disconnect, which the spec
treats as proceeding directly (FR-015's session-vs-zone distinction extends by analogy).

**OPNsense endpoint**: `POST /api/openvpn/service/kill_session`

**Input schema**: `{"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}`

---

## Tool: `openvpn_service_start` / `_stop` / `_restart`

Standard risk (service-level, spec Assumptions). Take an instance id.

**OPNsense endpoint**: `POST /api/openvpn/service/{start_service|stop_service|restart_service}` with `id` in the body.

## Tool: `openvpn_apply`

**Description**: Reconfigure OpenVPN to apply all staged instance/static-key/override
changes.

**OPNsense endpoint**: `POST /api/openvpn/service/reconfigure`

**Notes**: causes a brief interruption to active OpenVPN sessions while the service
reloads, same caveat style as `dns_apply`.
