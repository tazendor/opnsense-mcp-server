from unittest.mock import AsyncMock

import pytest

from opnsense_mcp.errors import OPNsenseAPIError, ToolError
from opnsense_mcp.tools.dns import (
    _dns_apply,
    _dns_host_override_add,
    _dns_host_override_delete,
    _dns_host_override_list,
    _dns_host_override_update,
    _dns_settings_get,
)

UUID_DNS = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
INVALID_UUID = "not-a-uuid"


class TestDnsSettingsGet:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"unbound": {"general": {}}}
        result = await _dns_settings_get(mock_client)
        mock_client.get.assert_called_once_with("unbound/settings/get")
        assert "unbound" in result

    async def test_returns_response_unchanged(self, mock_client: AsyncMock) -> None:
        payload = {"unbound": {"general": {"enabled": "1"}}}
        mock_client.get.return_value = payload
        assert await _dns_settings_get(mock_client) == payload


class TestDnsHostOverrideList:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"rows": [], "total": 0}
        await _dns_host_override_list(mock_client)
        mock_client.get.assert_called_once_with("unbound/settings/searchHostOverride")

    async def test_returns_rows(self, mock_client: AsyncMock) -> None:
        rows = [{"uuid": UUID_DNS, "host": "myhost", "domain": "example.com"}]
        mock_client.get.return_value = {"rows": rows, "total": 1}
        result = await _dns_host_override_list(mock_client)
        assert result["rows"] == rows

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.get.side_effect = OPNsenseAPIError(
            status_code=500,
            body={},
            path="unbound/settings/searchHostOverride",
            method="GET",
        )
        with pytest.raises(ToolError) as exc_info:
            await _dns_host_override_list(mock_client)
        assert "500" in str(exc_info.value)


class TestDnsHostOverrideAdd:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        host = {
            "host": "myhost",
            "domain": "example.com",
            "rr": "A",
            "server": "1.2.3.4",
        }
        mock_client.post.return_value = {"result": "saved", "uuid": UUID_DNS}
        await _dns_host_override_add(mock_client, host=host)
        mock_client.post.assert_called_once_with(
            "unbound/settings/addHostOverride", {"host": host}
        )

    async def test_returns_uuid(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved", "uuid": UUID_DNS}
        result = await _dns_host_override_add(
            mock_client,
            host={"host": "x", "domain": "example.com", "rr": "A", "server": "1.1.1.1"},
        )
        assert result["uuid"] == UUID_DNS

    async def test_validation_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.side_effect = OPNsenseAPIError(
            status_code=400,
            body={"validations": {"host.server": "Invalid IP"}},
            path="unbound/settings/addHostOverride",
            method="POST",
        )
        with pytest.raises(ToolError) as exc_info:
            await _dns_host_override_add(
                mock_client,
                host={"host": "x", "domain": "example.com", "rr": "A", "server": "bad"},
            )
        assert "400" in str(exc_info.value)


class TestDnsHostOverrideUpdate:
    async def test_calls_endpoint_with_uuid(self, mock_client: AsyncMock) -> None:
        host = {"server": "5.6.7.8"}
        mock_client.post.return_value = {"result": "saved"}
        await _dns_host_override_update(mock_client, uuid=UUID_DNS, host=host)
        mock_client.post.assert_called_once_with(
            f"unbound/settings/setHostOverride/{UUID_DNS}", {"host": host}
        )

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.side_effect = OPNsenseAPIError(
            status_code=404,
            body={},
            path=f"unbound/settings/setHostOverride/{UUID_DNS}",
            method="POST",
        )
        with pytest.raises(ToolError):
            await _dns_host_override_update(mock_client, uuid=UUID_DNS, host={})

    async def test_invalid_uuid_raises_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        with pytest.raises(ToolError, match="Invalid UUID"):
            await _dns_host_override_update(mock_client, uuid=INVALID_UUID, host={})
        mock_client.post.assert_not_called()


class TestDnsHostOverrideDelete:
    async def test_calls_endpoint_with_uuid(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "deleted"}
        result = await _dns_host_override_delete(mock_client, uuid=UUID_DNS)
        mock_client.post.assert_called_once_with(
            f"unbound/settings/delHostOverride/{UUID_DNS}", None
        )
        assert result["result"] == "deleted"

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.side_effect = OPNsenseAPIError(
            status_code=404,
            body={},
            path=f"unbound/settings/delHostOverride/{UUID_DNS}",
            method="POST",
        )
        with pytest.raises(ToolError):
            await _dns_host_override_delete(mock_client, uuid=UUID_DNS)

    async def test_invalid_uuid_raises_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        with pytest.raises(ToolError, match="Invalid UUID"):
            await _dns_host_override_delete(mock_client, uuid=INVALID_UUID)
        mock_client.post.assert_not_called()


class TestDnsApply:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"status": "ok"}
        result = await _dns_apply(mock_client)
        mock_client.post.assert_called_once_with("unbound/service/reconfigure", None)
        assert result["status"] == "ok"
