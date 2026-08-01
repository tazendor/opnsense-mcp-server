# Implementation Plan: Complete OPNsense API Coverage (Read-Write)

**Branch**: `002-complete-api-coverage` | **Date**: 2026-07-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-complete-api-coverage/spec.md`

## Summary

Extend the existing OPNsense MCP server (39 tools, 8 domains, shipped as
001-opnsense-mcp-server) to full read-write coverage of System, DHCP, Interfaces, IDS,
and Services, and add six previously-uncovered domains: OpenVPN, IPsec, WireGuard, Web
Proxy, Captive Portal, and Trust/Certificates. Introduce one new cross-cutting
mechanism — a process-local confirm-then-execute safety layer — gating every
operation classified high-risk (system reboot/halt, firmware upgrade, config restore,
interface reassignment, VPN config teardown, certificate revocation, bulk captive-portal
disconnect). No new runtime dependencies; the safety layer is stdlib-only
(`secrets`, `time`, `dataclasses`), following the same thin-wrapper architecture 001
established (`tools/*.py` modules exposing `register_tools(mcp, client)`, backed by the
existing `OPNsenseClient`).

Research (see `research.md`) surfaced two literal requirements the current-stable
OPNsense REST API does not support — arbitrary-XML config restore, and interface
disable/IP-config — each narrowed to what the API actually exposes and flagged for spec
owner sign-off before those two specific tasks are implemented.

## Technical Context

**Language/Version**: Python 3.12+ (unchanged from 001)

**Primary Dependencies**: `mcp` ≥1.0, `httpx` ≥0.27 (unchanged — no new runtime
dependencies; the confirmation store uses only `secrets`/`time`/`dataclasses` from the
stdlib)

**Dev Dependencies**: `pytest` ≥8.0, `pytest-asyncio` ≥0.23, `respx` ≥0.21, `mypy` ≥1.10,
`ruff` ≥0.5 (unchanged)

**Storage**: N/A — stateless proxy, as in 001, with one addition: an in-process,
non-persistent dict of pending high-risk-operation confirmations
(`PendingOperationStore`, see `data-model.md`). Explicitly not persisted (spec
Assumptions); dropped on process restart.

**Testing**: `pytest` + `pytest-asyncio`; unit tests mock `OPNsenseClient`/`httpx` via
`respx`, extended to every new domain module; integration tests require a live OPNsense
instance (`pytest.mark.integration`, skipped when `OPNSENSE_*` env vars absent), extended
to cover each new domain's primary use case (SC-006); contract tests
(`tests/contract/test_tool_schemas.py`) extended to assert every registered tool has a
corresponding contract document (FR-002/SC-002 — this test currently only checks schema
shape, not contract-doc existence, and must be extended to fail if any tool lacks one).

**Target Platform**: unchanged (macOS 13+, Linux; CPython 3.12+).

**Project Type**: MCP server (unchanged).

**Performance Goals**: unchanged (≤50ms tool-call overhead above OPNsense API latency).
The confirmation store adds a single dict lookup/insert — negligible.

**Constraints**:
- All 001 constraints unchanged (`mypy --strict`, `ruff`, no caching, HTTPS only, no
  undocumented behavior).
- **New**: a high-risk tool MUST NOT issue its underlying OPNsense request until a valid,
  matching, unexpired confirmation token is supplied (FR-008).
- **New**: every read response in the certificate and VPN-peer domains MUST have private
  key fields redacted, with the two documented one-shot-disclosure exceptions noted in
  `research.md`/`contracts/trust.md`/`contracts/openvpn.md`/`contracts/wireguard.md`
  (FR-017).
- **New**: 100% of tools (including 001's pre-existing ones) must have a contract
  document — closes the gap this spec's own research found in 001's `dhcp.md`,
  `services.md`, and `system.md` contracts, which had drifted from the shipped
  implementation (FR-002/FR-006).
- **New**: each high-risk preview MUST emit its own diagnostic record (`outcome="preview"`)
  through the same `OPNsenseClient` logging path as real requests, distinguishable from the
  confirmed-execution record by a shared token, so an operator can audit both steps from
  the server's diagnostic log alone (FR-011/SC-005).

**Scale/Scope**: Single OPNsense instance per server process, unchanged. Domain count
grows from 8 to 14 (System, Firewall, Interfaces, Routes, DHCP, DNS, Services, IDS
unchanged/extended; OpenVPN, IPsec, WireGuard, Proxy, Captive Portal, Trust new). Tool
count grows from 39 to roughly 220 (see Tool Inventory) — driven mainly by IPsec's and
WireGuard's own API granularity (connections/locals/remotes/children,
servers/clients/keys), not by any design choice made here; each new tool maps 1:1 to a
real OPNsense endpoint per FR-003, none invented for symmetry.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### I. Simplicity First ✅

- The confirmation mechanism is the one new abstraction this spec introduces, and it's
  the simplest structure satisfying FR-007–FR-011: a dict + a dataclass + lazy expiry
  checks, no background tasks, no persistence, no generic decorator/middleware layer —
  each high-risk tool takes an explicit `confirm` parameter (see `research.md` §1 for why
  a decorator was rejected).
- No new abstraction unifies OpenVPN/IPsec/WireGuard into a common "VPN" interface —
  three concrete domain modules, matching three genuinely different OPNsense object
  shapes (Constitution: "three concrete duplications over a premature abstraction").
- Redaction is one small explicit-field-list helper (`redact_private_keys`), not a
  generic "looks like a secret" heuristic (research.md/data-model.md).
- Web Proxy's `Acl` controller (needs a second plugin, `os-OPNProxy` + `os-redis`) is
  deliberately left out of scope rather than speculatively wrapped (YAGNI).

### II. Idiomatic Python ✅

- New domain modules follow the exact `register_tools(mcp, client)` closure pattern
  already established by `tools/dns.py` et al. — no new pattern introduced.
- `PendingOperationStore` uses `secrets.token_urlsafe` and `time.monotonic()`, both
  stdlib, both idiomatic choices for opaque tokens and monotonic expiry respectively.
- No new runtime dependency added for this entire feature.

### III. Full Type Safety ✅

- `PendingOperation` is a frozen `dataclass`; every new tool function carries full type
  annotations, matching the existing convention in `tools/*.py`.
- `mypy --strict` remains a required quality gate; no new `Any` beyond the existing
  raw-JSON boundary already accepted in 001.

### IV. Specification-Driven Development ✅ (with two flagged exceptions)

- Every new tool traces to exactly one documented current-stable OPNsense endpoint
  (`contracts/`), verified against source (github.com/opnsense/core,
  github.com/opnsense/plugins) and cross-checked against docs.opnsense.org, not
  invented — see `research.md` for the verification method and two independently
  re-confirmed surprising findings (interface `AssignmentController`, captive portal
  bulk-disconnect gap).
- **Exception requiring spec owner sign-off before implementation** (Principle IV: "the
  specification is not updated retroactively to match a convenient implementation" — the
  correct order here is the reverse: the spec's own accuracy needs a small correction
  because it currently asks for something the API doesn't support, discovered only
  during planning, not convenience-motivated):
  1. FR-018/US6 AC2 ("full configuration restore... an XML document") — no such endpoint
     exists; narrowed to restoring an existing backup revision (`contracts/system.md`).
  2. FR-018/US6 AC4 ("interface be reassigned or disabled") — disable/IP-config isn't
     exposed by any current OPNsense REST API and is a deliberate upstream scope boundary
     (open issue `opnsense/core#10568`), not a gap that will close soon; narrowed to
     reassignment only (`contracts/interfaces.md`).

### V. Test-Driven Development ✅ (mandatory, unchanged process)

- tasks.md (next phase) will sequence a failing-test task before every implementation
  task, per domain module, matching 001's task ordering convention.
- The confirmation mechanism gets its own dedicated unit test module
  (`tests/unit/test_confirmation.py`) covering: preview issues a token without contacting
  OPNsense (mock asserts zero calls); confirmed call with a valid token contacts OPNsense
  exactly once; expired/mismatched/reused tokens raise `ToolError` without contacting
  OPNsense.
- The preview diagnostic record (FR-011/SC-005) is tested in `tests/unit/test_logging.py`
  (a preview emits one `outcome="preview"` record and zero HTTP calls) and demonstrated
  end-to-end on a real high-risk tool by the representative `system_reboot` test — so an
  operator can distinguish preview from confirmed execution in the server's own log.
- Contract tests extended per Constraints above to enforce FR-002/SC-002 (zero
  undocumented tools) as a CI-checkable gate, not just a manual review step.

**Complexity Tracking**: No unjustified violations. The two Constitution IV exceptions
above are spec-accuracy corrections, not complexity added for convenience — tracked as
open items needing sign-off, not silently resolved.

## Project Structure

### Documentation (this feature)

```text
specs/002-complete-api-coverage/
├── plan.md                    # This file
├── spec.md                    # Feature specification (already complete)
├── research.md                # Phase 0: endpoint verification + design decisions
├── data-model.md               # Phase 1: confirmation store + new domain entity shapes
├── quickstart.md               # Phase 1: end-to-end validation guide per user story
├── contracts/
│   ├── confirmation.md         # Cross-cutting confirm-then-execute pattern
│   ├── dhcp.md                 # Supersedes 001's (corrected + new writes)
│   ├── ids.md                  # New (001 shipped ids_ruleset_list without one)
│   ├── services.md             # Supersedes 001's (corrected + extended module list)
│   ├── system.md               # Supersedes 001's (corrected + high-risk ops)
│   ├── interfaces.md           # Extends 001's (assignment tools)
│   ├── openvpn.md               # New
│   ├── ipsec.md                 # New
│   ├── wireguard.md             # New
│   ├── proxy.md                 # New
│   ├── captiveportal.md         # New
│   └── trust.md                 # New
├── checklists/
│   └── requirements.md         # Spec quality checklist (already complete, all passing)
└── tasks.md                    # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
src/opnsense_mcp/
├── __init__.py
├── __main__.py
├── config.py                  # + OPNSENSE_CONFIRM_TTL env var
├── client.py                  # + log_preview() for FR-011/SC-005 preview records (still domain-agnostic)
├── errors.py                  # unchanged
├── confirmation.py            # NEW: PendingOperation, PendingOperationStore
├── redaction.py                # NEW: redact_private_keys() + per-domain field sets
├── server.py                  # + register new tool modules
└── tools/
    ├── __init__.py
    ├── system.py               # + reboot/halt/firmware/config-restore (confirmed)
    ├── firewall.py             # unchanged
    ├── interfaces.py           # + assignment CRUD + apply
    ├── routes.py                # unchanged
    ├── dhcp.py                  # + static mapping CRUD + settings update + apply
    ├── dns.py                    # unchanged
    ├── ids.py                    # + ruleset/rule toggle + apply
    ├── services.py               # + extended SUPPORTED_MODULES
    ├── openvpn.py                 # NEW
    ├── ipsec.py                    # NEW
    ├── wireguard.py                 # NEW
    ├── proxy.py                     # NEW
    ├── captiveportal.py              # NEW
    └── trust.py                      # NEW

tests/
├── unit/
│   ├── test_confirmation.py    # NEW — PendingOperationStore behavior
│   ├── test_redaction.py       # NEW
│   └── tools/
│       ├── test_system.py       # + high-risk op tests
│       ├── test_interfaces.py   # + assignment tests
│       ├── test_dhcp.py         # + write tests
│       ├── test_ids.py          # + toggle tests
│       ├── test_services.py     # + extended module list
│       ├── test_openvpn.py       # NEW
│       ├── test_ipsec.py          # NEW
│       ├── test_wireguard.py       # NEW
│       ├── test_proxy.py            # NEW
│       ├── test_captiveportal.py     # NEW
│       └── test_trust.py              # NEW
├── integration/
│   ├── test_system.py           # + high-risk op tests (against a disposable test VM only)
│   ├── test_vpn.py               # NEW — OpenVPN/IPsec/WireGuard end-to-end
│   ├── test_proxy.py              # NEW
│   ├── test_captiveportal.py       # NEW
│   └── test_trust.py                # NEW
└── contract/
    └── test_tool_schemas.py      # + assert every tool has a contracts/ entry (FR-002)
```

**Structure Decision**: Same single-project `src/` layout as 001 — this is additive to
the existing structure, not a restructure. Two new top-level modules
(`confirmation.py`, `redaction.py`) sit alongside `client.py`/`errors.py` as shared
infrastructure; six new `tools/*.py` domain modules follow the existing one-module-per-
domain convention exactly.

## Tool Inventory

Approximate new/changed tool counts by domain (exact names in `contracts/`):

| Domain | Status | Tools (new unless noted) |
|---|---|---|
| DHCP | extended | +5 (static add/update/delete, settings update, apply) → 8 total |
| IDS | extended | +3 (ruleset toggle, rule toggle, apply) → 4 total |
| Services | extended | unchanged count (4), module enum 3→8 |
| System | extended | +9 (reboot, halt, firmware check/update/upgrade/upgradestatus/log, config restore, backup list) → 12 total |
| Interfaces | extended | +6 (assignment list/get/add/update/delete, apply) → 10 total |
| OpenVPN | new | ~23 |
| IPsec | new | ~51 |
| WireGuard | new | ~25 |
| Web Proxy | new | ~28 |
| Captive Portal | new | ~15 |
| Trust/Certificates | new | ~18 |
| **Total server tool count** | | **39 → ~222** |

This is a large surface driven by IPsec's and WireGuard's own object granularity
(connections/auth-rounds/children; servers/clients/keys/builders), not padding — every
row is a distinct documented OPNsense action. `tasks.md` breaks this down per user story
priority (P1–P6) so implementation can land and be reviewed incrementally rather than as
one 220-tool change.
