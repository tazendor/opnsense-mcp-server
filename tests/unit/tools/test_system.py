from unittest.mock import AsyncMock

import pytest

from opnsense_mcp.errors import OPNsenseAPIError, ToolError
from opnsense_mcp.tools.system import (
    _system_config_backup,
    _system_firmware_status,
    _system_status,
)


class TestSystemStatus:
    async def test_returns_dict(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"metadata": {"system": {"status": 2}}}
        result = await _system_status(mock_client)
        mock_client.get.assert_called_once_with("core/system/status")
        assert result == {"metadata": {"system": {"status": 2}}}

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.get.side_effect = OPNsenseAPIError(
            status_code=401,
            body={"message": "Unauthorized"},
            path="core/system/status",
            method="GET",
        )
        with pytest.raises(ToolError) as exc_info:
            await _system_status(mock_client)
        assert "401" in str(exc_info.value)


class TestSystemFirmwareStatus:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {
            "status": "ok",
            "product_version": "24.7",
            "product_latest": "24.7",
            "updates": 0,
        }
        result = await _system_firmware_status(mock_client)
        mock_client.get.assert_called_once_with("firmware/status/check")
        assert result["product_version"] == "24.7"

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.get.side_effect = OPNsenseAPIError(
            status_code=503,
            body={},
            path="firmware/status/check",
            method="GET",
        )
        with pytest.raises(ToolError) as exc_info:
            await _system_firmware_status(mock_client)
        assert "503" in str(exc_info.value)


class TestSystemConfigBackup:
    async def test_returns_raw_xml_string(self, mock_client: AsyncMock) -> None:
        xml = '<?xml version="1.0"?><opnsense/>'
        mock_client.get_text.return_value = xml
        result = await _system_config_backup(mock_client)
        mock_client.get_text.assert_called_once_with("core/backup/download/this")
        assert result == xml

    async def test_result_is_string_not_dict(self, mock_client: AsyncMock) -> None:
        mock_client.get_text.return_value = "<root/>"
        result = await _system_config_backup(mock_client)
        assert isinstance(result, str)

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.get_text.side_effect = OPNsenseAPIError(
            status_code=403,
            body={"message": "Forbidden"},
            path="core/backup/download/this",
            method="GET",
        )
        with pytest.raises(ToolError) as exc_info:
            await _system_config_backup(mock_client)
        assert "403" in str(exc_info.value)
