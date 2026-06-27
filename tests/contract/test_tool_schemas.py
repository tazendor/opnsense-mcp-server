"""Contract tests: verify each MCP tool across all 7 domains has the correct name,
non-empty description, and input schema required fields per contracts/*.md."""

from unittest.mock import AsyncMock

import pytest
from mcp.server.fastmcp import FastMCP

from opnsense_mcp.tools import dhcp, dns, firewall, interfaces, routes, services, system


@pytest.fixture
def firewall_mcp(mock_client: AsyncMock) -> FastMCP:
    mcp = FastMCP("test-firewall")
    firewall.register_tools(mcp, mock_client)
    return mcp


def _tool(mcp: FastMCP, name: str):  # type: ignore[no-untyped-def]
    tools = mcp._tool_manager._tools
    assert name in tools, f"Tool '{name}' not registered"
    return tools[name]


class TestFirewallRuleSchemas:
    def test_rule_list_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_rule_list")
        assert t.name == "firewall_rule_list"
        assert t.description

    def test_rule_list_no_required_params(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_rule_list")
        required = t.parameters.get("required", [])
        assert required == []

    def test_rule_get_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_rule_get")
        assert t.name == "firewall_rule_get"
        assert t.description

    def test_rule_get_requires_uuid(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_rule_get")
        assert "uuid" in t.parameters.get("required", [])

    def test_rule_add_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_rule_add")
        assert t.name == "firewall_rule_add"
        assert t.description

    def test_rule_add_requires_rule(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_rule_add")
        assert "rule" in t.parameters.get("required", [])

    def test_rule_update_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_rule_update")
        assert t.name == "firewall_rule_update"
        assert t.description

    def test_rule_update_requires_uuid_and_rule(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_rule_update")
        required = t.parameters.get("required", [])
        assert "uuid" in required
        assert "rule" in required

    def test_rule_delete_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_rule_delete")
        assert t.name == "firewall_rule_delete"
        assert t.description

    def test_rule_delete_requires_uuid(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_rule_delete")
        assert "uuid" in t.parameters.get("required", [])

    def test_rule_apply_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_rule_apply")
        assert t.name == "firewall_rule_apply"
        assert t.description

    def test_rule_apply_no_required_params(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_rule_apply")
        assert t.parameters.get("required", []) == []


class TestFirewallAliasSchemas:
    def test_alias_list_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_alias_list")
        assert t.name == "firewall_alias_list"
        assert t.description

    def test_alias_get_uuid_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_alias_get_uuid")
        assert t.name == "firewall_alias_get_uuid"
        assert t.description

    def test_alias_get_uuid_requires_name(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_alias_get_uuid")
        assert "name" in t.parameters.get("required", [])

    def test_alias_add_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_alias_add")
        assert t.name == "firewall_alias_add"
        assert t.description

    def test_alias_add_requires_alias(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_alias_add")
        assert "alias" in t.parameters.get("required", [])

    def test_alias_update_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_alias_update")
        assert t.name == "firewall_alias_update"
        assert t.description

    def test_alias_update_requires_uuid_and_alias(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_alias_update")
        required = t.parameters.get("required", [])
        assert "uuid" in required
        assert "alias" in required

    def test_alias_delete_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_alias_delete")
        assert t.name == "firewall_alias_delete"
        assert t.description

    def test_alias_delete_requires_uuid(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_alias_delete")
        assert "uuid" in t.parameters.get("required", [])

    def test_alias_apply_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_alias_apply")
        assert t.name == "firewall_alias_apply"
        assert t.description


class TestFirewallNatSchemas:
    def test_nat_list_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_nat_list")
        assert t.name == "firewall_nat_list"
        assert t.description

    def test_nat_list_no_required_params(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_nat_list")
        assert t.parameters.get("required", []) == []

    def test_nat_add_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_nat_add")
        assert t.name == "firewall_nat_add"
        assert t.description

    def test_nat_add_requires_rule(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_nat_add")
        assert "rule" in t.parameters.get("required", [])

    def test_nat_update_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_nat_update")
        assert t.name == "firewall_nat_update"
        assert t.description

    def test_nat_update_requires_uuid_and_rule(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_nat_update")
        required = t.parameters.get("required", [])
        assert "uuid" in required
        assert "rule" in required

    def test_nat_delete_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_nat_delete")
        assert t.name == "firewall_nat_delete"
        assert t.description

    def test_nat_delete_requires_uuid(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_nat_delete")
        assert "uuid" in t.parameters.get("required", [])

    def test_nat_apply_registered(self, firewall_mcp: FastMCP) -> None:
        t = _tool(firewall_mcp, "firewall_nat_apply")
        assert t.name == "firewall_nat_apply"
        assert t.description


# ---------------------------------------------------------------------------
# System domain (contracts/system.md) — 3 tools
# ---------------------------------------------------------------------------


@pytest.fixture
def system_mcp(mock_client: AsyncMock) -> FastMCP:
    mcp = FastMCP("test-system")
    system.register_tools(mcp, mock_client)
    return mcp


class TestSystemSchemas:
    def test_system_status_registered(self, system_mcp: FastMCP) -> None:
        t = _tool(system_mcp, "system_status")
        assert t.name == "system_status"
        assert t.description

    def test_system_status_no_required_params(self, system_mcp: FastMCP) -> None:
        t = _tool(system_mcp, "system_status")
        assert t.parameters.get("required", []) == []

    def test_system_firmware_status_registered(self, system_mcp: FastMCP) -> None:
        t = _tool(system_mcp, "system_firmware_status")
        assert t.name == "system_firmware_status"
        assert t.description

    def test_system_config_backup_registered(self, system_mcp: FastMCP) -> None:
        t = _tool(system_mcp, "system_config_backup")
        assert t.name == "system_config_backup"
        assert t.description


# ---------------------------------------------------------------------------
# Interfaces domain (contracts/interfaces.md) — 4 tools
# ---------------------------------------------------------------------------


@pytest.fixture
def interfaces_mcp(mock_client: AsyncMock) -> FastMCP:
    mcp = FastMCP("test-interfaces")
    interfaces.register_tools(mcp, mock_client)
    return mcp


class TestInterfaceSchemas:
    def test_interface_list_registered(self, interfaces_mcp: FastMCP) -> None:
        t = _tool(interfaces_mcp, "interface_list")
        assert t.name == "interface_list"
        assert t.description

    def test_interface_config_registered(self, interfaces_mcp: FastMCP) -> None:
        t = _tool(interfaces_mcp, "interface_config")
        assert t.name == "interface_config"
        assert t.description

    def test_interface_arp_table_registered(self, interfaces_mcp: FastMCP) -> None:
        t = _tool(interfaces_mcp, "interface_arp_table")
        assert t.name == "interface_arp_table"
        assert t.description

    def test_interface_ndp_table_registered(self, interfaces_mcp: FastMCP) -> None:
        t = _tool(interfaces_mcp, "interface_ndp_table")
        assert t.name == "interface_ndp_table"
        assert t.description


# ---------------------------------------------------------------------------
# DHCP domain (contracts/dhcp.md) — 3 tools
# ---------------------------------------------------------------------------


@pytest.fixture
def dhcp_mcp(mock_client: AsyncMock) -> FastMCP:
    mcp = FastMCP("test-dhcp")
    dhcp.register_tools(mcp, mock_client)
    return mcp


class TestDhcpSchemas:
    def test_dhcp_lease_list_registered(self, dhcp_mcp: FastMCP) -> None:
        t = _tool(dhcp_mcp, "dhcp_lease_list")
        assert t.name == "dhcp_lease_list"
        assert t.description

    def test_dhcp_lease_list_no_required_params(self, dhcp_mcp: FastMCP) -> None:
        t = _tool(dhcp_mcp, "dhcp_lease_list")
        assert t.parameters.get("required", []) == []

    def test_dhcp_settings_get_registered(self, dhcp_mcp: FastMCP) -> None:
        t = _tool(dhcp_mcp, "dhcp_settings_get")
        assert t.name == "dhcp_settings_get"
        assert t.description

    def test_dhcp_static_list_registered(self, dhcp_mcp: FastMCP) -> None:
        t = _tool(dhcp_mcp, "dhcp_static_list")
        assert t.name == "dhcp_static_list"
        assert t.description


# ---------------------------------------------------------------------------
# Routes domain (contracts/routes.md) — 5 tools
# ---------------------------------------------------------------------------


@pytest.fixture
def routes_mcp(mock_client: AsyncMock) -> FastMCP:
    mcp = FastMCP("test-routes")
    routes.register_tools(mcp, mock_client)
    return mcp


class TestRouteSchemas:
    def test_route_list_registered(self, routes_mcp: FastMCP) -> None:
        t = _tool(routes_mcp, "route_list")
        assert t.name == "route_list"
        assert t.description

    def test_route_list_no_required_params(self, routes_mcp: FastMCP) -> None:
        t = _tool(routes_mcp, "route_list")
        assert t.parameters.get("required", []) == []

    def test_route_add_registered(self, routes_mcp: FastMCP) -> None:
        t = _tool(routes_mcp, "route_add")
        assert t.name == "route_add"
        assert t.description

    def test_route_add_requires_route(self, routes_mcp: FastMCP) -> None:
        assert "route" in _tool(routes_mcp, "route_add").parameters.get("required", [])

    def test_route_update_registered(self, routes_mcp: FastMCP) -> None:
        t = _tool(routes_mcp, "route_update")
        assert t.name == "route_update"
        assert t.description

    def test_route_update_requires_uuid_and_route(self, routes_mcp: FastMCP) -> None:
        required = _tool(routes_mcp, "route_update").parameters.get("required", [])
        assert "uuid" in required
        assert "route" in required

    def test_route_delete_registered(self, routes_mcp: FastMCP) -> None:
        t = _tool(routes_mcp, "route_delete")
        assert t.name == "route_delete"
        assert t.description

    def test_route_delete_requires_uuid(self, routes_mcp: FastMCP) -> None:
        required = _tool(routes_mcp, "route_delete").parameters.get("required", [])
        assert "uuid" in required

    def test_route_apply_registered(self, routes_mcp: FastMCP) -> None:
        t = _tool(routes_mcp, "route_apply")
        assert t.name == "route_apply"
        assert t.description


# ---------------------------------------------------------------------------
# DNS domain (contracts/dns.md) — 6 tools
# ---------------------------------------------------------------------------


@pytest.fixture
def dns_mcp(mock_client: AsyncMock) -> FastMCP:
    mcp = FastMCP("test-dns")
    dns.register_tools(mcp, mock_client)
    return mcp


class TestDnsSchemas:
    def test_dns_settings_get_registered(self, dns_mcp: FastMCP) -> None:
        t = _tool(dns_mcp, "dns_settings_get")
        assert t.name == "dns_settings_get"
        assert t.description

    def test_dns_host_override_list_registered(self, dns_mcp: FastMCP) -> None:
        t = _tool(dns_mcp, "dns_host_override_list")
        assert t.name == "dns_host_override_list"
        assert t.description

    def test_dns_host_override_add_registered(self, dns_mcp: FastMCP) -> None:
        t = _tool(dns_mcp, "dns_host_override_add")
        assert t.name == "dns_host_override_add"
        assert t.description

    def test_dns_host_override_add_requires_host(self, dns_mcp: FastMCP) -> None:
        t = _tool(dns_mcp, "dns_host_override_add")
        assert "host" in t.parameters.get("required", [])

    def test_dns_host_override_update_registered(self, dns_mcp: FastMCP) -> None:
        t = _tool(dns_mcp, "dns_host_override_update")
        assert t.name == "dns_host_override_update"
        assert t.description

    def test_dns_host_override_update_requires_uuid_and_host(
        self, dns_mcp: FastMCP
    ) -> None:
        t = _tool(dns_mcp, "dns_host_override_update")
        required = t.parameters.get("required", [])
        assert "uuid" in required
        assert "host" in required

    def test_dns_host_override_delete_registered(self, dns_mcp: FastMCP) -> None:
        t = _tool(dns_mcp, "dns_host_override_delete")
        assert t.name == "dns_host_override_delete"
        assert t.description

    def test_dns_host_override_delete_requires_uuid(self, dns_mcp: FastMCP) -> None:
        t = _tool(dns_mcp, "dns_host_override_delete")
        assert "uuid" in t.parameters.get("required", [])

    def test_dns_apply_registered(self, dns_mcp: FastMCP) -> None:
        t = _tool(dns_mcp, "dns_apply")
        assert t.name == "dns_apply"
        assert t.description


# ---------------------------------------------------------------------------
# Services domain (contracts/services.md) — 4 tools
# ---------------------------------------------------------------------------


@pytest.fixture
def services_mcp(mock_client: AsyncMock) -> FastMCP:
    mcp = FastMCP("test-services")
    services.register_tools(mcp, mock_client)
    return mcp


class TestServicesSchemas:
    def test_service_status_registered(self, services_mcp: FastMCP) -> None:
        t = _tool(services_mcp, "service_status")
        assert t.name == "service_status"
        assert t.description

    def test_service_status_requires_module(self, services_mcp: FastMCP) -> None:
        required = _tool(services_mcp, "service_status").parameters.get("required", [])
        assert "module" in required

    def test_service_start_registered(self, services_mcp: FastMCP) -> None:
        t = _tool(services_mcp, "service_start")
        assert t.name == "service_start"
        assert t.description

    def test_service_start_requires_module(self, services_mcp: FastMCP) -> None:
        required = _tool(services_mcp, "service_start").parameters.get("required", [])
        assert "module" in required

    def test_service_stop_registered(self, services_mcp: FastMCP) -> None:
        t = _tool(services_mcp, "service_stop")
        assert t.name == "service_stop"
        assert t.description

    def test_service_stop_requires_module(self, services_mcp: FastMCP) -> None:
        required = _tool(services_mcp, "service_stop").parameters.get("required", [])
        assert "module" in required

    def test_service_restart_registered(self, services_mcp: FastMCP) -> None:
        t = _tool(services_mcp, "service_restart")
        assert t.name == "service_restart"
        assert t.description

    def test_service_restart_requires_module(self, services_mcp: FastMCP) -> None:
        required = _tool(services_mcp, "service_restart").parameters.get("required", [])
        assert "module" in required
