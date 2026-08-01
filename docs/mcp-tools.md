# MCP Server Tools

Full inventory of tools exposed by this MCP server, grouped by subsystem. Generated from the live tool registry (`create_server`).

- **223 tools total**, 14 subsystems.
- **⚠ high-risk** tools require a two-step confirm-then-execute flow (call once to preview, again with the returned `confirm` token). See `specs/002-complete-api-coverage/contracts/confirmation.md`.
- Write tools in most subsystems follow a stage-then-apply pattern (`*_add`/`*_update`/`*_delete` stage; `*_apply` applies).

## System (12 tools — 5 high-risk)

| Tool | |
|---|---|
| `system_config_backup` |  |
| `system_config_backup_list` |  |
| `system_config_restore` | ⚠ high-risk |
| `system_firmware_check` |  |
| `system_firmware_log` |  |
| `system_firmware_status` |  |
| `system_firmware_update` | ⚠ high-risk |
| `system_firmware_upgrade` | ⚠ high-risk |
| `system_firmware_upgrade_status` |  |
| `system_halt` | ⚠ high-risk |
| `system_reboot` | ⚠ high-risk |
| `system_status` |  |

## Firewall (17 tools)

| Tool | |
|---|---|
| `firewall_alias_add` |  |
| `firewall_alias_apply` |  |
| `firewall_alias_delete` |  |
| `firewall_alias_get_uuid` |  |
| `firewall_alias_list` |  |
| `firewall_alias_update` |  |
| `firewall_nat_add` |  |
| `firewall_nat_apply` |  |
| `firewall_nat_delete` |  |
| `firewall_nat_list` |  |
| `firewall_nat_update` |  |
| `firewall_rule_add` |  |
| `firewall_rule_apply` |  |
| `firewall_rule_delete` |  |
| `firewall_rule_get` |  |
| `firewall_rule_list` |  |
| `firewall_rule_update` |  |

## Interfaces (10 tools — 2 high-risk)

| Tool | |
|---|---|
| `interface_apply` |  |
| `interface_arp_table` |  |
| `interface_assignment_add` |  |
| `interface_assignment_delete` | ⚠ high-risk |
| `interface_assignment_get` |  |
| `interface_assignment_list` |  |
| `interface_assignment_update` | ⚠ high-risk |
| `interface_config` |  |
| `interface_list` |  |
| `interface_ndp_table` |  |

## Routes (5 tools)

| Tool | |
|---|---|
| `route_add` |  |
| `route_apply` |  |
| `route_delete` |  |
| `route_list` |  |
| `route_update` |  |

## DHCP (8 tools)

| Tool | |
|---|---|
| `dhcp_apply` |  |
| `dhcp_lease_list` |  |
| `dhcp_settings_get` |  |
| `dhcp_settings_update` |  |
| `dhcp_static_add` |  |
| `dhcp_static_delete` |  |
| `dhcp_static_list` |  |
| `dhcp_static_update` |  |

## DNS / Unbound (6 tools)

| Tool | |
|---|---|
| `dns_apply` |  |
| `dns_host_override_add` |  |
| `dns_host_override_delete` |  |
| `dns_host_override_list` |  |
| `dns_host_override_update` |  |
| `dns_settings_get` |  |

## IDS / IPS (4 tools)

| Tool | |
|---|---|
| `ids_apply` |  |
| `ids_rule_toggle` |  |
| `ids_ruleset_list` |  |
| `ids_ruleset_toggle` |  |

## Services (4 tools)

| Tool | |
|---|---|
| `service_restart` |  |
| `service_start` |  |
| `service_status` |  |
| `service_stop` |  |

## OpenVPN (24 tools — 1 high-risk)

| Tool | |
|---|---|
| `openvpn_apply` |  |
| `openvpn_client_override_add` |  |
| `openvpn_client_override_delete` |  |
| `openvpn_client_override_get` |  |
| `openvpn_client_override_list` |  |
| `openvpn_client_override_update` |  |
| `openvpn_instance_add` |  |
| `openvpn_instance_delete` | ⚠ high-risk |
| `openvpn_instance_get` |  |
| `openvpn_instance_list` |  |
| `openvpn_instance_toggle` |  |
| `openvpn_instance_update` |  |
| `openvpn_route_list` |  |
| `openvpn_service_restart` |  |
| `openvpn_service_start` |  |
| `openvpn_service_stop` |  |
| `openvpn_session_kill` |  |
| `openvpn_session_list` |  |
| `openvpn_static_key_add` |  |
| `openvpn_static_key_delete` |  |
| `openvpn_static_key_generate` |  |
| `openvpn_static_key_get` |  |
| `openvpn_static_key_list` |  |
| `openvpn_static_key_update` |  |

## IPsec (50 tools — 2 high-risk)

| Tool | |
|---|---|
| `ipsec_apply` |  |
| `ipsec_child_add` |  |
| `ipsec_child_delete` |  |
| `ipsec_child_get` |  |
| `ipsec_child_list` |  |
| `ipsec_child_toggle` |  |
| `ipsec_child_update` |  |
| `ipsec_connection_add` |  |
| `ipsec_connection_delete` | ⚠ high-risk |
| `ipsec_connection_get` |  |
| `ipsec_connection_list` |  |
| `ipsec_connection_toggle` |  |
| `ipsec_connection_update` |  |
| `ipsec_enabled_get` |  |
| `ipsec_enabled_toggle` | ⚠ high-risk |
| `ipsec_keypair_add` |  |
| `ipsec_keypair_delete` |  |
| `ipsec_keypair_generate` |  |
| `ipsec_keypair_get` |  |
| `ipsec_keypair_list` |  |
| `ipsec_keypair_update` |  |
| `ipsec_local_add` |  |
| `ipsec_local_delete` |  |
| `ipsec_local_get` |  |
| `ipsec_local_list` |  |
| `ipsec_local_toggle` |  |
| `ipsec_local_update` |  |
| `ipsec_pool_add` |  |
| `ipsec_pool_delete` |  |
| `ipsec_pool_get` |  |
| `ipsec_pool_list` |  |
| `ipsec_pool_toggle` |  |
| `ipsec_pool_update` |  |
| `ipsec_psk_add` |  |
| `ipsec_psk_delete` |  |
| `ipsec_psk_get` |  |
| `ipsec_psk_list` |  |
| `ipsec_psk_update` |  |
| `ipsec_remote_add` |  |
| `ipsec_remote_delete` |  |
| `ipsec_remote_get` |  |
| `ipsec_remote_list` |  |
| `ipsec_remote_toggle` |  |
| `ipsec_remote_update` |  |
| `ipsec_service_restart` |  |
| `ipsec_service_start` |  |
| `ipsec_service_stop` |  |
| `ipsec_session_connect` |  |
| `ipsec_session_disconnect` |  |
| `ipsec_session_list` |  |

## WireGuard (24 tools — 1 high-risk)

| Tool | |
|---|---|
| `wireguard_apply` |  |
| `wireguard_client_add` |  |
| `wireguard_client_builder_add` |  |
| `wireguard_client_builder_get` |  |
| `wireguard_client_delete` |  |
| `wireguard_client_get` |  |
| `wireguard_client_list` |  |
| `wireguard_client_psk_generate` |  |
| `wireguard_client_toggle` |  |
| `wireguard_client_update` |  |
| `wireguard_general_get` |  |
| `wireguard_general_update` |  |
| `wireguard_server_add` |  |
| `wireguard_server_delete` | ⚠ high-risk |
| `wireguard_server_get` |  |
| `wireguard_server_keypair_generate` |  |
| `wireguard_server_list` |  |
| `wireguard_server_list_for_client` |  |
| `wireguard_server_toggle` |  |
| `wireguard_server_update` |  |
| `wireguard_service_restart` |  |
| `wireguard_service_start` |  |
| `wireguard_service_stop` |  |
| `wireguard_status` |  |

## Web Proxy (Squid) (28 tools)

| Tool | |
|---|---|
| `proxy_apply` |  |
| `proxy_pac_match_add` |  |
| `proxy_pac_match_delete` |  |
| `proxy_pac_match_get` |  |
| `proxy_pac_match_list` |  |
| `proxy_pac_match_update` |  |
| `proxy_pac_proxy_add` |  |
| `proxy_pac_proxy_delete` |  |
| `proxy_pac_proxy_get` |  |
| `proxy_pac_proxy_list` |  |
| `proxy_pac_proxy_update` |  |
| `proxy_pac_rule_add` |  |
| `proxy_pac_rule_delete` |  |
| `proxy_pac_rule_get` |  |
| `proxy_pac_rule_list` |  |
| `proxy_pac_rule_update` |  |
| `proxy_remote_blacklist_add` |  |
| `proxy_remote_blacklist_delete` |  |
| `proxy_remote_blacklist_get` |  |
| `proxy_remote_blacklist_list` |  |
| `proxy_remote_blacklist_toggle` |  |
| `proxy_remote_blacklist_update` |  |
| `proxy_service_reset` |  |
| `proxy_service_restart` |  |
| `proxy_service_start` |  |
| `proxy_service_stop` |  |
| `proxy_settings_get` |  |
| `proxy_settings_update` |  |

## Captive Portal (15 tools — 1 high-risk)

| Tool | |
|---|---|
| `captiveportal_apply` |  |
| `captiveportal_service_restart` |  |
| `captiveportal_service_start` |  |
| `captiveportal_service_stop` |  |
| `captiveportal_session_connect` |  |
| `captiveportal_session_disconnect` |  |
| `captiveportal_session_disconnect_zone` | ⚠ high-risk |
| `captiveportal_session_list` |  |
| `captiveportal_zone_add` |  |
| `captiveportal_zone_delete` |  |
| `captiveportal_zone_get` |  |
| `captiveportal_zone_list` |  |
| `captiveportal_zone_names` |  |
| `captiveportal_zone_toggle` |  |
| `captiveportal_zone_update` |  |

## Trust / Certificates (16 tools — 1 high-risk)

| Tool | |
|---|---|
| `trust_ca_add` |  |
| `trust_ca_delete` |  |
| `trust_ca_get` |  |
| `trust_ca_list` |  |
| `trust_ca_update` |  |
| `trust_certificate_add` |  |
| `trust_certificate_delete` |  |
| `trust_certificate_export` |  |
| `trust_certificate_get` |  |
| `trust_certificate_list` |  |
| `trust_certificate_revoke` | ⚠ high-risk |
| `trust_certificate_update` |  |
| `trust_crl_get` |  |
| `trust_crl_list` |  |
| `trust_settings_get` |  |
| `trust_settings_update` |  |

