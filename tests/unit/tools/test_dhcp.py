from unittest.mock import AsyncMock

import pytest

from opnsense_mcp.errors import ToolError
from opnsense_mcp.tools.dhcp import (
    _dhcp_apply,
    _dhcp_lease_list,
    _dhcp_settings_get,
    _dhcp_settings_update,
    _dhcp_static_add,
    _dhcp_static_delete,
    _dhcp_static_list,
    _dhcp_static_update,
)


class TestDhcpLeaseList:
    async def test_calls_post_with_default_payload(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.return_value = {
            "rows": [{"address": "192.168.1.100", "mac": "aa:bb:cc:dd:ee:ff"}],
            "rowCount": 1,
            "total": 1,
            "current": 1,
        }
        await _dhcp_lease_list(mock_client)
        mock_client.post.assert_called_once_with(
            "kea/leases4/search",
            {"current": 1, "rowCount": -1, "searchPhrase": "", "inactive": 0},
        )

    async def test_returns_rows(self, mock_client: AsyncMock) -> None:
        rows = [{"address": "10.0.0.2", "mac": "bb:cc:dd:ee:ff:00"}]
        mock_client.post.return_value = {"rows": rows, "total": 1, "current": 1}
        result = await _dhcp_lease_list(mock_client)
        assert result["rows"] == rows

    async def test_returns_total(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"rows": [], "total": 0, "current": 1}
        result = await _dhcp_lease_list(mock_client)
        assert "total" in result


class TestDhcpSettingsGet:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"dhcp": {"lan": {"range": {}}}}
        result = await _dhcp_settings_get(mock_client)
        mock_client.get.assert_called_once_with("kea/dhcpv4/get")
        assert result == {"dhcp": {"lan": {"range": {}}}}

    async def test_returns_response_unchanged(self, mock_client: AsyncMock) -> None:
        payload = {"dhcp": {"opt1": {"range": {"from": "10.0.0.1"}}}}
        mock_client.get.return_value = payload
        assert await _dhcp_settings_get(mock_client) == payload


class TestDhcpStaticList:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {
            "rows": [{"mac": "aa:bb:cc:dd:ee:ff", "ipaddr": "192.168.1.10"}],
            "total": 1,
        }
        result = await _dhcp_static_list(mock_client)
        mock_client.get.assert_called_once_with("kea/dhcpv4/searchReservation")
        assert "rows" in result

    async def test_returns_response_unchanged(self, mock_client: AsyncMock) -> None:
        payload = {"rows": [], "total": 0}
        mock_client.get.return_value = payload
        assert await _dhcp_static_list(mock_client) == payload


class TestDhcpStaticAdd:
    async def test_posts_reservation(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved", "uuid": "new-uuid"}
        reservation = {
            "subnet": "subnet-uuid",
            "hw_address": "aa:bb:cc:dd:ee:ff",
            "ip_address": "192.168.1.50",
        }
        result = await _dhcp_static_add(mock_client, reservation)
        mock_client.post.assert_called_once_with(
            "kea/dhcpv4/add_reservation", {"reservation": reservation}
        )
        assert result["uuid"] == "new-uuid"

    async def test_wraps_api_error(self, mock_client: AsyncMock) -> None:
        from opnsense_mcp.errors import OPNsenseAPIError

        mock_client.post.side_effect = OPNsenseAPIError(
            status_code=400, body={}, path="kea/dhcpv4/add_reservation", method="POST"
        )
        with pytest.raises(ToolError):
            await _dhcp_static_add(mock_client, {"hw_address": "x"})


class TestDhcpStaticUpdate:
    async def test_posts_to_uuid_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved"}
        uuid = "12345678-1234-1234-1234-123456789abc"
        reservation = {"ip_address": "192.168.1.51"}
        await _dhcp_static_update(mock_client, uuid, reservation)
        mock_client.post.assert_called_once_with(
            f"kea/dhcpv4/set_reservation/{uuid}", {"reservation": reservation}
        )

    async def test_rejects_bad_uuid(self, mock_client: AsyncMock) -> None:
        with pytest.raises(ToolError):
            await _dhcp_static_update(mock_client, "not-a-uuid", {})
        mock_client.post.assert_not_called()


class TestDhcpStaticDelete:
    async def test_posts_to_uuid_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "deleted"}
        uuid = "12345678-1234-1234-1234-123456789abc"
        await _dhcp_static_delete(mock_client, uuid)
        mock_client.post.assert_called_once_with(
            f"kea/dhcpv4/del_reservation/{uuid}", None
        )

    async def test_rejects_bad_uuid(self, mock_client: AsyncMock) -> None:
        with pytest.raises(ToolError):
            await _dhcp_static_delete(mock_client, "bad")
        mock_client.post.assert_not_called()


class TestDhcpSettingsUpdate:
    async def test_posts_settings(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved"}
        settings = {"general": {"enabled": "1"}}
        await _dhcp_settings_update(mock_client, settings)
        mock_client.post.assert_called_once_with("kea/dhcpv4/set", {"dhcpv4": settings})


class TestDhcpApply:
    async def test_posts_reconfigure(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"status": "ok"}
        await _dhcp_apply(mock_client)
        mock_client.post.assert_called_once_with("kea/service/reconfigure", None)
