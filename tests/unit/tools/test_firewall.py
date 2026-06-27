from unittest.mock import AsyncMock

import pytest

from opnsense_mcp.errors import OPNsenseAPIError, ToolError
from opnsense_mcp.tools.firewall import (
    _alias_add,
    _alias_apply,
    _alias_delete,
    _alias_get_uuid,
    _alias_list,
    _alias_update,
    _nat_add,
    _nat_apply,
    _nat_delete,
    _nat_list,
    _nat_update,
    _rule_add,
    _rule_apply,
    _rule_delete,
    _rule_get,
    _rule_list,
    _rule_update,
)


class TestFirewallRuleList:
    async def test_calls_post_with_default_payload(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.return_value = {
            "rows": [],
            "rowCount": 0,
            "total": 0,
            "current": 1,
        }
        await _rule_list(mock_client)
        mock_client.post.assert_called_once_with(
            "firewall/filter/search_rule",
            {"current": 1, "rowCount": -1, "searchPhrase": ""},
        )

    async def test_returns_rows(self, mock_client: AsyncMock) -> None:
        rows = [{"uuid": "abc", "description": "allow ssh"}]
        mock_client.post.return_value = {"rows": rows, "total": 1, "current": 1}
        result = await _rule_list(mock_client)
        assert result["rows"] == rows


class TestFirewallRuleGet:
    async def test_calls_endpoint_with_uuid(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"rule": {"action": "pass"}}
        result = await _rule_get(mock_client, uuid="test-uuid-1")
        mock_client.get.assert_called_once_with("firewall/filter/get_rule/test-uuid-1")
        assert "rule" in result

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.get.side_effect = OPNsenseAPIError(
            status_code=404,
            body={},
            path="firewall/filter/get_rule/bad-uuid",
            method="GET",
        )
        with pytest.raises(ToolError) as exc_info:
            await _rule_get(mock_client, uuid="bad-uuid")
        assert "404" in str(exc_info.value)


class TestFirewallRuleAdd:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        rule = {"enabled": "1", "action": "pass", "interface": "lan", "direction": "in"}
        mock_client.post.return_value = {"result": "saved", "uuid": "new-uuid-1"}
        await _rule_add(mock_client, rule=rule)
        mock_client.post.assert_called_once_with(
            "firewall/filter/add_rule", {"rule": rule}
        )

    async def test_returns_uuid(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved", "uuid": "new-uuid-1"}
        rule = {
            "enabled": "1",
            "action": "pass",
            "interface": "lan",
            "direction": "in",
        }
        result = await _rule_add(mock_client, rule=rule)
        assert result["uuid"] == "new-uuid-1"

    async def test_validation_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.side_effect = OPNsenseAPIError(
            status_code=400,
            body={"validations": {"rule.interface": "Invalid interface"}},
            path="firewall/filter/add_rule",
            method="POST",
        )
        rule = {
            "enabled": "1",
            "action": "pass",
            "interface": "bad",
            "direction": "in",
        }
        with pytest.raises(ToolError) as exc_info:
            await _rule_add(mock_client, rule=rule)
        assert "400" in str(exc_info.value)


class TestFirewallRuleUpdate:
    async def test_calls_endpoint_with_uuid(self, mock_client: AsyncMock) -> None:
        rule = {"description": "updated"}
        mock_client.post.return_value = {"result": "saved"}
        await _rule_update(mock_client, uuid="rule-uuid-1", rule=rule)
        mock_client.post.assert_called_once_with(
            "firewall/filter/set_rule/rule-uuid-1", {"rule": rule}
        )

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.side_effect = OPNsenseAPIError(
            status_code=404, body={}, path="firewall/filter/set_rule/bad", method="POST"
        )
        with pytest.raises(ToolError):
            await _rule_update(mock_client, uuid="bad", rule={})


class TestFirewallRuleDelete:
    async def test_calls_endpoint_with_uuid(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "deleted"}
        result = await _rule_delete(mock_client, uuid="rule-uuid-1")
        mock_client.post.assert_called_once_with(
            "firewall/filter/del_rule/rule-uuid-1", None
        )
        assert result["result"] == "deleted"

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.side_effect = OPNsenseAPIError(
            status_code=404, body={}, path="firewall/filter/del_rule/bad", method="POST"
        )
        with pytest.raises(ToolError):
            await _rule_delete(mock_client, uuid="bad")


class TestFirewallRuleApply:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"status": "ok"}
        result = await _rule_apply(mock_client)
        mock_client.post.assert_called_once_with("firewall/filter/apply", None)
        assert result["status"] == "ok"


class TestFirewallAliasList:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"aliases": {"alias": {}}}
        result = await _alias_list(mock_client)
        mock_client.get.assert_called_once_with("firewall/alias/get")
        assert "aliases" in result


class TestFirewallAliasGetUuid:
    async def test_calls_endpoint_with_name(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"uuid": "alias-uuid-1"}
        result = await _alias_get_uuid(mock_client, name="MyAlias")
        mock_client.get.assert_called_once_with("firewall/alias/getAliasUUID/MyAlias")
        assert result["uuid"] == "alias-uuid-1"

    async def test_returns_empty_uuid_when_not_found(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.get.return_value = {"uuid": ""}
        result = await _alias_get_uuid(mock_client, name="Unknown")
        assert result["uuid"] == ""


class TestFirewallAliasAdd:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        alias = {"name": "MyHosts", "type": "host", "content": "1.2.3.4"}
        mock_client.post.return_value = {"result": "saved", "uuid": "alias-uuid-1"}
        await _alias_add(mock_client, alias=alias)
        mock_client.post.assert_called_once_with(
            "firewall/alias/add_item", {"alias": alias}
        )

    async def test_returns_uuid(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved", "uuid": "alias-uuid-1"}
        result = await _alias_add(
            mock_client, alias={"name": "X", "type": "host", "content": "1.1.1.1"}
        )
        assert result["uuid"] == "alias-uuid-1"


class TestFirewallAliasUpdate:
    async def test_calls_endpoint_with_uuid(self, mock_client: AsyncMock) -> None:
        alias = {"content": "2.2.2.2"}
        mock_client.post.return_value = {"result": "saved"}
        await _alias_update(mock_client, uuid="alias-uuid-1", alias=alias)
        mock_client.post.assert_called_once_with(
            "firewall/alias/set_item/alias-uuid-1", {"alias": alias}
        )


class TestFirewallAliasDelete:
    async def test_calls_endpoint_with_uuid(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "deleted"}
        result = await _alias_delete(mock_client, uuid="alias-uuid-1")
        mock_client.post.assert_called_once_with(
            "firewall/alias/del_item/alias-uuid-1", None
        )
        assert result["result"] == "deleted"


class TestFirewallAliasApply:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"status": "ok"}
        result = await _alias_apply(mock_client)
        mock_client.post.assert_called_once_with("firewall/alias/reconfigure", None)
        assert result["status"] == "ok"


class TestFirewallNatList:
    async def test_calls_post_with_default_payload(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.return_value = {"rows": [], "total": 0, "current": 1}
        await _nat_list(mock_client)
        mock_client.post.assert_called_once_with(
            "firewall/nat/searchrule",
            {"current": 1, "rowCount": -1, "searchPhrase": ""},
        )

    async def test_returns_rows(self, mock_client: AsyncMock) -> None:
        rows = [{"uuid": "nat-uuid-1", "description": "fwd http"}]
        mock_client.post.return_value = {"rows": rows, "total": 1, "current": 1}
        result = await _nat_list(mock_client)
        assert result["rows"] == rows


class TestFirewallNatAdd:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        rule = {"interface": "wan", "destination_port": "80"}
        mock_client.post.return_value = {"result": "saved", "uuid": "nat-uuid-1"}
        await _nat_add(mock_client, rule=rule)
        mock_client.post.assert_called_once_with("firewall/nat/addrule", {"rule": rule})

    async def test_returns_uuid(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved", "uuid": "nat-uuid-1"}
        result = await _nat_add(mock_client, rule={"interface": "wan"})
        assert result["uuid"] == "nat-uuid-1"


class TestFirewallNatUpdate:
    async def test_calls_endpoint_with_uuid(self, mock_client: AsyncMock) -> None:
        rule = {"destination_port": "8080"}
        mock_client.post.return_value = {"result": "saved"}
        await _nat_update(mock_client, uuid="nat-uuid-1", rule=rule)
        mock_client.post.assert_called_once_with(
            "firewall/nat/setrule/nat-uuid-1", {"rule": rule}
        )


class TestFirewallNatDelete:
    async def test_calls_endpoint_with_uuid(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "deleted"}
        result = await _nat_delete(mock_client, uuid="nat-uuid-1")
        mock_client.post.assert_called_once_with(
            "firewall/nat/delrule/nat-uuid-1", None
        )
        assert result["result"] == "deleted"


class TestFirewallNatApply:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"status": "ok"}
        result = await _nat_apply(mock_client)
        mock_client.post.assert_called_once_with("firewall/nat/apply", None)
        assert result["status"] == "ok"
