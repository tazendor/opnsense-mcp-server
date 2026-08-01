# MCP Tool Contracts: WireGuard Domain

Core module `wireguard` (research.md §4 — merged into OPNsense core in 2023; not a
separate plugin, correcting spec's grouping). Server and client (peer) mutations are
staged; `wireguard_apply` reconfigures the service.

---

## Tool: `wireguard_server_list` / `_get` / `_add` / `_update` / `_delete` / `_toggle`

`/api/wireguard/server/{search_server|get_server|add_server|set_server|toggle_server|del_server}[/{uuid}]`,
object key `server`: `name`, `instance`, `pubkey`, `privkey`, `port`, `mtu`, `dns`,
`tunneladdress`, `peers`, `gateway`.

**`privkey` redacted on every read** (`_list`/`_get`) per FR-017.

**`wireguard_server_delete`**: gated by `confirmation.md` (VPN config teardown, FR-007).
The rest are standard, staged writes.

## Tool: `wireguard_server_keypair_generate`

**OPNsense endpoint**: `GET /api/wireguard/server/key_pair`

**Output**: `{"public_key": ..., "private_key": ...}` — not redacted (one-shot generation
response the caller explicitly requested; not persisted by this call). Same pattern as
`openvpn_static_key_generate`.

---

## Tool: `wireguard_client_list` / `_get` / `_add` / `_update` / `_delete` / `_toggle`

`/api/wireguard/client/{search_client|get_client|add_client|set_client|toggle_client|del_client}[/{uuid}]`,
object key `client` (peer object): `name`, `pubkey`, `psk`, `tunneladdress`, `endpoint`,
`serveraddress`, `serverport`, `keepalive`.

**No private-key field exists on this object** — see `research.md` §4. FR-017's
redaction requirement is a **documented no-op** here: the tool's docstring notes this
explicitly so it isn't mistaken for a missed case. `psk` (pre-shared key, symmetric,
optional) **is** redacted on read as a sensitive secondary secret, following the same
principle applied to IPsec PSKs.

**`wireguard_client_delete`**: standard risk — removing one peer is not equivalent to
tearing down the tunnel/instance itself (unlike `_server_delete`).

## Tool: `wireguard_client_psk_generate`

**OPNsense endpoint**: `GET/POST /api/wireguard/client/psk` — generates a PSK value,
not persisted, not redacted (one-shot, explicitly requested).

## Tool: `wireguard_client_builder_get` / `_add`

**Description**: Helper that allocates a free tunnel IP and pre-fills a peer config
(used by the OPNsense UI's "add client" wizard). Exposed as-is for parity; standard risk.

**OPNsense endpoint**: `GET /api/wireguard/client/get_client_builder`, `POST /api/wireguard/client/add_client_builder`.

## Tool: `wireguard_server_list_for_client`

**OPNsense endpoint**: `GET /api/wireguard/client/list_servers`, `GET /api/wireguard/client/get_server_info`
— lookup helpers used when constructing a peer against a specific server.

---

## Tool: `wireguard_general_get` / `_update`

Whole-model general settings. `GET /api/wireguard/general/get`, `POST /api/wireguard/general/set`.
Standard risk, staged.

## Tool: `wireguard_service_start` / `_stop` / `_restart`

Standard risk. `POST /api/wireguard/service/{start|stop|restart}`.

## Tool: `wireguard_status`

**Description**: Live `wg show`-equivalent dump: which peers are online, last handshake,
transfer bytes. Distinct from `service_status` (running/stopped) — this is per-peer
connectivity detail.

**OPNsense endpoint**: `GET /api/wireguard/service/show`

## Tool: `wireguard_apply`

**OPNsense endpoint**: `POST /api/wireguard/service/reconfigure`.
