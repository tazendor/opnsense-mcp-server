import pytest

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.tools.firewall import (
    _alias_add,
    _alias_apply,
    _alias_delete,
    _alias_get_uuid,
    _alias_list,
    _nat_add,
    _nat_apply,
    _nat_delete,
    _nat_list,
    _rule_add,
    _rule_apply,
    _rule_delete,
    _rule_list,
)


@pytest.mark.integration
class TestFirewallRuleIntegration:
    async def test_rule_list_returns_rows_key(
        self, live_client: OPNsenseClient
    ) -> None:
        result = await _rule_list(live_client)
        assert "rows" in result
        assert "total" in result

    async def test_rule_crud_cycle(self, live_client: OPNsenseClient) -> None:
        rule = {
            "enabled": "1",
            "action": "block",
            "interface": "lan",
            "direction": "in",
            "ipprotocol": "inet",
            "protocol": "any",
            "source_net": "10.255.255.0/24",
            "destination_net": "any",
            "description": "mcp-integration-test",
        }

        # Add
        added = await _rule_add(live_client, rule=rule)
        uuid = added.get("uuid", "")
        assert uuid, "Expected a UUID from rule_add"

        try:
            # Verify present in list
            listing = await _rule_list(live_client)
            uuids = [r.get("uuid") for r in listing.get("rows", [])]
            assert uuid in uuids

            # Apply
            applied = await _rule_apply(live_client)
            assert applied.get("status", "").strip().lower() == "ok"
        finally:
            # Always clean up even if assertions above fail
            await _rule_delete(live_client, uuid=uuid)
            await _rule_apply(live_client)


@pytest.mark.integration
class TestFirewallAliasIntegration:
    async def test_alias_list_returns_aliases_key(
        self, live_client: OPNsenseClient
    ) -> None:
        result = await _alias_list(live_client)
        assert "alias" in result

    async def test_alias_crud_cycle(self, live_client: OPNsenseClient) -> None:
        alias = {
            "name": "mcp_integ_test",
            "type": "host",
            "content": "203.0.113.1",
            "description": "mcp-integration-test",
            "enabled": "1",
        }

        added = await _alias_add(live_client, alias=alias)
        uuid = added.get("uuid", "")
        assert uuid, "Expected a UUID from alias_add"

        try:
            by_name = await _alias_get_uuid(live_client, name="mcp_integ_test")
            assert by_name.get("uuid") == uuid

            applied = await _alias_apply(live_client)
            assert applied.get("status", "").strip().lower() == "ok"
        finally:
            await _alias_delete(live_client, uuid=uuid)
            await _alias_apply(live_client)


_NAT_SKIP = pytest.mark.xfail(
    reason="firewall/nat/* requires os-firewall plugin (not installed)",
    strict=False,
)


@pytest.mark.integration
class TestFirewallNatIntegration:
    @_NAT_SKIP
    async def test_nat_list_returns_rows_key(self, live_client: OPNsenseClient) -> None:
        result = await _nat_list(live_client)
        assert "rows" in result

    @_NAT_SKIP
    async def test_nat_crud_cycle(self, live_client: OPNsenseClient) -> None:
        rule = {
            "interface": "wan",
            "protocol": "tcp",
            "destination_port": "12399",
            "target": "192.168.1.100",
            "local_port": "12399",
            "description": "mcp-integration-test",
            "enabled": "1",
        }

        added = await _nat_add(live_client, rule=rule)
        uuid = added.get("uuid", "")
        assert uuid, "Expected a UUID from nat_add"

        try:
            listing = await _nat_list(live_client)
            uuids = [r.get("uuid") for r in listing.get("rows", [])]
            assert uuid in uuids
        finally:
            await _nat_delete(live_client, uuid=uuid)
            await _nat_apply(live_client)
