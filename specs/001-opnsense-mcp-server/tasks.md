---
description: "Task list for OPNsense MCP Server"
---

# Tasks: OPNsense MCP Server

**Input**: Design documents from `specs/001-opnsense-mcp-server/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅

**TDD**: Tests are MANDATORY on this project (constitution Principle V). Every implementation
task is preceded by a test task. Tests MUST fail before implementation begins.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to ([US1]–[US4])
- All file paths are relative to the repository root

---

## Phase 1: Setup

**Purpose**: Initialise the Python project, directory structure, and tooling.

- [ ] T001 Create `pyproject.toml` with project metadata (`opnsense-mcp`, Python ≥3.12, entry point `opnsense-mcp = "opnsense_mcp.__main__:main"`), runtime dependencies (`mcp>=1.0`, `httpx>=0.27`), dev dependencies (`pytest>=8.0`, `pytest-asyncio>=0.23`, `respx>=0.21`, `mypy>=1.10`, `ruff>=0.5`), and tool sections: ruff (lint + format), mypy (`strict = true`), pytest (`asyncio_mode = "auto"`)
- [ ] T002 [P] Create `src/opnsense_mcp/` package: empty `__init__.py`, `__main__.py`, `config.py`, `client.py`, `errors.py`, `server.py`, and `src/opnsense_mcp/tools/__init__.py` plus empty tool stubs `system.py`, `firewall.py`, `interfaces.py`, `routes.py`, `dhcp.py`, `dns.py`, `services.py`
- [ ] T003 [P] Create `tests/` directory tree: `tests/conftest.py`, `tests/unit/test_config.py`, `tests/unit/test_client.py`, `tests/unit/test_errors.py`, `tests/unit/tools/` (empty), `tests/integration/conftest.py` (adds `pytest.mark.integration` skip when `OPNSENSE_URL` env var absent), `tests/contract/test_tool_schemas.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure — `Config`, `OPNsenseClient`, error types, server
factory, and CLI entry point — required before any user story can be implemented.

**⚠️ CRITICAL**: No user story work begins until this phase is complete.

### Shared Test Infrastructure (must precede RED tests)

- [ ] T012 Add shared test fixtures to `tests/conftest.py`: `test_config: Config` fixture returning a `Config` instance with fake credentials (`url="https://fake.opnsense.example"`, dummy api_key/secret, defaults for all other fields); `mock_client` fixture returning an `AsyncMock` of `OPNsenseClient` with configurable `.get`, `.get_text`, and `.post` return values. These fixtures are referenced by T004–T006 and all domain test tasks — they MUST exist before any test file is written.

### Tests for Foundational (RED — must fail before implementation)

- [ ] T004 [P] Write failing unit tests for `Config` in `tests/unit/test_config.py`: env var loading (`OPNSENSE_URL`, `OPNSENSE_API_KEY`, `OPNSENSE_API_SECRET`, timeouts, transport), TOML file loading and merge precedence (env overrides TOML), `__post_init__` validation errors (missing `api_key`, non-`https://` URL, negative timeout, port out of range), `Config.load()` integration
- [ ] T005 [P] Write failing unit tests for `OPNsenseClient` in `tests/unit/test_client.py` using `respx` to mock httpx: verify Basic Auth header sent; `get()` on a JSON endpoint returns parsed `dict`; `get_text()` on an XML endpoint returns raw response body as `str` without JSON parsing; `post()` with JSON body returns parsed dict; `ConnectTimeout` maps to `OPNsenseAPIError` with clear message; `ReadTimeout` maps to clear timeout message; HTTP 401/403/404/500 responses map to `OPNsenseAPIError` with `status_code` and `body`; each call (get, get_text, post) produces a log record
- [ ] T006 [P] Write failing unit tests for error types in `tests/unit/test_errors.py`: `OPNsenseAPIError` construction (status_code, body, path, method fields), `str()` representation includes status code and path, `ToolError` wraps an `OPNsenseAPIError` into a human-readable MCP-safe string

**Checkpoint**: Run `pytest tests/unit/test_config.py tests/unit/test_client.py tests/unit/test_errors.py` — all tests MUST report FAILED before proceeding.

### Implementation for Foundational (GREEN)

- [ ] T007 Implement `src/opnsense_mcp/config.py`: `Config` dataclass with all fields from data-model.md, `__post_init__` validation, `Config.from_env() -> Config`, `Config.from_toml(path: Path) -> Config` using stdlib `tomllib`, `Config.load() -> Config` (env vars override TOML file values, TOML optional)
- [ ] T008 [P] Implement `src/opnsense_mcp/errors.py`: `OPNsenseAPIError(Exception)` dataclass with `status_code: int`, `body: dict[str, Any]`, `path: str`, `method: str`; `ToolError` string formatter that produces MCP-safe output including status code, path, and OPNsense body
- [ ] T009 Implement `src/opnsense_mcp/client.py`: `OPNsenseClient` async context manager wrapping `httpx.AsyncClient(auth=BasicAuth, verify=config.verify_tls, timeout=Timeout(connect=..., read=...))`; `async def get(path: str) -> dict[str, Any]` (parses response as JSON); `async def get_text(path: str) -> str` (returns raw response body as string, for non-JSON endpoints such as XML config backup); `async def post(path: str, data: dict[str, Any] | None = None) -> dict[str, Any]`; each call logs `{timestamp} {method} {path} status={code} outcome={success|error|timeout}` to stderr; `get` and `post` raise `OPNsenseAPIError` on non-2xx; `get_text` raises `OPNsenseAPIError` on non-2xx; all three raise `ToolError` on timeout or connection error
- [ ] T010 Implement `src/opnsense_mcp/server.py`: `create_server(config: Config) -> FastMCP` that instantiates `FastMCP("opnsense-mcp-server")`, calls `register_tools(mcp, client)` for each domain module (system, firewall, interfaces, routes, dhcp, dns, services), and returns the configured server; create shared `OPNsenseClient` passed to all domain modules
- [ ] T011 Implement `src/opnsense_mcp/__main__.py`: `main()` function that calls `Config.load()`, validates required fields (exit 1 with clear message on missing), probes OPNsense with `GET /api/core/dashboard/get` to confirm credentials before accepting connections (exit 1 with 401/connection error detail on failure), selects transport (`stdio` or `http`) from config, raises clear `OSError` on HTTP port already in use
- [ ] T013 [P] Implement `src/opnsense_mcp/__init__.py`: set `__version__ = "0.1.0"`

**Checkpoint**: `pytest tests/unit/test_config.py tests/unit/test_client.py tests/unit/test_errors.py` — all PASS. Then: `mypy --strict src/` zero errors, `ruff check src/ tests/` zero errors.

---

## Phase 3: User Story 1 — Query Firewall & System Status (Priority: P1) 🎯 MVP

**Goal**: MCP client can query live system status, interface state, and DHCP leases.

**Independent Test**: Connect an MCP client; call `system_status`, `interface_config`,
and `dhcp_lease_list`; receive accurate data with no write operations performed.

**Tools in scope**: `system_status`, `system_firmware_status`, `system_config_backup`
(contracts/system.md), `interface_list`, `interface_config`, `interface_arp_table`,
`interface_ndp_table` (contracts/interfaces.md), `dhcp_lease_list`, `dhcp_settings_get`,
`dhcp_static_list` (contracts/dhcp.md).

### Tests for User Story 1 (RED — must fail before implementation)

- [ ] T014 [P] [US1] Write failing unit tests for system tools in `tests/unit/tools/test_system.py`: mock `OPNsenseClient.get`, assert `system_status` returns parsed dict from `/api/core/dashboard/get`; assert `system_firmware_status` calls `client.get("/api/firmware/status/check")`; mock `OPNsenseClient.get_text`, assert `system_config_backup` calls `client.get_text("/api/core/backup/download/this")` and returns the raw string (not a dict — this endpoint returns XML); assert `OPNsenseAPIError` from client is surfaced as `ToolError` text
- [ ] T015 [P] [US1] Write failing unit tests for interface tools in `tests/unit/tools/test_interfaces.py`: mock `OPNsenseClient.get`, assert each of `interface_list`, `interface_config`, `interface_arp_table`, `interface_ndp_table` calls the correct OPNsense endpoint and returns the response unchanged
- [ ] T016 [P] [US1] Write failing unit tests for DHCP read tools in `tests/unit/tools/test_dhcp.py`: mock `OPNsenseClient.get`/`.post`, assert `dhcp_lease_list` calls `POST /api/dhcpv4/leases/searchLease` with search payload and returns rows; assert `dhcp_settings_get` calls `GET /api/dhcpv4/settings/get`; assert `dhcp_static_list` calls `GET /api/dhcpv4/settings/searchStaticMap`
- [ ] T017 [P] [US1] Write failing integration tests in `tests/integration/test_system.py`: assert `system_status` returns dict with `versions` key; assert `interface_list` returns non-empty dict; assert `dhcp_lease_list` returns `{"rows": [...], "total": N}` (marked `pytest.mark.integration`, skipped without `OPNSENSE_URL`)

**Checkpoint**: `pytest tests/unit/tools/test_system.py tests/unit/tools/test_interfaces.py tests/unit/tools/test_dhcp.py` — all MUST report FAILED.

### Implementation for User Story 1 (GREEN)

- [ ] T018 [P] [US1] Implement `src/opnsense_mcp/tools/system.py`: async functions `_system_status(client)` and `_system_firmware_status(client)` using `client.get()`; `_system_config_backup(client)` using `client.get_text()` (returns raw XML string — the OPNsense backup endpoint returns `application/xml`, not JSON); `register_tools(mcp: FastMCP, client: OPNsenseClient) -> None` wrapping each as an MCP tool with description from contracts/system.md
- [ ] T019 [P] [US1] Implement `src/opnsense_mcp/tools/interfaces.py`: async functions for `interface_list`, `interface_config`, `interface_arp_table`, `interface_ndp_table` per contracts/interfaces.md; `register_tools()` registering all four
- [ ] T020 [US1] Implement `src/opnsense_mcp/tools/dhcp.py`: async functions for `dhcp_lease_list` (POST with search payload), `dhcp_settings_get`, `dhcp_static_list` per contracts/dhcp.md; `register_tools()` registering all three
- [ ] T021 [US1] Wire US1 domains into `src/opnsense_mcp/server.py`: call `system.register_tools(mcp, client)`, `interfaces.register_tools(mcp, client)`, `dhcp.register_tools(mcp, client)`

**Checkpoint**: `pytest tests/unit/tools/test_system.py tests/unit/tools/test_interfaces.py tests/unit/tools/test_dhcp.py` — all PASS. `mypy --strict src/` zero errors. `ruff check src/` zero errors.

**User Story 1 complete — independently testable**: `uv run opnsense-mcp` in stdio mode, call `system_status` via MCP client, confirm live OPNsense data returned.

---

## Phase 4: User Story 2 — Manage Firewall Rules & Aliases (Priority: P2)

**Goal**: MCP client can list, create, update, delete, and apply firewall rules,
aliases, and NAT rules.

**Independent Test**: Call `firewall_rule_list`, add a test rule, verify it appears,
call `firewall_rule_apply`, delete it, apply again. No dependency on US3/US4.

**Tools in scope**: `firewall_rule_*` (6), `firewall_alias_*` (6), `firewall_nat_*` (5)
per contracts/firewall.md.

### Tests for User Story 2 (RED — must fail before implementation)

- [ ] T022 [P] [US2] Write failing unit tests for firewall tools in `tests/unit/tools/test_firewall.py`: mock `OPNsenseClient.get`/`.post`; test `firewall_rule_list` calls `POST /api/firewall/filter/search_rule`; test `firewall_rule_get` calls `GET /api/firewall/filter/get_rule/{uuid}`; test `firewall_rule_add` calls `POST /api/firewall/filter/add_rule` and returns UUID; test `firewall_rule_update` calls correct endpoint with UUID in path; test `firewall_rule_delete` calls correct endpoint; test `firewall_rule_apply` calls `POST /api/firewall/filter/apply`; repeat same pattern for alias and NAT tools; test 400 validation error is surfaced as `ToolError`
- [ ] T023 [P] [US2] Write failing contract schema tests in `tests/contract/test_tool_schemas.py`: for each tool in contracts/firewall.md, verify the registered MCP tool has matching `name`, `description` (not empty), and `inputSchema` with the required fields from the contract; use `FastMCP.get_tool()` or equivalent introspection

**Checkpoint**: `pytest tests/unit/tools/test_firewall.py tests/contract/test_tool_schemas.py` — all MUST report FAILED.

### Implementation for User Story 2 (GREEN)

- [ ] T024 [US2] Implement firewall rule functions in `src/opnsense_mcp/tools/firewall.py`: `_rule_list`, `_rule_get`, `_rule_add`, `_rule_update`, `_rule_delete`, `_rule_apply` — each calls the OPNsense endpoint from contracts/firewall.md; path parameters (uuid) are interpolated from function arguments
- [ ] T025 [US2] Implement firewall alias functions in `src/opnsense_mcp/tools/firewall.py`: `_alias_list`, `_alias_get_uuid`, `_alias_add`, `_alias_update`, `_alias_delete`, `_alias_apply`
- [ ] T026 [US2] Implement firewall NAT functions in `src/opnsense_mcp/tools/firewall.py`: `_nat_list`, `_nat_add`, `_nat_update`, `_nat_delete`, `_nat_apply`; implement `register_tools(mcp: FastMCP, client: OPNsenseClient) -> None` registering all 17 tools with input schemas matching contracts/firewall.md
- [ ] T027 [US2] Wire firewall domain into `src/opnsense_mcp/server.py`: call `firewall.register_tools(mcp, client)`
- [ ] T028 [P] [US2] Write and run integration test CRUD cycle in `tests/integration/test_firewall.py` (marked `pytest.mark.integration`): `rule_list` → `rule_add` (assert UUID returned) → `rule_list` (assert new rule present) → `rule_apply` → `rule_delete` → `rule_apply`

**Checkpoint**: `pytest tests/unit/tools/test_firewall.py tests/contract/test_tool_schemas.py` — all PASS. `mypy --strict src/` zero errors. `ruff check src/` zero errors.

**User Story 2 complete — independently testable**: firewall CRUD + apply cycle completes without errors against live OPNsense.

---

## Phase 5: User Story 3 — Manage Network Configuration (Priority: P3)

**Goal**: MCP client can manage static routes, DNS host overrides, and core service
lifecycle (start/stop/restart/status).

**Independent Test**: Add a DNS host override, apply, verify, remove, apply again.
Add a static route, apply, remove, apply. Restart Unbound service, verify running.

**Tools in scope**: `route_*` (5 tools, contracts/routes.md), `dns_*` (6 tools,
contracts/dns.md), `service_*` (4 tools, contracts/services.md).

### Tests for User Story 3 (RED — must fail before implementation)

- [ ] T029 [P] [US3] Write failing unit tests for route tools in `tests/unit/tools/test_routes.py`: mock `OPNsenseClient.post`, assert `route_list` calls `POST /api/routes/routes/searchroute`; `route_add` calls `POST /api/routes/routes/addroute` with route payload; `route_update` interpolates UUID in path; `route_delete` calls correct endpoint; `route_apply` calls `POST /api/routes/routes/reconfigure`
- [ ] T030 [P] [US3] Write failing unit tests for DNS tools in `tests/unit/tools/test_dns.py`: assert `dns_settings_get` calls `GET /api/unbound/settings/get`; `dns_host_override_list` calls `GET /api/unbound/settings/searchHostOverride`; `dns_host_override_add` returns UUID; `dns_host_override_update`/`_delete` interpolate UUID; `dns_apply` calls `POST /api/unbound/service/reconfigure`
- [ ] T031 [P] [US3] Write failing unit tests for services tools in `tests/unit/tools/test_services.py`: assert `service_status`/`start`/`stop`/`restart` with `module="unbound"` calls the correct endpoint; assert passing `module="unknown_service"` raises a validation error before any HTTP call is made (FR-003); test all 5 supported module names succeed

**Checkpoint**: `pytest tests/unit/tools/test_routes.py tests/unit/tools/test_dns.py tests/unit/tools/test_services.py` — all MUST report FAILED.

### Implementation for User Story 3 (GREEN)

- [ ] T032 [P] [US3] Implement `src/opnsense_mcp/tools/routes.py`: async functions `_route_list`, `_route_add`, `_route_update`, `_route_delete`, `_route_apply` per contracts/routes.md; `register_tools()` registering all 5 with typed input schemas
- [ ] T033 [P] [US3] Implement `src/opnsense_mcp/tools/dns.py`: async functions `_dns_settings_get`, `_dns_host_override_list`, `_dns_host_override_add`, `_dns_host_override_update`, `_dns_host_override_delete`, `_dns_apply` per contracts/dns.md; `register_tools()` registering all 6
- [ ] T034 [P] [US3] Implement `src/opnsense_mcp/tools/services.py`: `SUPPORTED_MODULES: frozenset[str] = frozenset({"unbound", "dhcpv4", "firmware", "ids", "cron"})`; validate `module` parameter against this set before any HTTP call (raise `ToolError` on unknown module); async functions `_service_status`, `_service_start`, `_service_stop`, `_service_restart` interpolating `module` into path; `register_tools()` registering all 4
- [ ] T035 [US3] Wire routes/DNS/services domains into `src/opnsense_mcp/server.py`: call `routes.register_tools(mcp, client)`, `dns.register_tools(mcp, client)`, `services.register_tools(mcp, client)`
- [ ] T036 [P] [US3] Write and run integration tests in `tests/integration/test_dns.py` and `tests/integration/test_network.py` (marked `pytest.mark.integration`): DNS host override CRUD + apply; route add + apply + delete + apply; service_status for `unbound`

**Checkpoint**: `pytest tests/unit/tools/test_routes.py tests/unit/tools/test_dns.py tests/unit/tools/test_services.py` — all PASS. `mypy --strict src/` zero errors.

**User Story 3 complete — independently testable**: DNS override + route CRUD + service restart all succeed against live OPNsense.

---

## Phase 6: User Story 4 — Secure Server Configuration & Deployment (Priority: P4)

**Goal**: Server starts cleanly with valid credentials; fails fast with clear errors
for all invalid startup conditions; supports both stdio and HTTP/SSE transports.

**Independent Test**: Start with valid creds (success); with missing API key (clear
error); with wrong credentials (401 error); with TLS disabled (warns, succeeds);
start HTTP mode on occupied port (clear port-conflict error).

### Tests for User Story 4 (RED — must fail before implementation)

- [ ] T037 [P] [US4] Write failing unit tests for startup validation in `tests/unit/test_startup.py`: mock `OPNsenseClient.get` to return success → assert server starts; mock to raise `OPNsenseAPIError(status_code=401)` → assert `SystemExit(1)` with message containing "401"; mock `ConnectError` → assert `SystemExit(1)` with message identifying host unreachable; assert startup log records include "Startup complete" or error detail
- [ ] T038 [P] [US4] Write failing unit tests for transport configuration in `tests/unit/test_startup.py` (extend): assert `transport="stdio"` invokes FastMCP stdio run; assert `transport="http"` invokes FastMCP HTTP/SSE run on configured port; assert HTTP startup on already-occupied port raises `SystemExit(1)` with message identifying the port conflict

**Checkpoint**: `pytest tests/unit/test_startup.py` — all MUST report FAILED.

### Implementation for User Story 4 (GREEN)

- [ ] T039 [US4] Enhance `src/opnsense_mcp/__main__.py`: wrap startup in `async def _startup_check(config: Config) -> None` that calls `client.get("/api/core/dashboard/get")` via a temporary `OPNsenseClient`; on `OPNsenseAPIError` exit 1 with `f"Startup failed: OPNsense returned {e.status_code} for {e.path} — {e.body}"`; on connection error exit 1 with host-unreachable message; log "TLS verification disabled — use only on trusted networks" when `verify_tls=False`; log "Startup complete" on success
- [ ] T040 [US4] Implement HTTP/SSE transport binding with port conflict detection in `src/opnsense_mcp/__main__.py`: catch `OSError` with `errno.EADDRINUSE` when starting HTTP server and exit 1 with `f"Port {config.http_port} is already in use — choose a different OPNSENSE_HTTP_PORT"`

**Checkpoint**: `pytest tests/unit/test_startup.py` — all PASS. Validate all 5 startup scenarios from quickstart.md manually.

**User Story 4 complete — independently testable**: all startup scenarios from quickstart.md produce expected outcomes.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Full quality gate pass, complete contract test coverage, and end-to-end
quickstart validation.

- [ ] T041 [P] Extend `tests/contract/test_tool_schemas.py` to cover all 42 tools across all 7 domain contract files (contracts/system.md, firewall.md, interfaces.md, routes.md, dhcp.md, dns.md, services.md): for each tool verify `name`, non-empty `description`, and `inputSchema` required fields match the contract
- [ ] T042 [P] Verify diagnostic logging: add `tests/unit/test_logging.py` asserting that each successful `OPNsenseClient.get`/`.post` call emits a log record containing `method`, `path`, `status_code`, and `outcome=success`; and that failed calls emit `outcome=error` with `error_message`
- [ ] T043 [P] Run full quality gate pass from repository root: `ruff check src/ tests/` (zero errors), `ruff format --check src/ tests/` (zero violations), `mypy --strict src/` (zero errors), `pytest -m "not integration"` (all unit + contract tests green)
- [ ] T044 [P] Run integration test suite against live OPNsense instance: `pytest -m integration -v` — all integration tests in `tests/integration/` pass
- [ ] T045 Validate end-to-end quickstart.md scenarios for all 4 user stories using a live MCP client session (Claude Desktop or Claude Code); document any deviations from expected outcomes in `specs/001-opnsense-mcp-server/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Phase 2 — first independently deliverable increment.
- **User Story 2 (Phase 4)**: Depends on Phase 2 — can start in parallel with US1 after Phase 2.
- **User Story 3 (Phase 5)**: Depends on Phase 2 — can start in parallel with US1/US2 after Phase 2.
- **User Story 4 (Phase 6)**: Depends on Phase 2 + T010/T011 specifically — enhances entry point.
- **Polish (Phase 7)**: Depends on Phases 3–6 all complete.

### Within Each User Story

1. Test tasks MUST be written and confirmed FAILING before implementation.
2. Models → services (inner functions) → tool registration → server wiring.
3. Quality gates (mypy + ruff + pytest) verified at each phase checkpoint.

### Parallel Opportunities

Within Phase 2: T004, T005, T006 can run in parallel (different test files).
Within Phase 3: T014, T015, T016, T017 in parallel; T018, T019 in parallel.
Within Phase 4: T022, T023 in parallel.
Within Phase 5: T029, T030, T031 in parallel; T032, T033, T034 in parallel.
Within Phase 6: T037, T038 in parallel.
Across stories after Phase 2: US2 (Phase 4) and US3 (Phase 5) can proceed in parallel
with US1 (Phase 3) if team capacity allows, since they touch different files.

---

## Parallel Example: User Story 1

```bash
# Launch all test tasks for US1 simultaneously:
Task: "T014 — Write failing tests for system tools in tests/unit/tools/test_system.py"
Task: "T015 — Write failing tests for interface tools in tests/unit/tools/test_interfaces.py"
Task: "T016 — Write failing tests for DHCP read tools in tests/unit/tools/test_dhcp.py"

# After RED checkpoint, launch implementation tasks simultaneously:
Task: "T018 — Implement system tools in src/opnsense_mcp/tools/system.py"
Task: "T019 — Implement interface tools in src/opnsense_mcp/tools/interfaces.py"
# T020 and T021 are sequential (dhcp depends on prior patterns being established)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T013) — CRITICAL, blocks everything
3. Complete Phase 3: User Story 1 (T014–T021)
4. **STOP and VALIDATE**: `uv run opnsense-mcp` → call `system_status` via MCP client
5. If validated: proceed to US2 or deploy MVP

### Incremental Delivery

- Phase 1+2 → Foundation ready
- Phase 3 → US1 (monitoring/read-only) → validate → ship MVP
- Phase 4 → US2 (firewall management) → validate → ship v0.2
- Phase 5 → US3 (network config + services) → validate → ship v0.3
- Phase 6 → US4 (HTTP transport + startup hardening) → validate → ship v1.0
- Phase 7 → Polish → v1.0 production-ready

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
- Each user story phase is independently completable and testable
- Commit after each phase checkpoint, not after every task
- `mypy --strict src/` MUST pass at every phase checkpoint (Principle III)
- `ruff check` MUST pass at every phase checkpoint (Principle II)
- Stop at any checkpoint to validate the story independently before advancing
