from unittest.mock import AsyncMock

import pytest

from opnsense_mcp.errors import ToolError
from opnsense_mcp.tools.services import (
    SUPPORTED_MODULES,
    _service_restart,
    _service_start,
    _service_status,
    _service_stop,
)

VALID_MODULES = ["unbound", "dhcpv4", "firmware", "ids", "cron"]


class TestSupportedModules:
    def test_contains_all_required_modules(self) -> None:
        for module in VALID_MODULES:
            assert module in SUPPORTED_MODULES

    def test_is_frozenset(self) -> None:
        assert isinstance(SUPPORTED_MODULES, frozenset)


class TestServiceStatus:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"status": "running"}
        result = await _service_status(mock_client, module="unbound")
        mock_client.get.assert_called_once_with("unbound/service/status")
        assert result["status"] == "running"

    async def test_all_supported_modules_accepted(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"status": "running"}
        for module in VALID_MODULES:
            mock_client.get.reset_mock()
            await _service_status(mock_client, module=module)
            mock_client.get.assert_called_once_with(f"{module}/service/status")

    async def test_unknown_module_raises_tool_error_before_http(
        self, mock_client: AsyncMock
    ) -> None:
        with pytest.raises(ToolError):
            await _service_status(mock_client, module="unknown_service")
        mock_client.get.assert_not_called()


class TestServiceStart:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"response": "OK"}
        result = await _service_start(mock_client, module="dhcpv4")
        mock_client.post.assert_called_once_with("dhcpv4/service/start", None)
        assert result["response"] == "OK"

    async def test_unknown_module_raises_tool_error_before_http(
        self, mock_client: AsyncMock
    ) -> None:
        with pytest.raises(ToolError):
            await _service_start(mock_client, module="nginx")
        mock_client.post.assert_not_called()


class TestServiceStop:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"response": "OK"}
        result = await _service_stop(mock_client, module="ids")
        mock_client.post.assert_called_once_with("ids/service/stop", None)
        assert result["response"] == "OK"

    async def test_unknown_module_raises_tool_error_before_http(
        self, mock_client: AsyncMock
    ) -> None:
        with pytest.raises(ToolError):
            await _service_stop(mock_client, module="apache")
        mock_client.post.assert_not_called()


class TestServiceRestart:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"response": "OK"}
        result = await _service_restart(mock_client, module="cron")
        mock_client.post.assert_called_once_with("cron/service/restart", None)
        assert result["response"] == "OK"

    async def test_all_supported_modules_accepted(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"response": "OK"}
        for module in VALID_MODULES:
            mock_client.post.reset_mock()
            await _service_restart(mock_client, module=module)
            mock_client.post.assert_called_once_with(f"{module}/service/restart", None)

    async def test_unknown_module_raises_tool_error_before_http(
        self, mock_client: AsyncMock
    ) -> None:
        with pytest.raises(ToolError):
            await _service_restart(mock_client, module="myservice")
        mock_client.post.assert_not_called()
