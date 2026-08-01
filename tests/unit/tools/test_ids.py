from unittest.mock import AsyncMock

import pytest

from opnsense_mcp.errors import OPNsenseAPIError, ToolError
from opnsense_mcp.tools.ids import (
    _ids_apply,
    _ids_rule_toggle,
    _ids_ruleset_list,
    _ids_ruleset_toggle,
)


class TestIdsRulesetList:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"total": 0, "rowCount": 0, "rows": []}
        await _ids_ruleset_list(mock_client)
        mock_client.get.assert_called_once_with("ids/settings/listRulesets")

    async def test_returns_rows(self, mock_client: AsyncMock) -> None:
        rows = [{"filename": "emerging-scan.rules", "enabled": "1"}]
        mock_client.get.return_value = {"total": 1, "rowCount": 1, "rows": rows}
        result = await _ids_ruleset_list(mock_client)
        assert result["rows"] == rows

    async def test_returns_total(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"total": 68, "rowCount": 68, "rows": []}
        result = await _ids_ruleset_list(mock_client)
        assert result["total"] == 68

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.get.side_effect = OPNsenseAPIError(
            status_code=500,
            body={},
            path="ids/settings/listRulesets",
            method="GET",
        )
        with pytest.raises(ToolError) as exc_info:
            await _ids_ruleset_list(mock_client)
        assert "500" in str(exc_info.value)


class TestIdsRulesetToggle:
    async def test_toggle_with_enabled_state(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "ok"}
        await _ids_ruleset_toggle(mock_client, "emerging-scan.rules", enabled=0)
        mock_client.post.assert_called_once_with(
            "ids/settings/toggle_ruleset/emerging-scan.rules/0", None
        )

    async def test_toggle_without_enabled_flips_state(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.return_value = {"result": "ok"}
        await _ids_ruleset_toggle(mock_client, "emerging-scan.rules")
        mock_client.post.assert_called_once_with(
            "ids/settings/toggle_ruleset/emerging-scan.rules", None
        )


class TestIdsRuleToggle:
    async def test_toggle_rule_by_sid(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "ok"}
        await _ids_rule_toggle(mock_client, "2001,2002", enabled=1)
        mock_client.post.assert_called_once_with(
            "ids/settings/toggle_rule/2001,2002/1", None
        )


class TestIdsApply:
    async def test_posts_reconfigure(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"status": "ok"}
        await _ids_apply(mock_client)
        mock_client.post.assert_called_once_with("ids/service/reconfigure", None)
