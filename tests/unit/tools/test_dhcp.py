from unittest.mock import AsyncMock

from opnsense_mcp.tools.dhcp import (
    _dhcp_lease_list,
    _dhcp_settings_get,
    _dhcp_static_list,
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
            "dhcpv4/leases/searchLease",
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
        mock_client.get.assert_called_once_with("dhcpv4/settings/get")
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
        mock_client.get.assert_called_once_with("dhcpv4/settings/searchStaticMap")
        assert "rows" in result

    async def test_returns_response_unchanged(self, mock_client: AsyncMock) -> None:
        payload = {"rows": [], "total": 0}
        mock_client.get.return_value = payload
        assert await _dhcp_static_list(mock_client) == payload
