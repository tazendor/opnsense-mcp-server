# MCP Server Tools

Full inventory of tools exposed by this MCP server, grouped by subsystem, with each
tool's access type (read-only vs. write).

Write tools in the DNS, Firewall, and Routes subsystems follow a stage-then-apply
pattern: `*_add` / `*_update` / `*_delete` calls stage changes, and nothing takes
effect until the corresponding `*_apply` tool is called. Services tools
(start/stop/restart) act immediately with no staging.

## DHCP (3 tools) — all read-only

| Tool | Type |
|---|---|
| `dhcp_lease_list` | Read |
| `dhcp_settings_get` | Read |
| `dhcp_static_list` | Read |

## DNS / Unbound (6 tools) — read + write

| Tool | Type |
|---|---|
| `dns_settings_get` | Read |
| `dns_host_override_list` | Read |
| `dns_host_override_add` | Write (staged) |
| `dns_host_override_update` | Write (staged) |
| `dns_host_override_delete` | Write (staged) |
| `dns_apply` | Write (applies staged changes, restarts Unbound) |

## Firewall (17 tools) — read + write, largest surface

**Filter rules**

| Tool | Type |
|---|---|
| `firewall_rule_list` | Read |
| `firewall_rule_get` | Read |
| `firewall_rule_add` | Write (staged) |
| `firewall_rule_update` | Write (staged) |
| `firewall_rule_delete` | Write (staged) |
| `firewall_rule_apply` | Write (apply) |

**Aliases**

| Tool | Type |
|---|---|
| `firewall_alias_list` | Read |
| `firewall_alias_get_uuid` | Read |
| `firewall_alias_add` | Write (staged) |
| `firewall_alias_update` | Write (staged) |
| `firewall_alias_delete` | Write (staged) |
| `firewall_alias_apply` | Write (apply) |

**NAT**

| Tool | Type |
|---|---|
| `firewall_nat_list` | Read |
| `firewall_nat_add` | Write (staged) |
| `firewall_nat_update` | Write (staged) |
| `firewall_nat_delete` | Write (staged) |
| `firewall_nat_apply` | Write (apply) |

## IDS/IPS (1 tool) — read-only

| Tool | Type |
|---|---|
| `ids_ruleset_list` | Read |

## Interfaces (4 tools) — all read-only

| Tool | Type |
|---|---|
| `interface_list` | Read |
| `interface_config` | Read |
| `interface_arp_table` | Read |
| `interface_ndp_table` | Read |

## Routes (5 tools) — read + write

| Tool | Type |
|---|---|
| `route_list` | Read |
| `route_add` | Write (staged) |
| `route_update` | Write (staged) |
| `route_delete` | Write (staged) |
| `route_apply` | Write (apply) |

## Services (4 tools) — read + write (state-changing, not config)

| Tool | Type |
|---|---|
| `service_status` | Read |
| `service_start` | Write (start unbound/kea/ids) |
| `service_stop` | Write (stop unbound/kea/ids) |
| `service_restart` | Write (restart unbound/kea/ids) |

## System (3 tools) — read-only

| Tool | Type |
|---|---|
| `system_status` | Read |
| `system_firmware_status` | Read |
| `system_config_backup` | Read (exports config XML — no mutation) |

## Summary

- **39 tools total**, 8 subsystems (dhcp, dns, firewall, ids, interfaces, routes, services, system).
- **Read-only subsystems:** DHCP, Interfaces, System, IDS — no write path at all.
- **Write-capable subsystems:** DNS, Firewall, Routes (stage-then-apply), and Services (immediate start/stop/restart).
- Firewall is the largest and most sensitive surface (17 tools, including NAT/port-forwarding and raw rule add/update/delete).
- DNS tools only wrap Unbound; there is no Dnsmasq wrapper.
