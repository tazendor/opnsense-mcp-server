# Research: Complete OPNsense API Coverage (Read-Write)

Research method: read `Api/*Controller.php` sources and model `.xml` definitions in
`github.com/opnsense/core` and `github.com/opnsense/plugins` (current stable at time of
writing: 26.7.1 "Xenial Xenops"), cross-checked against `docs.opnsense.org/development/api/`.
Two of the more surprising findings below (interface assignment API, captive portal
bulk-disconnect gap) were independently re-verified against live docs pages and the GitHub
API/source directly before being relied on here — see the "Verified" notes.

---

## 1. Confirmation / Safety Layer (User Story 2 — foundational)

**Decision**: An in-process, non-persistent `PendingOperationStore`: a dict keyed by an
opaque token (`secrets.token_urlsafe(32)`) → a `PendingOperation` dataclass holding the
tool name, its resolved arguments, a human-readable description of what will happen, and
an expiry timestamp (`time.monotonic() + ttl`). High-risk tools take an optional
`confirm: str | None` parameter:

- `confirm=None` (or omitted): validate inputs, describe the effect, register a
  `PendingOperation`, return `{"status": "confirmation_required", "confirm_token": ...,
  "description": ..., "expires_in_seconds": ...}`. No OPNsense request is made.
- `confirm=<token>`: look up the token. If missing/expired/mismatched to this specific
  tool+arguments, raise `ToolError` (client must re-request a preview). If valid, pop it
  (single-use), send the real request to OPNsense, return the result.

**Rationale**: Matches FR-007–FR-011 exactly with the simplest structure that satisfies
them (Constitution Principle I). No persistence needed (spec's own Assumptions section
rules it out — confirmations don't survive a restart). `time.monotonic()` avoids wall-clock
jumps affecting expiry. Using `secrets.token_urlsafe` rather than a predictable ID prevents
a client from guessing another session's pending-operation token.

**TTL**: 120 seconds default, configurable via `OPNSENSE_CONFIRM_TTL` env var (consistent
with existing `Config.from_env` pattern) — long enough for a human-in-the-loop AI assistant
to relay the preview and get a response, short enough to bound "stale preview" risk (Edge
Case in spec.md).

**Logging**: Both the preview and the confirmed-execution step go through the existing
`OPNsenseClient._log` path for the execution step; the preview step gets its own log record
(new `_log_preview`-style call, or a synthetic log entry with `outcome="preview"`) so SC-005
("distinguishable from each other") holds without adding a second logging subsystem.

**Alternatives considered**:
- Persistent (SQLite/file) store: rejected — spec explicitly scopes this out; adds a
  dependency and migration surface for no required benefit.
- A generic "risk" decorator that wraps arbitrary tool functions: rejected for the first
  cut — a plain explicit `confirm` parameter on each high-risk tool is more idiomatic and
  keeps each tool's schema self-documenting (a client introspecting the tool sees the
  `confirm` parameter directly, rather than needing to know about wrapper behavior).

---

## 2. OpenVPN

**Decision**: Wrap the **Instances** model (unified server+client object distinguished by a
`role` field), not the legacy servers/clients split. Current stable OPNsense's
`OpenVPN\Api\InstancesController` is the only supported way to create/edit OpenVPN
config via API; the old model is read-only backward-compat inside `ServiceController`.

**Endpoints** (module `openvpn`, core — no plugin required):

| Controller | Actions | Notes |
|---|---|---|
| `Instances` | `search`, `get`, `add`, `set`, `del`, `toggle` | object key `instance` |
| `Instances` | `search_static_key`, `get_static_key`, `add_static_key`, `set_static_key`, `del_static_key` | tls-auth/tls-crypt/tls-crypt-v2 keys, object key `statickey` |
| `Instances` | `gen_key` (`type=secret\|auth-token\|tls-auth\|tls-crypt\|tls-crypt-v2-server`) | GET, returns `{key: ...}` |
| `ClientOverwrites` | `search`, `get`, `add`, `set`, `del`, `toggle` | per-client config overrides, object key `cso` |
| `Service` | `search_sessions`, `search_routes`, `kill_session` | live status |
| `Service` | `start_service`, `stop_service`, `restart_service` (take `$id`), `reconfigure` | standard service actions, id-scoped |

**Key fields**: `Instance`: `vpnid`, `enabled`, `role`, `dev_type`, `proto`, `port`, `local`,
`remote`, `topology`, `cert`/`ca` (Trust refs, not raw material), `tls_key` (relation to
StaticKeys), `authmode`. `StaticKey`: `mode`, `key`, `description`.

**Redact on read** (FR-017): `StaticKeys.StaticKey.key` — returned in plaintext by
`get_static_key` and `gen_key`.

---

## 3. IPsec (strongSwan)

**Decision**: Core module `ipsec` (confirmed: no separate plugin package — it ships in
`opnsense/core`, unlike the spec's assumption text which groups it with "plugins").

**Endpoints**:

| Controller | Actions | Notes |
|---|---|---|
| `Connections` | `search_connection`, `get_connection`, `add_connection`, `set_connection`, `toggle_connection`, `del_connection` | "Phase 1" |
| `Connections` | `search_local`/`_remote`, `get_local`/`_remote`, `add_local`/`_remote`, `set_local`/`_remote`, `toggle_local`/`_remote`, `del_local`/`_remote` | auth rounds |
| `Connections` | `search_child`, `get_child`, `add_child`, `set_child`, `toggle_child`, `del_child` | "Phase 2" |
| `Connections` | `is_enabled` (GET), `toggle` (POST) | global IPsec on/off |
| `KeyPairs` | `search_item`, `get_item`, `add_item`, `set_item`, `del_item`, `gen_key_pair` (`type=rsa\|ecdsa`, `size`) | pubkey-auth keypairs |
| `PreSharedKeys` | `search_item`, `get_item`, `add_item`, `set_item`, `del_item` | PSK/EAP secrets |
| `Pools` | `search`, `get`, `add`, `set`, `del`, `toggle` | remote-access virtual-IP pools |
| `Sessions` | `search_phase1`, `search_phase2`, `connect`, `disconnect` | live status, session-scoped |
| `Service` | `start`, `stop`, `restart`, `reconfigure`, `status` | standard |

**Redact on read** (FR-017): `KeyPairs.keyPair.privateKey`; `PreSharedKeys.preSharedKey.Key`
(the shared secret itself — sensitive even though symmetric, not asymmetric).

---

## 4. WireGuard

**Decision**: Core module `wireguard` (confirmed: `os-wireguard` was merged into
`opnsense/core` in 2023 and no longer exists as a separate plugin package — spec's grouping
of WireGuard with "plugins" is inaccurate and will be corrected in the FR reference).

**Endpoints**:

| Controller | Actions | Notes |
|---|---|---|
| `Server` | `search_server`, `get_server`, `add_server`, `set_server`, `del_server`, `toggle_server` | one instance = one WG interface |
| `Server` | `key_pair` (GET) | server-side keypair generation |
| `Client` | `search_client`, `get_client`, `add_client`, `set_client`, `del_client`, `toggle_client` | peer object |
| `Client` | `psk` (GET/POST), `list_servers`, `get_server_info`, `get_client_builder`/`add_client_builder` | psk gen, IP-alloc helper |
| `General` | `get`, `set` | whole-model general settings |
| `Service` | `start`, `stop`, `restart`, `reconfigure`, `status`, `show` | `show` = live handshake/online status |

**Redact on read** (FR-017): `servers.server.privkey` **only**. The peer/client object
(`clients.client`) has no private-key field at all — WireGuard's design means the server
only ever stores a peer's public key (`pubkey`) plus an optional PSK; a peer's own private
key is generated client-side and never touches this API. This means FR-017's "VPN
peer/client entries" redaction requirement is a no-op for WireGuard clients specifically —
worth noting in the contract so it isn't mistaken for a missed case.

---

## 5. Web Proxy (Squid)

**Decision**: Module `proxy`, requires plugin `os-squid`. Implement `Settings`
(general/cache/forward/parentproxy/remote-blacklist/PAC-rule CRUD) and `Service`
only. **Do not** implement the `Acl` controller (policy-based ACL engine) — it requires a
*second* plugin, `os-OPNProxy`, which itself depends on `os-redis`. Wrapping it would mean
the proxy domain silently 404s on any installation with only base `os-squid`, which
conflicts with FR-003/edge-case handling ("plugin not installed → surface OPNsense's own
not-found error", not a partially-working tool). Scoped out for this spec; revisit as a
follow-up feature if user demand appears.

**Endpoints** (`os-squid` only):

| Controller | Actions | Notes |
|---|---|---|
| `Settings` | `get`, `set` | whole-model general/cache/traffic/parentproxy/forward/icap/auth settings |
| `Settings` | `search_remote_blacklist`, `get_remote_blacklist`, `add_remote_blacklist`, `set_remote_blacklist`, `del_remote_blacklist`, `toggle_remote_blacklist` | downloadable blacklist feeds |
| `Settings` | `search_pac_rule`/`_proxy`/`_match` + full CRUD each | PAC generation rules |
| `Service` | `start`, `stop`, `restart`, `reconfigure`, `status`, `reset`, `refresh_template` | standard + squid-specific |

**Important correction to spec's framing of "access control rules"**: base `os-squid` has
**no array-typed per-rule ACL object**. The actual allow/deny controls
(`allowedSubnets`, `unrestricted`, `bannedHosts`, `whiteList`, `blackList`, `safePorts`,
`sslPorts`) are flat CSV-list fields inside the single `forward.acl` sub-object of the
general settings (`proxy/settings/get`+`set`). FR-014 ("access control rules") is satisfied
by exposing these fields through `proxy_settings_get`/`proxy_settings_set`, not by a
separate CRUD tool — there is nothing to CRUD.

**Redact on read**: `remoteACLs.blacklists.blacklist.password` (plaintext feed-fetch
credential — not asymmetric key material, but sensitive; redact per the spirit of FR-017
even though it's not literally a private key).

---

## 6. Captive Portal

**Decision**: Core module `captiveportal`.

**Endpoints**:

| Controller | Actions | Notes |
|---|---|---|
| `Settings` | `search_zones`, `get_zone`, `add_zone`, `set_zone`, `del_zone`, `toggle_zone` | zone config |
| `Service` | `start`, `stop`, `restart`, `reconfigure`, `status` | + template management (not exposed — cosmetic, out of scope) |
| `Session` | `list` (`$zoneid`), `search`, `zones`, `connect`, `disconnect` | admin session management |

`Access` (the end-client-facing logon/logoff page) and `Voucher` are out of scope — they're
not "administrator manages the portal" operations described in the spec's user story.

**Verified (docs + source cross-check)**: bulk/zone-wide disconnect has **no dedicated
endpoint**. `disconnect` takes exactly one `sessionId`. To satisfy FR-015's "disconnecting
all sessions in a zone" as a single high-risk operation: the confirmed high-risk tool
(`captiveportal_session_disconnect_zone`) itself calls `session/list/{zoneid}` to enumerate
sessions, then calls `session/disconnect` once per session, inside the single confirmed tool
invocation. The client sees one high-risk operation; the server fans it out internally. This
keeps the confirm-then-execute contract (FR-008) at the "zone" granularity the spec
describes, rather than requiring the MCP client to orchestrate N individual disconnects
itself (which would defeat the purpose of gating the bulk action).

---

## 7. Trust / Certificates & CAs

**Decision**: Core module `trust`.

**Endpoints**:

| Controller | Actions | Notes |
|---|---|---|
| `Ca` | `search`, `get`, `add`, `set`, `del`, `ca_info`, `ca_list`, `raw_dump`, `generate_file` (`type=crt\|prv`) | |
| `Cert` | `search`, `get`, `add`, `set`, `del`, `ca_info`, `ca_list`, `raw_dump`, `generate_file` (`type=crt\|csr\|prv\|pkcs12`) | |
| `Crl` | `search`, `get(caref)`, `set(caref)`, `del(caref)`, `raw_dump`, `get_ocsp_info_data` | revocation lives here |

**Key fields**: `refid`, `descr`, `caref`, `crt` (base64 cert), `prv` (base64 private key,
persisted key only if `private_key_location=firewall`), `csr`. Import/issue-time fields:
`action` (internal/external/import/import_csr/sign_csr/reissue/manual), `key_type`,
`digest`, `cert_type`, `lifetime`, `private_key_location`, `crt_payload`/`csr_payload`/
`prv_payload` (raw PEM on the wire).

**Redact on read** (FR-017): `prv` and `prv_payload`, unconditionally, on both `Ca` and
`Cert` objects. **One documented exception to note in the contract, not silently drop**:
when a client requests `private_key_location=local`, the *add* action itself returns the
freshly generated key once, as `private_key`, in the same response — this is OPNsense's own
intentional one-shot disclosure at creation time, not a subsequent read. The redaction rule
applies to every *read* (`get`/`search`) response; the one-shot creation disclosure passes
through untouched (the caller just generated it and asked for it back), but the tool
docstring must say so explicitly so it isn't mistaken for a leak.

**Verified**: no dedicated `revoke` action exists (confirmed against docs and source).
Revocation is: fetch `Crl.get(caref)`, add the cert's `refid` into the appropriate
`revoked_reason_N` (0=unspecified … 6=certificateHold) bucket, POST the entire CRL state
back via `Crl.set(caref)`. The high-risk `certificate_revoke` tool wraps this
read-modify-write as one atomic operation from the client's perspective (matches FR-016).

---

## 8. High-Risk System Operations (User Story 6)

**Reboot/Halt — decision**: use `core/system/reboot` and `core/system/halt`
(`Core\Api\SystemController`) — fire-and-forget, immediate `{"status": "ok"}“, no progress
polling. **Not** `core/firmware/reboot`/`core/firmware/poweroff` (a separate pair used
specifically after a firmware operation, which returns a pollable `msg_uuid` — not
interchangeable, and irrelevant when the trigger isn't a firmware action).

**Firmware upgrade — decision**: expose both `core/firmware/update` (minor/patch, e.g.
26.7→26.7.2) and `core/firmware/upgrade` (major, e.g. 26.7→next major) as distinct
high-risk tools, since they're distinct OPNsense actions with distinct blast radius. Both
preceded by `core/firmware/check` (non-mutating) and polled via `core/firmware/status` /
`core/firmware/upgradestatus`. The confirmation preview for either tool includes the
pending-version info from `status` so the operator can evaluate it before confirming
(FR-009).

**Full configuration restore — ⚠ spec/API mismatch found, needs a decision** (see
"Discovered Spec Conflicts" below): `core/backup` (`Core\Api\BackupController`) only
manages backups already on disk (automatic per-save revision history) or on a remote
OPNcentral host — `providers`, `backups`, `diff`, `delete_backup`, `revert_backup`,
`download`. **There is no endpoint that accepts an arbitrary uploaded `config.xml` and
restores it.** That flow only exists as the legacy session/CSRF-protected multipart HTML
form (`src/www/diag_backup.php`), which is not a stable API contract to drive
programmatically.

**Interface reassignment/disable — ⚠ spec/API mismatch found, needs a decision** (see
below): **Verified via GitHub source** (`Interfaces\Api\AssignmentController`, merged
2026-06-07, PR opnsense/core#10366): reassignment (physical device ↔ logical interface,
e.g. `igb2` ↔ `opt3`) **is** exposed — `search_item`/`get_item`/`add_item`/`set_item`
(`$ifname`)/`del_item`(`$ifnames`)/`reconfigure`. **Enabling/disabling an interface or
editing its IP/media/MTU config is explicitly not exposed** — this was deliberately scoped
out of the MVC migration (tracked separately, still open, as `opnsense/core#10568`
"Interfaces: Assignments - add interface configuration settings"). That configuration
remains on the legacy non-API page `src/www/interfaces.php`.

---

## Note on URL casing conventions

Existing shipped code in this repo (`tools/dns.py`, `tools/dhcp.py`) calls camelCase action
segments directly (`searchHostOverride`, `addHostOverride`, `searchReservation`), matching
the PHP method name verbatim (minus the `Action` suffix). Current docs.opnsense.org pages
render the same actions in snake_case (`search_reservation`, `add_host_override`). Both
forms resolve to the same endpoint against a real OPNsense instance: the framework's
Phalcon-based dispatcher camelizes underscore/dash-delimited URL segments before resolving
an action method, and PHP method dispatch is case-insensitive, so a camelCase URL segment
also happens to match the same method by coincidence of case-folding. **New contracts in
this spec standardize on docs.opnsense.org's published snake_case form** for consistency
with the official reference; this doesn't imply the existing camelCase-calling code is
broken, and it's a task-level item to verify exact casing against a live 26.7.1 instance
during implementation regardless (contract docs describe intent; a live smoke test is the
actual source of truth before merging any new tool).

## Discovered Spec Conflicts Requiring a Decision

Two literal requirements in spec.md describe operations the current-stable OPNsense REST
API does not support, discovered during this research pass (not assumptions — verified
against source + a merged PR + a still-open follow-up issue):

1. **FR-018 / US6 AC2** — "full configuration restore (an XML document)": no REST endpoint
   accepts an arbitrary uploaded config and restores it. Only restoring an **existing
   on-disk backup revision** (`core/backup/revert_backup`) is possible via API.
2. **FR-018 / US6 AC4** — "interface be reassigned **or disabled**": reassignment is
   supported; disabling (or any IP/media config change) is not — and is deliberately out of
   scope upstream, not merely unimplemented yet.

**Recommendation carried into this plan** (pending spec owner sign-off, tracked as an open
item rather than silently implemented): narrow both to what the API actually supports —
config restore becomes "revert to an existing backup revision, selected from
`core/backup/backups`" (still high-risk, still gated by FR-008); interface "disable" is
dropped from scope, leaving reassignment only. This is Constitution Principle IV in
action (spec is authoritative, but FR-003 — no undocumented behavior — takes precedence
over implementing something that doesn't exist) rather than FR-002/FR-003 being quietly
worked around.
