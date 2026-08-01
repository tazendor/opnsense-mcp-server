# MCP Tool Contracts: IPsec Domain (strongSwan)

Core module `ipsec` (research.md §3 — not a separate plugin, correcting spec's grouping).
Connection ("phase 1"), local/remote auth rounds, and child ("phase 2") mutations are
staged; `ipsec_apply` reconfigures the service.

---

## Tool: `ipsec_connection_list` / `_get` / `_add` / `_update` / `_delete` / `_toggle`

CRUD over `/api/ipsec/connections/{search_connection|get_connection|add_connection|set_connection|toggle_connection|del_connection}[/{uuid}]`.

**`ipsec_connection_delete`**: gated by `confirmation.md` (VPN config teardown — FR-007).
The rest are standard, staged writes.

**Key fields**: `enabled`, `proposals`, `version` (0=IKEv1+2, 1=IKEv1, 2=IKEv2),
`local_addrs`, `remote_addrs`, `pools`, `description`.

## Tool: `ipsec_local_list` / `_get` / `_add` / `_update` / `_delete` / `_toggle`
## Tool: `ipsec_remote_list` / `_get` / `_add` / `_update` / `_delete` / `_toggle`

Auth-round sub-objects of a connection. `/api/ipsec/connections/{search_local|...}` and
`{search_remote|...}` respectively. Standard risk, staged.

## Tool: `ipsec_child_list` / `_get` / `_add` / `_update` / `_delete` / `_toggle`

"Phase 2" equivalent. `/api/ipsec/connections/{search_child|get_child|add_child|set_child|toggle_child|del_child}[/{uuid}]`.
Key fields: `local_ts`, `remote_ts`. Standard risk, staged (FR-013).

## Tool: `ipsec_enabled_get` / `ipsec_enabled_toggle`

Global IPsec on/off. `GET /api/ipsec/connections/is_enabled`, `POST /api/ipsec/connections/toggle`.
Toggling off is a config-level teardown of every tunnel at once — **gated by
`confirmation.md`**.

---

## Tool: `ipsec_keypair_list` / `_get` / `_add` / `_update` / `_delete`

`/api/ipsec/key_pairs/{search_item|get_item|add_item|set_item|del_item}[/{uuid}]`.
**`privateKey` redacted on every read** (FR-017).

## Tool: `ipsec_keypair_generate`

**OPNsense endpoint**: `GET /api/ipsec/key_pairs/gen_key_pair/{type}/{size}` (`type`=rsa|ecdsa).
Not persisted by this call; not redacted (one-shot generation response, same pattern as
`openvpn_static_key_generate`).

## Tool: `ipsec_psk_list` / `_get` / `_add` / `_update` / `_delete`

`/api/ipsec/pre_shared_keys/{search_item|get_item|add_item|set_item|del_item}[/{uuid}]`.
Object key `preSharedKey`: `ident`, `remote_ident`, `keyType` (PSK/EAP), `Key`.
**`Key` redacted on every read** (FR-017 — a shared secret, treated the same as an
asymmetric private key for redaction purposes since its disclosure is equally sensitive).

## Tool: `ipsec_pool_list` / `_get` / `_add` / `_update` / `_delete` / `_toggle`

Remote-access virtual-IP pools. `/api/ipsec/pools/{search|get|add|set|toggle|del}[/{uuid}]`.
Standard risk, staged.

---

## Tool: `ipsec_session_list`

**Description**: List live phase 1 and phase 2 security associations.

**OPNsense endpoint**: `GET /api/ipsec/sessions/search_phase1`, `GET /api/ipsec/sessions/search_phase2`
(exposed as two tools, `ipsec_phase1_session_list` / `ipsec_phase2_session_list`, mirroring
the two distinct OPNsense endpoints rather than merging them).

## Tool: `ipsec_session_connect` / `ipsec_session_disconnect`

**Description**: Manually bring a tunnel up or down (live state, not config). Standard
risk — analogous to a VPN service restart, not a config teardown.

**OPNsense endpoint**: `POST /api/ipsec/sessions/connect`, `POST /api/ipsec/sessions/disconnect`.

---

## Tool: `ipsec_service_start` / `_stop` / `_restart`

Standard risk (service-level). `POST /api/ipsec/service/{start|stop|restart}`.

## Tool: `ipsec_apply`

**OPNsense endpoint**: `POST /api/ipsec/service/reconfigure`.
