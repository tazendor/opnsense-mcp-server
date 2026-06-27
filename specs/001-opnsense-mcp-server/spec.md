# Feature Specification: OPNsense MCP Server

**Feature Branch**: `001-opnsense-mcp-server`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "Create a production-quality Python MCP server that faithfully
implements the documented OPNsense REST API using typed, test-driven, idiomatic Python,
exposing only documented functionality with secure authentication, robust error handling,
and no undocumented assumptions or invented behavior."

## Clarifications

### Session 2026-06-27

- Q: Which OPNsense major version(s) should the server target? → A: No version pin — the server always targets the current OPNsense stable release; tests run against the stable version current at the time of testing.
- Q: Which MCP transport mechanism(s) should the server support? → A: Both stdio and HTTP/SSE — stdio for local subprocess clients; HTTP/SSE for remote or multi-client scenarios.
- Q: What timeout structure should govern individual OPNsense API calls? → A: Separate configurable connection timeout and read timeout, each with a sensible default; both operator-overridable without code changes.
- Q: What level of diagnostic visibility must the server provide to the operator? → A: Every OPNsense API call and its outcome (success or error) must be recorded; errors and startup events must also be included.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query Firewall & System Status (Priority: P1)

A network administrator uses an AI assistant to check the current health and
operational status of an OPNsense firewall. The assistant queries live data —
interface states, active firewall states, ARP/DHCP leases, gateway status, and
firmware version — through the MCP server, without needing to log into the
firewall UI or know the REST API directly.

**Why this priority**: Read-only monitoring is the safest, most universally
useful capability. It delivers immediate value with no risk of misconfiguration
and validates end-to-end connectivity.

**Independent Test**: Can be fully tested by connecting an MCP client to the
server and requesting system status, gateway status, and interface information.
Returns accurate, current data from the firewall with no write operations
performed.

**Acceptance Scenarios**:

1. **Given** the MCP server is running and connected to an OPNsense instance,
   **When** an MCP client requests system status,
   **Then** the server returns the current firmware version, uptime, CPU load,
   and memory usage as reported by OPNsense.

2. **Given** the MCP server is configured with valid credentials,
   **When** an MCP client requests interface status,
   **Then** the server returns the status, IP address, and link state for each
   network interface on the OPNsense instance.

3. **Given** the OPNsense API returns an error (e.g., connection refused,
   invalid endpoint),
   **When** the MCP client makes any status request,
   **Then** the server surfaces the specific error to the client with enough
   context to diagnose the problem — no generic failures, no silent swallowing.

---

### User Story 2 - Manage Firewall Rules & Aliases (Priority: P2)

A network administrator uses an AI assistant to create, modify, and delete
firewall rules and aliases on OPNsense. The assistant proposes changes, the
administrator approves them, and the MCP server applies them. After any change,
the assistant can confirm the change took effect by re-querying the state.

**Why this priority**: Firewall rule management is the highest-value operational
use case for OPNsense automation. The read-then-write pattern (Story 1 first)
ensures the AI assistant has full context before proposing changes.

**Independent Test**: Can be fully tested by using an MCP client to list
existing firewall rules, add a test rule, verify it appears in the list, and
then delete it. No dependency on Story 3 or later stories.

**Acceptance Scenarios**:

1. **Given** an MCP client requests the list of firewall rules,
   **When** the server queries OPNsense,
   **Then** all currently configured rules are returned in the structure
   OPNsense defines, without modification or filtering.

2. **Given** an MCP client submits a new firewall rule matching the OPNsense
   API schema,
   **When** the server applies the rule,
   **Then** OPNsense confirms creation, and a subsequent list request includes
   the new rule.

3. **Given** an MCP client submits a rule with an invalid field value,
   **When** the server attempts to apply it,
   **Then** OPNsense's validation error is returned to the client with the
   exact field and reason, before any state change occurs.

4. **Given** a rule has been created or modified,
   **When** the MCP client requests the changes to be applied (reconfigure),
   **Then** OPNsense applies the pending changes and confirms success.

---

### User Story 3 - Manage Network Configuration (Priority: P3)

A network administrator uses an AI assistant to inspect and update network
configuration: DHCP server settings, DNS resolver configuration, static routes,
and interface assignments. The assistant queries current state, proposes updates
matching OPNsense's documented API schema, and applies approved changes.

**Why this priority**: Network configuration changes are more impactful than
firewall rules, so they build on the validated pattern from Stories 1 and 2.
DHCP/DNS errors can disrupt the network, so this story is lower priority than
basic firewall management.

**Independent Test**: Can be fully tested by querying DHCP leases, updating a
DNS host override, verifying it appears in DNS resolution, then removing it.

**Acceptance Scenarios**:

1. **Given** an MCP client requests DHCP leases,
   **When** the server queries OPNsense,
   **Then** all active and static leases are returned as OPNsense reports them.

2. **Given** an MCP client submits a DNS host override matching the OPNsense
   API schema,
   **When** the server applies it and reconfigures the DNS service,
   **Then** OPNsense confirms success and the override is resolvable.

3. **Given** an MCP client requests static routes,
   **When** the server queries OPNsense,
   **Then** all routes are returned and subsequent additions/deletions succeed
   or fail according to OPNsense's response.

---

### User Story 4 - Secure Server Configuration & Deployment (Priority: P4)

A system administrator installs and configures the MCP server. They provide
the OPNsense instance URL and API credentials through a configuration file or
environment variables. The server validates connectivity and credential validity
on startup, refusing to start (with a clear error) if credentials are missing
or the OPNsense instance is unreachable.

**Why this priority**: Configuration is a prerequisite for all other stories,
but it is scoped last here because Stories 1–3 can be validated against a
pre-configured environment.

**Independent Test**: Can be fully tested by starting the server with valid
credentials (verifies startup and connectivity), then starting it with missing
or wrong credentials (verifies rejection with a clear error message).

**Acceptance Scenarios**:

1. **Given** valid OPNsense API credentials and a reachable OPNsense instance
   are configured,
   **When** the MCP server starts in stdio mode (launched as a subprocess),
   **Then** the server successfully initialises and is ready to accept MCP
   client connections over stdio.

2. **Given** valid credentials and a configurable HTTP port are provided,
   **When** the MCP server starts in HTTP/SSE mode,
   **Then** the server binds to the configured port and is ready to accept
   MCP client connections over HTTP/SSE; a different port can be specified
   to avoid conflicts.

3. **Given** credentials are missing or invalid,
   **When** the MCP server starts in either transport mode,
   **Then** the server exits with a clear, human-readable error identifying
   what is missing or wrong (missing key, wrong secret, unreachable host).

4. **Given** the OPNsense instance uses a self-signed TLS certificate,
   **When** the MCP server is configured to allow it,
   **Then** connections succeed; when not configured to allow it, connections
   are rejected with a clear certificate validation error.

---

### Edge Cases

- What happens when the OPNsense instance becomes unreachable mid-session?
  The server MUST surface a connection error to the MCP client, not hang or
  return stale data.
- What happens when an OPNsense API endpoint returns a 500 error?
  The server MUST propagate the error with the OPNsense response body so the
  client can diagnose the issue.
- What happens when the MCP client sends a tool call with extra or missing
  parameters?
  The server MUST reject the call with a descriptive validation error before
  forwarding anything to OPNsense.
- What happens when OPNsense is upgrading firmware and some endpoints are
  unavailable?
  The server MUST return the HTTP error from OPNsense rather than inventing an
  explanation.
- What happens when the API key has insufficient privileges for a requested
  operation?
  The server MUST return OPNsense's 403 response with context, not a generic
  "permission denied".
- What happens when the configured HTTP/SSE port is already in use?
  The server MUST fail at startup with a clear error identifying the port
  conflict, rather than binding to an arbitrary fallback port silently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The server MUST authenticate all OPNsense API calls using
  API key/secret credentials supplied at configuration time.
- **FR-002**: The server MUST expose each documented OPNsense REST API
  endpoint as a discrete MCP tool, with tool names and parameters derived
  directly from the official OPNsense REST API documentation for the current
  stable release at the time of implementation.
- **FR-003**: The server MUST validate MCP client inputs against the
  expected OPNsense API schema before forwarding any request to OPNsense.
- **FR-004**: The server MUST return OPNsense API responses to the MCP client
  in a structured, machine-readable format, preserving the response structure
  OPNsense defines.
- **FR-005**: The server MUST surface all OPNsense API errors — including HTTP
  status codes, error messages, and validation failures — to the MCP client
  with sufficient context for diagnosis.
- **FR-006**: The server MUST NOT implement any behavior not documented in the
  OPNsense REST API documentation; invented endpoints, inferred defaults beyond
  what OPNsense specifies, and undocumented fields are prohibited.
- **FR-007**: The server MUST connect to OPNsense via HTTPS; unencrypted HTTP
  is not permitted.
- **FR-008**: The server MUST apply two independently configurable timeouts to
  every OPNsense API call: a connection timeout (how long to wait for the TCP
  connection to be established) and a read timeout (how long to wait for the
  full response after connection). Both MUST have documented defaults and MUST
  be overridable by the operator without modifying source code. When either
  timeout expires, the server MUST return a clear timeout error to the MCP
  client identifying which timeout was exceeded; the server MUST NOT hang.
- **FR-009**: OPNsense credentials (API key, API secret, instance URL) MUST be
  configurable without modifying the server's source code (via environment
  variables or a configuration file).
- **FR-010**: The server MUST support OPNsense instances using self-signed TLS
  certificates, with TLS verification behaviour configurable by the operator.
- **FR-011**: The server MUST cover the following OPNsense API domains at
  minimum: System (status, firmware, configuration backup), Firewall (rules,
  aliases, NAT), Interfaces, Routes, DHCP, DNS Resolver, and Services (start/
  stop/restart).
- **FR-012**: The server MUST support the MCP stdio transport, allowing MCP
  clients (e.g., Claude Desktop, Claude Code) to launch it as a subprocess
  and communicate over standard input/output.
- **FR-013**: The server MUST support the MCP HTTP/SSE transport, binding to
  a configurable local port to accept connections from remote or multiple MCP
  clients. The active transport is selected at startup via configuration.
- **FR-014**: The server MUST produce a diagnostic record for every OPNsense
  API call it makes, capturing at minimum: the operation requested, the
  OPNsense endpoint invoked, and the outcome (success or the error status and
  message). Startup and shutdown events, credential validation results, and
  all OPNsense error responses MUST also be recorded. Diagnostic output MUST
  be accessible to the operator without modifying source code.

### Key Entities

- **MCP Tool**: A discrete, callable capability the server exposes to MCP
  clients, corresponding to a single OPNsense API operation.
- **OPNsense Instance**: The target firewall/router device, accessed exclusively
  via its documented REST API.
- **API Credential**: The API key and secret pair used to authenticate with
  OPNsense, plus the instance base URL.
- **Tool Request**: An MCP client's invocation of a tool, including parameters.
- **Tool Response**: The server's reply to the MCP client, containing either
  OPNsense's response data or a structured error.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All documented OPNsense REST API endpoints listed in FR-011 have
  corresponding MCP tools; no documented endpoint in those domains is missing.
- **SC-002**: An MCP client can complete the end-to-end workflow for each User
  Story (query, modify, apply, verify) without encountering unhandled errors or
  undocumented behaviour.
- **SC-003**: Every OPNsense API error condition (400, 403, 404, 500, timeout)
  is surfaced to the MCP client with the original OPNsense error payload; zero
  error types are silently swallowed or replaced with a generic message.
- **SC-004**: The server starts successfully within 5 seconds when given valid
  credentials pointing to a reachable OPNsense instance, or fails within 10
  seconds with a human-readable error when credentials are invalid or the
  instance is unreachable.
- **SC-005**: No tool, parameter, or behaviour exists in the server that is not
  traceable to a specific page or section of the OPNsense REST API
  documentation; the specification and implementation are verifiable against
  documentation.
- **SC-006**: When the OPNsense instance is unreachable, every API call made
  through the server returns a timeout error to the MCP client within the
  configured connection timeout period; no call blocks longer than the
  configured read timeout.
- **SC-007**: After any sequence of tool calls, an operator can review a
  complete record of every OPNsense API request made and its outcome, without
  accessing the MCP client's own session history or OPNsense's internal logs.

## Assumptions

- OPNsense instances expose their REST API on the standard HTTPS port (443)
  unless configured otherwise; the operator provides the full base URL.
- API key/secret authentication is sufficient; session-based (cookie) or OAuth
  authentication is out of scope.
- The server supports two deployment modes: (a) stdio — launched as a local
  subprocess by the MCP client; (b) HTTP/SSE — bound to a configurable port,
  accessible by local or network-adjacent MCP clients. Multi-tenant and
  cloud-hosted deployments are out of scope for v1.
- The server targets the current OPNsense stable release without version
  pinning. The implementation and its acceptance tests are validated against
  whichever stable release is current at the time of testing. Compatibility
  with older or future releases is out of scope. All endpoint references in
  this specification are resolved against the official OPNsense REST API
  documentation for the current stable release.
- Write operations (create, update, delete, reconfigure) are permitted; the MCP
  client and its human operator are responsible for reviewing proposed changes
  before submitting them. The server does not implement an additional approval
  gate beyond what OPNsense itself requires.
- VPN configuration (OpenVPN, IPsec, WireGuard) and advanced services (web
  proxy, captive portal, IDS) are out of scope for v1; the priority domains are
  those listed in FR-011.
- The server does not need to cache OPNsense responses; all data returned to the
  MCP client reflects the live state of OPNsense at the time of the request.
