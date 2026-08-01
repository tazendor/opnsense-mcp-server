# MCP Tool Contracts: Services Domain (supersedes 001's contract)

Tools in this domain control the start, stop, restart, and status of core OPNsense
services via the generic `{module}/service/{action}` pattern. The `module` parameter
identifies the service using its OPNsense API module name.

**Reconciliation (FR-006)**: 001's contract doc listed
`{unbound, dhcpv4, firmware, ids, cron}` — none of `dhcpv4`, `firmware`, `cron` match a
real `{module}/service/*` triple (dhcp service control is under `kea`, not `dhcpv4`;
firmware/cron have no analogous start/stop/restart lifecycle to control this way). The
actual shipped `SUPPORTED_MODULES` is `{unbound, kea, ids}`. 002 corrects the documented
list to match shipped reality and extends it with the new VPN/proxy/captive-portal
domains, each of which has its own standard `Service` controller
(`start`/`stop`/`restart`/`reconfigure`/`status`) matching this same shape.

**Supported modules** (current, corrected + extended):

| `module` value | Service |
|---|---|
| `unbound` | DNS Resolver (Unbound) |
| `kea` | DHCPv4 server (Kea) |
| `ids` | Intrusion Detection System (Suricata) |
| `openvpn` | OpenVPN |
| `ipsec` | IPsec (strongSwan) |
| `wireguard` | WireGuard |
| `proxy` | Web Proxy (Squid) |
| `captiveportal` | Captive Portal |

Calling a tool with a `module` value not in this list returns a validation error before
any request is sent to OPNsense (FR-003), unchanged from 001's behavior.

All start/stop/restart/status calls are standard risk (spec Assumptions: service-level
lifecycle control, as distinct from configuration-level teardown/disable, which is
high-risk per-domain — see each domain's own contract).

---

## Tool: `service_status` / `service_start` / `service_stop` / `service_restart`

**Unchanged from 001** except for the `module` enum above.

**OPNsense endpoints**: `GET /api/{module}/service/status`,
`POST /api/{module}/service/{start|stop|restart}`.
