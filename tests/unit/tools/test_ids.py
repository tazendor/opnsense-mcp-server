from unittest.mock import AsyncMock

import pytest

from opnsense_mcp.errors import OPNsenseAPIError, ToolError
from opnsense_mcp.tools.ids import _ids_alert_list, _ids_ruleset_list


class TestIdsAlertList:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"rows": [], "total": 0}
        await _ids_alert_list(mock_client)
        mock_client.post.assert_called_once_with(
            "ids/alert/search",
            {"current": 1, "rowCount": 100, "searchPhrase": "", "sort": {}},
        )

    async def test_custom_row_count_and_phrase(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"rows": [], "total": 0}
        await _ids_alert_list(mock_client, row_count=25, search_phrase="ET SCAN")
        mock_client.post.assert_called_once_with(
            "ids/alert/search",
            {"current": 1, "rowCount": 25, "searchPhrase": "ET SCAN", "sort": {}},
        )

    async def test_returns_rows(self, mock_client: AsyncMock) -> None:
        rows = [{"sid": "1234", "src_ip": "1.2.3.4", "dest_ip": "5.6.7.8"}]
        mock_client.post.return_value = {"rows": rows, "total": 1}
        result = await _ids_alert_list(mock_client)
        assert result["rows"] == rows
        assert result["total"] == 1

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.side_effect = OPNsenseAPIError(
            status_code=500,
            body={},
            path="ids/alert/search",
            method="POST",
        )
        with pytest.raises(ToolError) as exc_info:
            await _ids_alert_list(mock_client)
        assert "500" in str(exc_info.value)


class TestIdsRulesetList:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"rows": [], "total": 0}
        await _ids_ruleset_list(mock_client)
        mock_client.post.assert_called_once_with(
            "ids/settings/searchRuleset",
            {"current": 1, "rowCount": 100, "searchPhrase": "", "sort": {}},
        )

    async def test_returns_rows(self, mock_client: AsyncMock) -> None:
        rows = [{"filename": "emerging-scan.rules", "enabled": "1"}]
        mock_client.post.return_value = {"rows": rows, "total": 1}
        result = await _ids_ruleset_list(mock_client)
        assert result["rows"] == rows

    async def test_search_phrase_forwarded(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"rows": [], "total": 0}
        await _ids_ruleset_list(mock_client, search_phrase="emerging")
        call_args = mock_client.post.call_args
        assert call_args[0][1]["searchPhrase"] == "emerging"

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.side_effect = OPNsenseAPIError(
            status_code=404,
            body={},
            path="ids/settings/searchRuleset",
            method="POST",
        )
        with pytest.raises(ToolError) as exc_info:
            await _ids_ruleset_list(mock_client)
        assert "404" in str(exc_info.value)
