# Quickstart: Complete OPNsense API Coverage Validation

Installation, configuration, and running the server are unchanged from
`specs/001-opnsense-mcp-server/quickstart.md` — see that document first. This guide only
covers validating the *new* behavior added by 002: completed domains, the safety layer,
and the six new domains. See `contracts/` for exact tool schemas and `data-model.md` for
type definitions.

**Test environment note**: high-risk operations (`system_reboot`, `system_halt`,
`system_firmware_upgrade`, `system_config_restore`, `interface_assignment_update/delete`)
should only be validated against a disposable OPNsense test VM, never production
hardware — several of them are, by design, irreversible or connectivity-disrupting once
confirmed.

## Running the test suite (unchanged commands, extended coverage)

```bash
uv run pytest -m "not integration" -v      # unit — no OPNsense instance required
uv run pytest -m integration -v            # integration — requires OPNSENSE_* env vars
uv run ruff check . && uv run ruff format --check . && uv run mypy --strict src/
```

---

## Validating User Story 1: Complete Network & Service Configuration Writes

1. Ask: *"Add a DHCP static mapping for MAC aa:bb:cc:dd:ee:ff to 192.168.1.50 on the LAN
   subnet, then apply it."*
   - Expected: `dhcp_static_add` stages the mapping, `dhcp_apply` reconfigures Kea, a
     follow-up `dhcp_static_list` includes the new entry.
2. Ask: *"Disable the ET Open ruleset in IDS."*
   - Expected: `ids_ruleset_toggle` called with the ruleset filename and `enabled=0`;
     `ids_apply` reconfigures Suricata; `ids_ruleset_list` reflects the change.
3. Run `uv run pytest tests/integration/test_dhcp.py tests/integration/test_ids.py -v` —
   all pass against a live instance.

## Validating User Story 2: Confirm High-Risk Operations Before They Execute

This is the representative test for every high-risk tool in the spec — using
`system_reboot` as the example, but the same two-call shape applies to all of them
(`contracts/confirmation.md`).

1. Ask: *"Reboot the firewall"* (or call `system_reboot` directly with no `confirm`).
   - Expected: response is `{"status": "confirmation_required", "confirm_token": "...",
     "description": "...", "expires_in_seconds": 120}`. **Verify via a network capture or
     the server's own diagnostic log that no request reached OPNsense** — the log's most
     recent entry should show `outcome="preview"`, not a call to `core/system/reboot`.
2. Call `system_reboot` again with `confirm=<token from step 1>`.
   - Expected: exactly one `POST core/system/reboot` in the log, `outcome="success"`,
     and the tool returns `{"status": "ok"}`.
3. Call `system_reboot` a third time reusing the same token.
   - Expected: `ToolError` — token already consumed. No request reaches OPNsense.
4. Call `system_reboot` with no `confirm`, wait past `expires_in_seconds`, then confirm
   with the expired token.
   - Expected: `ToolError` — expired. No request reaches OPNsense.
5. `uv run pytest tests/unit/test_confirmation.py -v` — covers all four cases above
   without needing a live instance.

## Validating User Story 3: Manage VPN Tunnels

1. Ask: *"List OpenVPN instances and their status."*
   - Expected: `openvpn_instance_list` + `openvpn_session_list` show configured
     instances and which are actively connected.
2. Ask: *"Add a new WireGuard peer to my <name> server with public key <key>, then apply
   it."*
   - Expected: `wireguard_client_add` stages the peer, `wireguard_apply` reconfigures,
     `wireguard_client_list` includes it, and the returned object has **no private key
     field at all** (WireGuard peers never carry one — see `contracts/wireguard.md`).
   - Then remove it: `wireguard_client_delete` (standard risk, not gated) → `wireguard_apply`.
3. Ask: *"Tear down my IPsec connection named <name>."* (a config-level teardown, not a
   service stop)
   - Expected: `ipsec_connection_delete` returns `confirmation_required` first (VPN
     config teardown is high-risk per FR-007); confirming actually deletes it.
4. `uv run pytest tests/integration/test_vpn.py -v`.

## Validating User Story 4: Manage Web Proxy and Captive Portal

1. Ask: *"Show the current web proxy access control settings."*
   - Expected: `proxy_settings_get` returns the `forward.acl` fields
     (`allowedSubnets`, `blackList`, etc. — there is no separate per-rule list, see
     `contracts/proxy.md`).
2. Ask: *"List active captive portal sessions in zone 1, then disconnect
   <specific session>."*
   - Expected: `captiveportal_session_list` shows sessions; `captiveportal_session_disconnect`
     removes the one named session directly, no confirmation required (FR-015).
3. Ask: *"Disconnect everyone in captive portal zone 1."*
   - Expected: `captiveportal_session_disconnect_zone` returns `confirmation_required`
     with a preview listing how many sessions would be dropped; confirming disconnects
     all of them and reports per-session success/failure.
4. `uv run pytest tests/integration/test_proxy.py tests/integration/test_captiveportal.py -v`.

## Validating User Story 5: Manage Certificates and PKI

1. Ask: *"List all certificate authorities and certificates."*
   - Expected: `trust_ca_list` / `trust_certificate_list` return metadata with `prv`
     (private key) fields absent from every entry, even for certs that have a persisted
     key server-side.
2. Ask: *"Import this certificate and private key: <PEM>."* with
   `private_key_location=local`.
   - Expected: `trust_certificate_add`'s response includes the key **once**, as
     `private_key` — this is the documented one-shot exception, not a redaction bug. A
     subsequent `trust_certificate_get` on the same cert does **not** include it.
3. Ask: *"Revoke certificate <name>."*
   - Expected: `trust_certificate_revoke` returns `confirmation_required` first; confirming
     performs the CRL read-modify-write and a follow-up `trust_crl_get` shows the cert's
     `refid` under the requested `revoked_reason_N`.
4. `uv run pytest tests/integration/test_trust.py -v`.

## Validating User Story 6: Perform High-Risk System Operations

Run each against a disposable test VM only:

1. `system_reboot` / `system_halt` — same two-call pattern as User Story 2's example.
2. `system_config_restore` — preview should show a diff summary (from `core/backup/diff`)
   before confirming; confirm and verify the box reverts to the selected revision.
3. `system_firmware_update` (or `_upgrade`) — preview shows the pending version; confirm
   and poll `system_firmware_upgrade_status` until it completes.
4. `interface_assignment_update` — preview names the interface and warns about possible
   session disconnection; confirm and verify via `interface_assignment_list`.
5. `uv run pytest tests/integration/test_system.py -v` (high-risk subset — run this file
   only against the disposable VM, never CI-against-production).
