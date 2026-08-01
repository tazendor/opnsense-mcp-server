---
description: "Task list for Complete OPNsense API Coverage (Read-Write)"
---

# Tasks: Complete OPNsense API Coverage (Read-Write)

**Input**: Design documents from `specs/002-complete-api-coverage/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅

**TDD**: Tests are MANDATORY on this project (constitution Principle V). Every
implementation task is preceded by a test task. Tests MUST fail before implementation
begins.

**Two open items requiring spec owner sign-off** before their tasks are considered
done (not just implemented) — see `research.md` "Discovered Spec Conflicts": T0xx
(`system_config_restore`, narrowed to existing-backup-revision restore) and T0xx
(`interface_assignment_update/_delete`, "disable" dropped from scope). Both are marked
below.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to ([US1]–[US6])
- All file paths are relative to the repository root

---

## Phase 1: Setup

**Purpose**: Scaffold new modules and test files so later phases only add content, not
new files (avoids merge collisions between parallel [P] tasks).

- [ ] T001 Create stub files: `src/opnsense_mcp/confirmation.py`, `src/opnsense_mcp/redaction.py` (empty modules), `src/opnsense_mcp/tools/{openvpn,ipsec,wireguard,proxy,captiveportal,trust}.py` (each with an empty `register_tools(mcp: FastMCP, client: OPNsenseClient) -> None: pass` stub), `tests/unit/test_confirmation.py`, `tests/unit/test_redaction.py`, `tests/unit/tools/{test_openvpn,test_ipsec,test_wireguard,test_proxy,test_captiveportal,test_trust}.py`, `tests/integration/{test_vpn,test_proxy,test_captiveportal,test_trust}.py` (all empty)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The one truly cross-cutting piece every later phase relies on for
correctness verification — the contract-completeness gate (FR-002/SC-002) — plus the
new config field the safety layer needs. Independent of User Story 1 (US1 needs neither);
required before Polish can validate SC-002 across the whole tool surface.

### Tests for Foundational (RED)

- [ ] T002 [P] Add failing assertions to `tests/unit/test_config.py`: `OPNSENSE_CONFIRM_TTL` env var parsed as `float` into a new `Config.confirm_ttl_seconds` field, default `120.0` when unset, same env-overrides-TOML precedence as existing fields
- [ ] T003 [P] Add a failing test to `tests/contract/test_tool_schemas.py`: for every tool name returned by the running server's tool registry, assert a `## Tool: \`<name>\`` (or `### Tool: \`<name>\`` for sub-headings) heading exists somewhere under `specs/001-opnsense-mcp-server/contracts/*.md` or `specs/002-complete-api-coverage/contracts/*.md`, and fail loudly (listing the missing names) if not — this is the automated form of FR-002/SC-002, not just a manual review step

**Checkpoint**: `pytest tests/unit/test_config.py tests/contract/test_tool_schemas.py` — the new assertions MUST report FAILED (the contract-scan test will fail harmlessly here since it only checks already-shipped tools, which already have contracts as of this plan — if it passes immediately, still add it; the RED requirement applies to genuinely new assertions, not this one if it's vacuously green because 001+002's docs already reconcile 001's drift).

### Implementation for Foundational (GREEN)

- [ ] T004 [P] Extend `src/opnsense_mcp/config.py`: add `confirm_ttl_seconds: float = 120.0` to `Config`, wire through `from_env`/`from_toml`/`load` following the existing `_f()` pattern
- [ ] T005 [P] Implement the contract-completeness scanner in `tests/contract/test_tool_schemas.py`: parse `## Tool: \`name\`` headings from all `contracts/*.md` files across both spec folders into a set, compare against `server.list_tools()` (or equivalent FastMCP introspection), assert set equality (extra contract entries for not-yet-registered tools are fine mid-implementation — only *missing* contracts for *registered* tools should fail)

**Checkpoint**: tests pass; `mypy --strict src/` and `ruff check .` clean.

---

## Phase 3: User Story 1 — Complete Network & Service Configuration Writes (Priority: P1) 🎯 MVP

**Goal**: DHCP static mappings, DHCP settings, and IDS ruleset/rule state become
writable; the Services module list is reconciled with reality (FR-004–FR-006).

**Independent Test**: List DHCP static mappings, add one, apply, verify it appears,
remove it. Toggle an IDS ruleset's enabled state, apply, verify a subsequent list
reflects it. No dependency on any other phase.

**Tools in scope**: `dhcp_static_add/_update/_delete`, `dhcp_settings_update`,
`dhcp_apply` (`contracts/dhcp.md`); `ids_ruleset_toggle`, `ids_rule_toggle`, `ids_apply`
(`contracts/ids.md`); extended `SUPPORTED_MODULES` (`contracts/services.md`).

### Tests for User Story 1 (RED)

- [ ] T006 [P] [US1] Add failing unit tests to `tests/unit/tools/test_dhcp.py`: `dhcp_static_add` posts to `kea/dhcpv4/add_reservation` with the reservation body and returns `{"result": "saved", "uuid": ...}`; `dhcp_static_update`/`_delete` hit `set_reservation/{uuid}`/`del_reservation/{uuid}`; `dhcp_settings_update` posts to `kea/dhcpv4/set`; `dhcp_apply` posts to `kea/service/reconfigure`; `OPNsenseAPIError` surfaces as `ToolError` for each
- [ ] T007 [P] [US1] Create failing unit tests in `tests/unit/tools/test_ids.py`: `ids_ruleset_list` (existing tool — add contract-doc-backed assertions if missing), `ids_ruleset_toggle` posts to `ids/settings/toggle_ruleset` with `filenames`/`enabled`, `ids_rule_toggle` posts to `ids/settings/toggle_rule` with `sids`/`enabled`, `ids_apply` posts to `ids/service/reconfigure`
- [ ] T008 [P] [US1] Add a failing assertion to `tests/unit/tools/test_services.py`: `SUPPORTED_MODULES` includes `unbound, kea, ids, openvpn, ipsec, wireguard, proxy, captiveportal`; calling any service tool with a module outside this set still raises `ToolError` before any HTTP call
- [ ] T009 [P] [US1] Create failing integration tests in `tests/integration/test_dhcp.py` (new) covering the full add→apply→list→delete→apply cycle against a live instance, marked `pytest.mark.integration`

**Checkpoint**: `pytest tests/unit/tools/test_dhcp.py tests/unit/tools/test_ids.py tests/unit/tools/test_services.py` — new assertions MUST report FAILED.

### Implementation for User Story 1 (GREEN)

- [ ] T010 [US1] Extend `src/opnsense_mcp/tools/dhcp.py`: add `_dhcp_static_add/_update/_delete`, `_dhcp_settings_update`, `_dhcp_apply` per `contracts/dhcp.md`; register all five in `register_tools()`
- [ ] T011 [US1] Extend `src/opnsense_mcp/tools/ids.py`: add `_ids_ruleset_toggle`, `_ids_rule_toggle`, `_ids_apply` per `contracts/ids.md`; register in `register_tools()`
- [ ] T012 [US1] Extend `SUPPORTED_MODULES` in `src/opnsense_mcp/tools/services.py` to `frozenset({"unbound", "kea", "ids", "openvpn", "ipsec", "wireguard", "proxy", "captiveportal"})`

**Checkpoint**: all US1 tests pass; `mypy --strict src/` and `ruff check .` clean. Ship as
an independent increment if desired — no dependency on any later phase.

---

## Phase 4: User Story 2 — Confirm-Then-Execute Safety Layer (Priority: P2)

**Goal**: Build the shared, in-process confirmation mechanism every high-risk tool in
Phases 5–8 will use (FR-007–FR-011). No MCP tool is owned by this phase itself — it's
pure infrastructure, exercised directly at the store level so it's independently testable
without any later phase existing yet (spec's own "Independent Test" describes the
generic preview→confirm→execute shape, which this phase's unit tests demonstrate
directly against `PendingOperationStore`, without needing a real tool wired up).

**Independent Test**: Directly exercise `PendingOperationStore.create()`/`.consume()`:
create a pending operation, assert nothing resembling an HTTP call happened; consume it
with matching tool/arguments and assert it succeeds exactly once; consume again and
assert it's rejected (single-use); create another, let it expire, assert consuming it is
rejected.

**Also in scope**: the redaction helper (FR-017) — grouped here because, like the
confirmation store, it's shared safety infrastructure consumed by later phases rather
than owned by any single one.

### Tests for User Story 2 (RED)

- [ ] T013 [P] [US2] Write failing unit tests in `tests/unit/test_confirmation.py`: `create()` returns a `PendingOperation` with a unique token, the given description, and an expiry in the future; `consume(token, tool_name, arguments)` with an exact match succeeds and removes the entry (a second `consume()` with the same token then raises `ToolError`); `consume()` with a wrong `tool_name` or different `arguments` (same token) raises `ToolError` without removing the entry's ability to be looked up correctly by its real owner; `consume()` on an unknown token raises `ToolError`; `consume()` on an expired token (use a `ttl_seconds` near zero and a short sleep, or inject a fake clock) raises `ToolError`
- [ ] T014 [P] [US2] Write failing unit tests in `tests/unit/test_redaction.py`: `redact_private_keys(obj, frozenset({"prv", "privkey"}))` removes exactly those top-level keys when present, leaves all other keys untouched, doesn't mutate the input dict (returns a copy), and no-ops cleanly when none of the target fields are present

**Checkpoint**: `pytest tests/unit/test_confirmation.py tests/unit/test_redaction.py` —
MUST report FAILED.

### Implementation for User Story 2 (GREEN)

- [ ] T015 [US2] Implement `src/opnsense_mcp/confirmation.py`: `PendingOperation` frozen dataclass (`token`, `tool_name`, `arguments`, `description`, `expires_at`), `PendingOperationStore(ttl_seconds: float = 120.0)` with `create(tool_name, arguments, description) -> PendingOperation` (uses `secrets.token_urlsafe(32)`, `time.monotonic()`), `consume(token, tool_name, arguments) -> PendingOperation` (raises `ToolError` on any mismatch/expiry/absence; removes on success), private `_evict_expired()` called from both methods
- [ ] T016 [P] [US2] Implement `src/opnsense_mcp/redaction.py`: `redact_private_keys(obj: dict[str, Any], fields: frozenset[str]) -> dict[str, Any]`

**Checkpoint**: tests pass; `mypy --strict src/` and `ruff check .` clean. This phase
unblocks the high-risk-tool tasks in Phases 5–8 (each such task is annotated below).

---

## Phase 5: User Story 3 — Manage VPN Tunnels (Priority: P3)

**Goal**: Full read-write coverage of OpenVPN, IPsec, and WireGuard per
`contracts/openvpn.md`, `contracts/ipsec.md`, `contracts/wireguard.md`.

**Independent Test**: List OpenVPN instances and status; start a stopped instance and
confirm its status changes; add a WireGuard peer, verify it appears, then remove it.

**Depends on Phase 4** only for the config-teardown tools specifically
(`openvpn_instance_delete`, `ipsec_connection_delete`, `ipsec_enabled_toggle`,
`wireguard_server_delete`) — every other tool in this phase has no dependency on it.

### OpenVPN

- [ ] T017 [P] [US3] Write failing unit tests in `tests/unit/tools/test_openvpn.py` for instance + static-key CRUD (`search`/`get`/`add`/`set`/`del`/`toggle` on instances; `search_static_key`.../`gen_key`), asserting `key` is absent from list/get responses (FR-017) and present, unredacted, in `gen_key`'s response
- [ ] T018 [US3] Implement instance + static-key tools in `src/opnsense_mcp/tools/openvpn.py` per `contracts/openvpn.md`, applying `redact_private_keys` to `StaticKeys.StaticKey.key` on read; `openvpn_instance_delete` takes `confirm` and calls `PendingOperationStore` per `contracts/confirmation.md`
- [ ] T019 [P] [US3] Write failing unit tests for client overrides, sessions/routes, kill-session, service start/stop/restart, and `openvpn_apply` in `tests/unit/tools/test_openvpn.py`
- [ ] T020 [US3] Implement the remainder of `src/opnsense_mcp/tools/openvpn.py`: client overrides, `openvpn_session_list`/`_route_list`/`_session_kill`, service lifecycle, `openvpn_apply`

**Checkpoint**: `pytest tests/unit/tools/test_openvpn.py` all pass; `mypy --strict`/`ruff` clean.

### IPsec

- [ ] T021 [P] [US3] Write failing unit tests in `tests/unit/tools/test_ipsec.py` for connections + local/remote auth rounds (CRUD + toggle), asserting `ipsec_connection_delete` requires `confirm`
- [ ] T022 [US3] Implement connections + local/remote tools in `src/opnsense_mcp/tools/ipsec.py`; `ipsec_connection_delete` and `ipsec_enabled_toggle` (disabling) gated via `PendingOperationStore`
- [ ] T023 [P] [US3] Write failing unit tests for children (phase 2) and pools in `tests/unit/tools/test_ipsec.py`
- [ ] T024 [US3] Implement child + pool tools in `src/opnsense_mcp/tools/ipsec.py`
- [ ] T025 [P] [US3] Write failing unit tests for keypairs, PSKs, and their generators in `tests/unit/tools/test_ipsec.py`, asserting `privateKey`/`Key` are redacted on read but present in the `gen_key_pair` generator response
- [ ] T026 [US3] Implement keypair + PSK tools in `src/opnsense_mcp/tools/ipsec.py`, applying `redact_private_keys`
- [ ] T027 [P] [US3] Write failing unit tests for sessions (phase1/phase2 search, connect/disconnect), service lifecycle, and `ipsec_apply` in `tests/unit/tools/test_ipsec.py`
- [ ] T028 [US3] Implement session + service tools and `ipsec_apply` in `src/opnsense_mcp/tools/ipsec.py`

**Checkpoint**: `pytest tests/unit/tools/test_ipsec.py` all pass; `mypy --strict`/`ruff` clean.

### WireGuard

- [ ] T029 [P] [US3] Write failing unit tests in `tests/unit/tools/test_wireguard.py` for server CRUD + keypair generation (assert `privkey` redacted on read, present in `key_pair` generator) and client/peer CRUD (assert no private-key field is ever expected/redacted — document the no-op explicitly per `contracts/wireguard.md`), asserting `wireguard_server_delete` requires `confirm`
- [ ] T030 [US3] Implement server + client tools in `src/opnsense_mcp/tools/wireguard.py` per `contracts/wireguard.md`; `wireguard_server_delete` gated via `PendingOperationStore`
- [ ] T031 [P] [US3] Write failing unit tests for general settings, client-builder helpers, service lifecycle, `wireguard_status` (`show`), and `wireguard_apply` in `tests/unit/tools/test_wireguard.py`
- [ ] T032 [US3] Implement the remainder of `src/opnsense_mcp/tools/wireguard.py`

**Checkpoint**: `pytest tests/unit/tools/test_wireguard.py` all pass; `mypy --strict`/`ruff`
clean. Wire all three modules into `src/opnsense_mcp/server.py`.

- [ ] T033 [P] [US3] Write failing integration tests in `tests/integration/test_vpn.py`: OpenVPN instance list/status, WireGuard add-peer→apply→list→remove→apply, IPsec connection list, marked `pytest.mark.integration`
- [ ] T034 [US3] (no implementation task — integration tests validate T017–T032; run against a live instance)

---

## Phase 6: User Story 4 — Manage Web Proxy and Captive Portal (Priority: P4)

**Goal**: Full read-write coverage of Squid proxy settings and Captive Portal zones/sessions
per `contracts/proxy.md`, `contracts/captiveportal.md`.

**Independent Test**: List proxy configuration and captive portal zones; add a proxy
access rule and verify it appears; list active captive portal sessions and disconnect one.

**Depends on Phase 4** only for `captiveportal_session_disconnect_zone`.

### Web Proxy

- [ ] T035 [P] [US4] Write failing unit tests in `tests/unit/tools/test_proxy.py` for `proxy_settings_get/_update` (including the flat ACL CSV fields under `forward.acl`) and remote-blacklist CRUD, asserting blacklist `password` is redacted on read
- [ ] T036 [US4] Implement settings + remote-blacklist tools in `src/opnsense_mcp/tools/proxy.py` per `contracts/proxy.md`, applying redaction to blacklist `password`
- [ ] T037 [P] [US4] Write failing unit tests for PAC rule/proxy/match CRUD, service lifecycle, `proxy_service_reset`, and `proxy_apply` in `tests/unit/tools/test_proxy.py`
- [ ] T038 [US4] Implement PAC + service tools in `src/opnsense_mcp/tools/proxy.py`

**Checkpoint**: `pytest tests/unit/tools/test_proxy.py` all pass; `mypy --strict`/`ruff` clean.

### Captive Portal

- [ ] T039 [P] [US4] Write failing unit tests in `tests/unit/tools/test_captiveportal.py` for zone CRUD, `captiveportal_session_list/_zone_names/_connect/_disconnect` (single-session, no `confirm` required)
- [ ] T040 [US4] Implement zone + single-session tools in `src/opnsense_mcp/tools/captiveportal.py` per `contracts/captiveportal.md`
- [ ] T041 [P] [US4] Write failing unit tests for `captiveportal_session_disconnect_zone` in `tests/unit/tools/test_captiveportal.py`: unconfirmed call enumerates sessions via a (non-mutating) `session/list` call for the preview description but issues zero `session/disconnect` calls; confirmed call issues exactly one `session/disconnect` per session found, reporting per-session success/failure; service lifecycle + `captiveportal_apply`
- [ ] T042 [US4] Implement `captiveportal_session_disconnect_zone` in `src/opnsense_mcp/tools/captiveportal.py`, gated via `PendingOperationStore`, plus service + apply tools

**Checkpoint**: `pytest tests/unit/tools/test_captiveportal.py` all pass; `mypy --strict`/`ruff`
clean. Wire both modules into `server.py`.

- [ ] T043 [P] [US4] Write failing integration tests in `tests/integration/test_proxy.py` and `tests/integration/test_captiveportal.py`, marked `pytest.mark.integration`

---

## Phase 7: User Story 5 — Manage Certificates and PKI (Priority: P5)

**Goal**: Full read-write coverage of CAs, certificates, and revocation per
`contracts/trust.md`.

**Independent Test**: List CAs/certificates; import a certificate and verify it appears;
revoke a certificate and verify its status changes.

**Depends on Phase 4** only for `trust_certificate_revoke`.

- [ ] T044 [P] [US5] Write failing unit tests in `tests/unit/tools/test_trust.py` for `trust_ca_*`/`trust_certificate_*` CRUD and `trust_certificate_export`: assert `prv`/`prv_payload` redacted on every `_list`/`_get`; assert the one-shot `private_key_location=local` disclosure on `_add` passes through unredacted; assert `_export(type="prv"|"pkcs12")` is unredacted by design
- [ ] T045 [US5] Implement CA + certificate CRUD + export tools in `src/opnsense_mcp/tools/trust.py` per `contracts/trust.md`, applying `redact_private_keys` only to the `_list`/`_get` paths
- [ ] T046 [P] [US5] Write failing unit tests for `trust_certificate_revoke` (read-modify-write against `Crl.get`/`Crl.set`, requires `confirm`) and `trust_crl_list/_get`, `trust_settings_get/_update` in `tests/unit/tools/test_trust.py`
- [ ] T047 [US5] Implement `trust_certificate_revoke` in `src/opnsense_mcp/tools/trust.py`, gated via `PendingOperationStore`; implement `trust_crl_*` and `trust_settings_*`

**Checkpoint**: `pytest tests/unit/tools/test_trust.py` all pass; `mypy --strict`/`ruff`
clean. Wire into `server.py`.

- [ ] T048 [P] [US5] Write failing integration tests in `tests/integration/test_trust.py`, marked `pytest.mark.integration`

---

## Phase 8: User Story 6 — Perform High-Risk System Operations (Priority: P6)

**Goal**: System reboot/halt, firmware update/upgrade, configuration restore, and
interface reassignment, all gated by the Phase 4 safety layer, per `contracts/system.md`
and `contracts/interfaces.md`.

**Independent Test**: Request a system reboot; verify a preview is returned and OPNsense
is not contacted until confirmed; confirm and verify exactly one request is sent.

**Depends entirely on Phase 4** — every tool in this phase is high-risk.

**⚠️ Two tasks below require spec owner sign-off before being marked done** (narrowed
scope vs. the literal spec text — see `research.md`).

### System

- [ ] T049 [P] [US6] Write failing unit tests in `tests/unit/tools/test_system.py` for `system_reboot`/`system_halt`: unconfirmed call makes zero HTTP calls and returns a preview; confirmed call makes exactly one `POST core/system/reboot`(or `/halt`); reused/expired/mismatched tokens raise `ToolError`
- [ ] T050 [US6] Implement `system_reboot`/`system_halt` in `src/opnsense_mcp/tools/system.py`, gated via `PendingOperationStore` — the representative case for the whole confirm-then-execute mechanism (spec's own US2 Independent Test)
- [ ] T051 [P] [US6] Write failing unit tests for `system_firmware_check`, `_update`, `_upgrade`, `_upgrade_status`, `_log` in `tests/unit/tools/test_system.py`, asserting `_update`/`_upgrade` require `confirm`
- [ ] T052 [US6] Implement firmware tools in `src/opnsense_mcp/tools/system.py`
- [ ] T053 [P] [US6] **[needs spec owner sign-off — research.md conflict #1]** Write failing unit tests for `system_config_restore` (narrowed to restoring an existing backup revision via `core/backup/revert_backup`, preview built from `core/backup/diff`) and `system_config_backup_list` in `tests/unit/tools/test_system.py`
- [ ] T054 [US6] **[needs spec owner sign-off]** Implement `system_config_restore`/`_backup_list` in `src/opnsense_mcp/tools/system.py`, gated via `PendingOperationStore`

**Checkpoint**: `pytest tests/unit/tools/test_system.py` all pass; `mypy --strict`/`ruff`
clean.

### Interfaces

- [ ] T055 [P] [US6] Write failing unit tests in `tests/unit/tools/test_interfaces.py` for `interface_assignment_list/_get/_add` (standard risk) and `_update`/`_delete` (require `confirm`) and `interface_apply`
- [ ] T056 [US6] **[needs spec owner sign-off — research.md conflict #2, "disable" dropped from scope]** Implement assignment tools in `src/opnsense_mcp/tools/interfaces.py` per `contracts/interfaces.md`, `_update`/`_delete` gated via `PendingOperationStore`

**Checkpoint**: `pytest tests/unit/tools/test_interfaces.py` all pass; `mypy --strict`/`ruff`
clean. Wire `system.py`'s new tools and `interfaces.py`'s new tools (already registered
module) into `server.py`.

- [ ] T057 [P] [US6] Write failing integration tests in `tests/integration/test_system.py` additions for the high-risk ops, explicitly documented as **disposable-test-VM-only, never run against production or in shared CI**, marked `pytest.mark.integration`

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T058 Run the Phase 2 contract-completeness scanner (`tests/contract/test_tool_schemas.py`) across the full ~222-tool surface; fix any straggling contract gaps
- [ ] T059 [P] Regenerate `docs/mcp-tools.md` (the cross-cutting tool inventory started before this plan) to include every domain added in this feature, with the same read/write-type table format already established
- [ ] T060 Full quality gate: `uv run pytest` (unit, excluding integration), `uv run mypy --strict src/`, `uv run ruff check .`, `uv run ruff format --check .` — all clean
- [ ] T061 Confirm spec owner sign-off obtained for both flagged scope narrowings (T053/T054 config restore, T056 interface disable) — update `spec.md`'s FR-018/US6 AC2/AC4 text to match the shipped scope once agreed, rather than leaving the literal text unresolved
- [ ] T062 Walk through `quickstart.md` end-to-end against a live (non-production) OPNsense instance, one section per user story

---

## Dependencies & Execution Order

- **Phase 1 (Setup)** → no dependencies.
- **Phase 2 (Foundational)** → depends on Phase 1. Independent of Phase 3 (US1) — the two
  may run in parallel.
- **Phase 3 (US1)** → depends only on Phase 1. No dependency on Phase 2 or Phase 4.
- **Phase 4 (US2 — safety layer)** → depends only on Phase 1. Independent of Phase 3.
- **Phase 5 (US3 — VPN)** → depends on Phase 1; depends on Phase 4 **only** for the
  four config-teardown tools called out in that phase.
- **Phase 6 (US4 — Proxy/Portal)** → same shape, depends on Phase 4 only for
  `captiveportal_session_disconnect_zone`.
- **Phase 7 (US5 — Trust)** → depends on Phase 4 only for `trust_certificate_revoke`.
- **Phase 8 (US6 — high-risk system ops)** → depends on Phase 4 entirely (every tool
  in this phase is gated).
- **Phase 9 (Polish)** → depends on all prior phases.

Suggested order for a solo implementer: **1 → 2 → 4 → 3 → 5 → 6 → 7 → 8 → 9** (build
the safety layer right after setup since five of the six later phases need at least one
tool gated by it; US1 can slot in anywhere since it's fully independent).

---

## Parallel Example: User Story 3 (VPN)

```bash
# After Phase 4 (safety layer) is green, these three test-writing tasks
# touch different files and can run simultaneously:
Task: "T017 — OpenVPN instance/static-key tests in tests/unit/tools/test_openvpn.py"
Task: "T021 — IPsec connection/local/remote tests in tests/unit/tools/test_ipsec.py"
Task: "T029 — WireGuard server/client tests in tests/unit/tools/test_wireguard.py"

# Their corresponding implementation tasks (T018, T022, T030) can also run in
# parallel once each domain's own RED checkpoint is confirmed.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 (Setup) → Phase 2 (Foundational, config field only — US1 doesn't need the
   confirmation store) → Phase 3 (US1: T006–T012)
2. **STOP and VALIDATE**: add a DHCP static mapping end-to-end via a real MCP client
3. Ship as v0.3.0 if desired — no dependency on the safety layer or any new domain

### Incremental Delivery

- Phase 1+2 → tooling ready
- Phase 3 → US1 ships (DHCP/IDS/Services completion) → v0.3.0
- Phase 4 → safety layer ships (no user-visible tool yet, but unblocks the rest)
- Phase 5 → US3 ships (VPN) → v0.4.0
- Phase 6 → US4 ships (Proxy/Captive Portal) → v0.5.0
- Phase 7 → US5 ships (Certificates) → v0.6.0
- Phase 8 → US6 ships (high-risk system ops) → v1.0.0, pending the two sign-offs
- Phase 9 → Polish → v1.0.0 production-ready

### TDD Cycle Per Phase (mandatory)

1. Write tests (RED tasks marked [P] within phase) — run pytest, confirm FAILED
2. Implement (GREEN tasks) — run pytest until PASSED
3. Refactor — run ruff + mypy, fix issues
4. Checkpoint: all tests green, zero lint/type errors — advance to next phase

---

## Notes

- [P] tasks = different files, no dependencies on each other within the phase
- [USN] label maps task to its user story for traceability
- Tests MUST fail before implementation (Principle V — non-negotiable)
- Each user story phase is independently completable and testable, modulo the
  narrow cross-phase dependencies on Phase 4 called out above
- Commit after each phase checkpoint, not after every task
- `mypy --strict src/` MUST pass at every phase checkpoint (Principle III)
- `ruff check` MUST pass at every phase checkpoint (Principle II)
- Stop at any checkpoint to validate the story independently before advancing
- T053/T054/T056 are implementable as designed (narrowed scope), but should not be
  considered spec-complete until the sign-off in T061 happens
