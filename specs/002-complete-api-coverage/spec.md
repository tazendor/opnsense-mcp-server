# Feature Specification: Complete OPNsense API Coverage (Read-Write)

**Feature Branch**: `002-complete-api-coverage`

**Created**: 2026-07-31

**Status**: Draft

**Input**: User description: "Expand the OPNsense MCP server to cover the complete
documented OPNsense REST API surface, read-write, superseding the scope boundary set
in 001-opnsense-mcp-server. Complete the domains already partially covered (System,
DHCP, Interfaces, IDS, Services). Add entirely new domains not covered at all today
(VPN: OpenVPN/IPsec/WireGuard; Web Proxy; Captive Portal; Certificate/PKI management),
full read-write. Any operation that is destructive or high-blast-radius at the box or
network level must go through an explicit safety layer in the MCP server itself,
beyond whatever validation OPNsense performs — a deliberate change from 001's
no-extra-gate assumption, narrowed to non-destructive writes only."

## Clarifications

### Session 2026-07-31

- Q: OPNsense's certificate and VPN peer/client endpoints can return private key
  material (certificate private keys, WireGuard/OpenVPN peer private keys) when
  documented as part of the object. Should the server expose that material through
  its read tools? → A: No — redact private key fields from all read responses.
  Write/import tools still accept a key to install it, but no tool ever returns one.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete Network & Service Configuration Writes (Priority: P1)

A network administrator uses an AI assistant to make the same kind of configuration
changes to DHCP, IDS, and non-destructive system settings that 001 already allows for
firewall rules, DNS, and routes. Today these domains are read-only even though
OPNsense's documented API supports writing to them. The assistant proposes a change
(e.g., a new DHCP static mapping, toggling an IDS ruleset), the administrator approves,
and the server applies it using the same staged-then-apply pattern already validated
in 001.

**Why this priority**: These domains reuse a pattern (stage → apply) already proven
safe and useful in 001. Extending it to the remaining low-risk domains is the highest
value-to-risk work and requires no new safety mechanism.

**Independent Test**: List DHCP static mappings, add one, verify it appears, remove it.
Toggle an IDS ruleset's enabled state and verify the change is reflected in a
subsequent list call. No dependency on any other story in this spec.

**Acceptance Scenarios**:

1. **Given** an MCP client requests the current DHCPv4 static mappings, **When** it
   submits a new mapping matching the OPNsense API schema, **Then** the server stages
   it, and applying the pending DHCP changes confirms success and a subsequent list
   includes the new mapping.
2. **Given** an MCP client submits an update to DHCPv4 service settings, **When** the
   server applies it, **Then** OPNsense confirms the change and the updated settings
   are reflected in a subsequent read.
3. **Given** an MCP client requests the list of IDS/IPS rulesets, **When** it toggles
   a ruleset's enabled/disabled state and applies the change, **Then** a subsequent
   list reflects the new state.
4. **Given** the server's own module list for the Services domain has drifted from
   what the current OPNsense stable release actually exposes, **When** this story is
   implemented, **Then** the supported module list is reconciled against the current
   stable release and documented accurately.
5. **Given** an existing tool has no corresponding contract document (the IDS ruleset
   listing tool shipped without one), **When** this story is implemented, **Then** a
   contract document is written for it before any new IDS capability is added.

---

### User Story 2 - Confirm High-Risk Operations Before They Execute (Priority: P2)

A network administrator asks an AI assistant to perform an operation that could
disrupt connectivity to the firewall itself or to the network it protects — for
example, rebooting the box, restoring a full configuration backup, or disabling the
interface the administrator is currently connected through. Before anything happens,
the assistant receives a clear, specific description of what the operation will do and
must explicitly confirm before the server carries it out.

**Why this priority**: Every high-risk capability added later in this spec (system
reboot, config restore, interface reassignment, VPN teardown, certificate revocation,
captive portal mass-disconnect) depends on this mechanism existing first. It is the
one new piece of behavior in this spec that is not simply "proxy another documented
endpoint" — it is server-side safety logic — so it must be built and validated before
anything relies on it.

**Independent Test**: Using any single high-risk tool (e.g., system reboot) as the
representative case: call it without confirmation and verify OPNsense is not
contacted and a preview of the action is returned instead; call it again with the
confirmation step completed and verify the operation executes exactly once.

**Acceptance Scenarios**:

1. **Given** an MCP client calls a high-risk tool without confirming, **When** the
   server processes the call, **Then** no request is sent to OPNsense, and the client
   receives a description of exactly what the operation would do plus what is needed
   to confirm it.
2. **Given** an MCP client completes the confirmation step for a specific pending
   high-risk operation, **When** it resubmits with confirmation, **Then** the server
   sends the corresponding request to OPNsense exactly once and returns the result.
3. **Given** a confirmation was issued for one specific operation, **When** a client
   attempts to reuse it for a different operation or after it has expired, **Then**
   the server rejects the attempt and requires a fresh confirmation.
4. **Given** any high-risk operation is confirmed and executed, **When** the operator
   reviews the diagnostic log, **Then** both the preview step and the confirmed
   execution step appear as distinct, timestamped records.

---

### User Story 3 - Manage VPN Tunnels (Priority: P3)

A network administrator uses an AI assistant to inspect and manage VPN connectivity —
OpenVPN server/client instances, IPsec tunnels, and WireGuard instances — including
status, start/stop, and peer/client configuration, without needing the OPNsense web UI.

**Why this priority**: VPN is a major, frequently-used OPNsense capability entirely
absent today. It ranks above Proxy/Captive Portal/Certificates because tunnel
visibility and control (is the tunnel up, restart it, add a peer) is the most common
operational need administrators have for VPN.

**Independent Test**: List configured OpenVPN instances and their status; start a
stopped instance and confirm its status changes; add a WireGuard peer, verify it
appears in a subsequent list, then remove it.

**Acceptance Scenarios**:

1. **Given** an MCP client requests OpenVPN instance status, **When** the server
   queries OPNsense, **Then** all configured instances and their running/stopped
   state are returned as OPNsense reports them.
2. **Given** an MCP client submits a new WireGuard peer or IPsec phase 2 entry
   matching the OPNsense API schema, **When** the server applies it, **Then**
   OPNsense confirms creation and a subsequent list includes the new entry.
3. **Given** an MCP client requests an OpenVPN, IPsec, or WireGuard service be
   stopped or the tunnel torn down, **When** this is a service-level start/restart
   (not a teardown/disable of the underlying configuration), **Then** it proceeds
   directly like other service controls in this server; a configuration-level
   teardown/disable instead goes through the confirm-then-execute mechanism from
   User Story 2.

---

### User Story 4 - Manage Web Proxy and Captive Portal (Priority: P4)

A network administrator uses an AI assistant to inspect and configure the Squid web
proxy (access control, cache settings) and Captive Portal (zones, allowed hosts,
active sessions), including disconnecting sessions when needed.

**Why this priority**: These are widely used but more specialized than VPN or core
network domains — most OPNsense deployments use them situationally rather than as a
baseline requirement.

**Independent Test**: List proxy configuration and captive portal zones; add a proxy
access rule and verify it appears; list active captive portal sessions and
disconnect one (single-session disconnect proceeds directly; a mass-disconnect of an
entire zone routes through User Story 2's confirmation mechanism).

**Acceptance Scenarios**:

1. **Given** an MCP client requests the current web proxy configuration, **When** it
   submits a new access control rule matching the OPNsense API schema, **Then** the
   server applies it and a subsequent read reflects the change.
2. **Given** an MCP client requests active captive portal sessions for a zone,
   **When** the server queries OPNsense, **Then** all currently connected clients are
   returned as OPNsense reports them.
3. **Given** an MCP client requests a single captive portal session be disconnected,
   **When** the server processes the request, **Then** it proceeds directly and
   confirms the session was removed.
4. **Given** an MCP client requests all sessions in a zone be disconnected at once,
   **When** the server processes the request, **Then** it is treated as a high-risk
   operation per User Story 2 and requires confirmation first.

---

### User Story 5 - Manage Certificates and PKI (Priority: P5)

A network administrator uses an AI assistant to inspect certificate authorities and
certificates used by OPNsense services (web UI, VPN, captive portal), import or issue
new certificates, and revoke ones that are no longer trusted.

**Why this priority**: Certificate management is powerful but the least frequently
exercised of the new domains day-to-day, and revocation/reissuance carries meaningful
trust implications, so it is scoped last.

**Independent Test**: List configured certificate authorities and certificates; import
a certificate and verify it appears in a subsequent list; revoke a certificate and
verify its status changes (revocation routes through User Story 2's confirmation
mechanism as a trust-impacting, hard-to-reverse action).

**Acceptance Scenarios**:

1. **Given** an MCP client requests the list of configured certificate authorities and
   certificates, **When** the server queries OPNsense, **Then** all entries are
   returned with their metadata (subject, issuer, validity dates, purpose) as
   OPNsense reports them.
2. **Given** an MCP client submits a new certificate or CA for import matching the
   OPNsense API schema, **When** the server applies it, **Then** OPNsense confirms
   creation and a subsequent list includes the new entry.
3. **Given** an MCP client requests a certificate be revoked, **When** the server
   processes the request, **Then** it requires confirmation per User Story 2 before
   sending the revocation to OPNsense.

---

### User Story 6 - Perform High-Risk System Operations (Priority: P6)

A network administrator uses an AI assistant to perform system-level operations that
can disrupt the firewall itself: rebooting or halting the device, restoring a full
configuration backup, triggering a firmware upgrade, and reassigning or disabling a
network interface.

**Why this priority**: These are the highest blast-radius operations in the entire
API surface — a mistake can make the firewall (and the network behind it)
unreachable. They are scoped last and depend entirely on User Story 2's
confirm-then-execute mechanism being in place first.

**Independent Test**: Request a system reboot; verify the server returns a preview
and does not contact OPNsense until confirmed; confirm it and verify the reboot
request is sent exactly once. Equivalent tests apply to halt, config restore,
firmware upgrade, and interface reassignment/disable.

**Acceptance Scenarios**:

1. **Given** an MCP client requests a system reboot or halt, **When** it has not yet
   confirmed, **Then** no reboot/halt request reaches OPNsense; once confirmed, the
   server sends exactly one request and surfaces OPNsense's response.
2. **Given** an MCP client submits a full configuration restore (an XML document),
   **When** it has not yet confirmed, **Then** the server describes what will be
   overwritten without submitting it; once confirmed, it submits the restore and
   surfaces the result.
3. **Given** an MCP client requests a firmware upgrade be triggered, **When** it has
   not yet confirmed, **Then** the server reports the pending version change without
   starting it; once confirmed, it starts the upgrade and surfaces OPNsense's
   response.
4. **Given** an MCP client requests an interface be reassigned or disabled, **When**
   it has not yet confirmed, **Then** the server describes the change (including
   that it may disconnect the current management session) without applying it; once
   confirmed, it applies the change and surfaces the result.

---

### Edge Cases

- What happens when a confirmation step is issued but the underlying OPNsense state
  changes before the client confirms (e.g., someone else already rebooted the box)?
  The server MUST attempt the confirmed operation and surface whatever error OPNsense
  returns, rather than assuming the preview is still accurate.
- What happens when an MCP client disconnects between the preview and confirmation
  steps of a high-risk operation? The pending confirmation MUST expire on its own
  after a bounded time rather than remaining valid indefinitely.
- What happens when a VPN, proxy, or captive portal endpoint documented in the
  OPNsense API is provided by a plugin that is not installed on the target instance?
  The server MUST surface OPNsense's own "not found"/"not installed" error rather
  than inventing a different explanation.
- What happens when a certificate or VPN peer object is read back after import?
  The server MUST redact any private key field from the response per FR-017, even
  though the underlying OPNsense endpoint includes it.
- What happens when an interface reassignment tool is confirmed and executed, and it
  happens to disable the interface the MCP client itself is connected through? The
  server MUST still attempt the operation and report whatever result or error
  OPNsense returns; the server cannot know before the fact which interface carries
  its own management traffic.

## Requirements *(mandatory)*

### Functional Requirements

**Scope and traceability (extends 001's FR-002/FR-006)**

- **FR-001**: The server MUST expose every documented OPNsense REST API endpoint
  across the System, Firewall, Interfaces, Routes, DHCP, DNS Resolver, Services, IDS,
  VPN (OpenVPN, IPsec, WireGuard), Web Proxy, Captive Portal, and Certificate/PKI
  domains as a discrete MCP tool, superseding 001's domain boundary.
- **FR-002**: Every MCP tool, including ones that already ship without one, MUST have
  a corresponding contract document tying it to a specific OPNsense REST API
  endpoint. No tool may exist without a contract.
- **FR-003**: The server MUST NOT implement behavior not documented in the OPNsense
  REST API for the current stable release; this applies equally to the newly added
  domains.

**Completing existing domains (User Story 1)**

- **FR-004**: The server MUST support creating, updating, deleting, and applying
  DHCPv4 static mappings, and reading/writing DHCPv4 service settings.
- **FR-005**: The server MUST support enabling and disabling individual IDS/IPS
  rulesets (and rules, if individually addressable in the current stable API).
- **FR-006**: The server's declared set of controllable service modules MUST match
  what the current OPNsense stable release actually exposes; this MUST be
  re-verified as part of implementation rather than carried over from prior
  documentation.

**Safety layer (User Story 2)**

- **FR-007**: The server MUST classify each write operation as either standard
  (proceeds directly, matching 001's existing stage-then-apply behavior) or
  high-risk (requires confirmation). High-risk operations are, at minimum: system
  reboot/halt, firmware upgrade, full configuration restore, interface reassignment
  or disable, VPN configuration teardown/disable, certificate revocation, and
  bulk/zone-wide captive portal disconnect.
- **FR-008**: For a high-risk operation, the server MUST NOT send the corresponding
  request to OPNsense until the MCP client has completed a distinct confirmation
  step for that specific operation.
- **FR-009**: The server MUST describe, in the unconfirmed response, what the
  operation will do in terms an operator can evaluate before confirming.
- **FR-010**: A confirmation MUST be single-use, scoped to the specific operation it
  was issued for, and MUST expire after a bounded time if unused.
- **FR-011**: Both the preview step and the confirmed execution step of a high-risk
  operation MUST produce their own diagnostic record, consistent with 001's
  per-call logging requirement.

**New domains (User Stories 3-5)**

- **FR-012**: The server MUST support reading status and configuration, and
  starting/stopping/restarting, for OpenVPN, IPsec, and WireGuard, per the current
  stable OPNsense API.
- **FR-013**: The server MUST support creating, updating, deleting, and applying VPN
  peer/client/phase-2 entries (as applicable per VPN type) via the same
  stage-then-apply pattern used elsewhere in the server.
- **FR-014**: The server MUST support reading and writing Web Proxy (Squid)
  configuration, including access control rules, per the current stable OPNsense
  API.
- **FR-015**: The server MUST support reading Captive Portal zone configuration and
  active sessions, disconnecting an individual session directly, and disconnecting
  all sessions in a zone only through the confirmation mechanism (FR-008).
- **FR-016**: The server MUST support reading certificate authorities and
  certificates (metadata at minimum), importing or issuing new ones, and revoking
  existing ones only through the confirmation mechanism (FR-008).
- **FR-017**: The server MUST redact private key material from every read response
  for certificates and VPN peer/client entries, even when the underlying OPNsense
  endpoint includes it. Write/import tools MAY still accept a private key as input
  in order to install it; no tool may return one.

**High-risk system operations (User Story 6)**

- **FR-018**: The server MUST support system reboot and halt, full configuration
  restore, firmware upgrade triggering, and interface reassignment/disable, each
  gated by the confirmation mechanism (FR-008).

### Key Entities

- **Pending Operation / Confirmation**: A server-held record representing one
  requested high-risk operation awaiting confirmation — what it will do, which tool
  and parameters it corresponds to, and when it expires. Never persisted beyond the
  server process's own lifetime.
- **VPN Instance**: An OpenVPN, IPsec, or WireGuard tunnel/service as configured on
  OPNsense, including its running/stopped status.
- **VPN Peer/Client Entry**: A single client or peer configuration attached to a VPN
  instance (WireGuard peer, OpenVPN client-specific override, IPsec phase 2 entry).
- **Proxy Configuration**: Web Proxy (Squid) settings and access control rules.
- **Captive Portal Zone**: A captive portal configuration domain, containing active
  client sessions.
- **Certificate / Certificate Authority**: A PKI object with subject, issuer,
  validity period, and purpose, optionally including private key material subject to
  FR-017.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every domain listed in FR-001 has full read-write MCP tool coverage
  for its documented OPNsense REST API endpoints; no documented endpoint in those
  domains is missing a corresponding tool.
- **SC-002**: 100% of MCP tools in the server, including those that predate this
  spec, have a corresponding contract document; zero tools are undocumented.
- **SC-003**: In testing, 100% of high-risk operations (per FR-007's list) are
  rejected without contacting OPNsense when attempted without prior confirmation.
- **SC-004**: In testing, a confirmed high-risk operation results in exactly one
  corresponding request to OPNsense — never zero, never more than one.
- **SC-005**: An operator can review a complete record of every preview and
  every confirmed execution of a high-risk operation, distinguishable from each
  other, without accessing the MCP client's own session history.
- **SC-006**: An MCP client can complete the end-to-end workflow (query, modify,
  apply, verify) for each new domain's primary use case without encountering
  unhandled errors or undocumented behavior.

## Assumptions

- This spec supersedes the scope exclusions in 001-opnsense-mcp-server for: DHCP
  writes, Interface assignment/enable-disable, IDS ruleset writes, VPN, Web Proxy,
  Captive Portal, and Certificate/PKI. All other assumptions and requirements from
  001 (HTTPS-only, API key/secret auth, no caching, dual transport, per-call
  logging, current-stable-release targeting) continue to apply.
- "Documented OPNsense REST API" includes the officially maintained plugins bundled
  with a standard OPNsense installation (OpenVPN, IPsec/strongSwan, WireGuard, Squid
  proxy, Captive Portal) — the same standard already applied when 001's IDS support
  was verified against the current stable release and adjusted when a documented
  endpoint turned out not to exist in the base install.
- The confirmation mechanism from User Story 2 is in-memory / process-local; it does
  not require persistent storage, and confirmations do not survive a server restart.
- Service-level start/stop/restart of VPN services (the daemon itself) is treated as
  standard risk, matching existing Services domain behavior; only configuration-level
  teardown/disable and the other operations named in FR-007 are treated as high-risk.
- DHCPv6, multi-tenant/cloud-hosted deployment, and session/OAuth-based OPNsense
  authentication remain out of scope, unchanged from 001.
