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
            "api_version": "1",
            "connection": "ok",
            "downgrade_packages": [],
            "download_size": "",
            "last_check": "Mon Jan  1 00:00:00 UTC 2026",
        }
        result = await _system_firmware_status(mock_client)
        mock_client.get.assert_called_once_with("core/firmware/status")
        assert "last_check" in result

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.get.side_effect = OPNsenseAPIError(
            status_code=503,
            body={},
            path="core/firmware/status",
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


class TestSystemHighRisk:
    """FR-018: reboot/halt/firmware/config-restore are confirmation-gated.
    The scanner separately confirms all 12 system tools are documented."""

    @staticmethod
    def _fn(mock_client: AsyncMock, name: str, store: object):  # type: ignore[no-untyped-def]
        from mcp.server.fastmcp import FastMCP

        from opnsense_mcp.tools import system

        mcp = FastMCP("t")
        system.register_tools(mcp, mock_client, store)
        return mcp._tool_manager._tools[name].fn

    async def test_reboot_preview_no_post(self, mock_client: AsyncMock) -> None:
        from opnsense_mcp.confirmation import PendingOperationStore

        fn = self._fn(mock_client, "system_reboot", PendingOperationStore())
        result = await fn()
        assert result["status"] == "confirmation_required"
        mock_client.post.assert_not_called()

    async def test_reboot_confirmed_posts_once(self, mock_client: AsyncMock) -> None:
        from opnsense_mcp.confirmation import PendingOperationStore

        store = PendingOperationStore()
        fn = self._fn(mock_client, "system_reboot", store)
        preview = await fn()
        mock_client.post.return_value = {"status": "ok"}
        await fn(confirm=preview["confirm_token"])
        mock_client.post.assert_called_once_with(
            "core/system/reboot", None, token=preview["confirm_token"]
        )

    async def test_config_restore_gated_and_scoped(
        self, mock_client: AsyncMock
    ) -> None:
        from opnsense_mcp.confirmation import PendingOperationStore

        store = PendingOperationStore()
        fn = self._fn(mock_client, "system_config_restore", store)
        result = await fn(backup="config-2026.xml")
        assert result["status"] == "confirmation_required"
        assert "config-2026.xml" in result["description"]
        mock_client.post.assert_not_called()

    async def test_firmware_check_is_standard(self, mock_client: AsyncMock) -> None:
        from opnsense_mcp.confirmation import PendingOperationStore

        mock_client.post.return_value = {"status": "ok"}
        fn = self._fn(mock_client, "system_firmware_check", PendingOperationStore())
        await fn()
        mock_client.post.assert_called_once_with("core/firmware/check", None)
