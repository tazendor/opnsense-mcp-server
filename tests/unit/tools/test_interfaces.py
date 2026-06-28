from unittest.mock import AsyncMock

from opnsense_mcp.tools.interfaces import (
    _interface_arp_table,
    _interface_config,
    _interface_list,
    _interface_ndp_table,
)


class TestInterfaceList:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"em0": "WAN", "em1": "LAN"}
        result = await _interface_list(mock_client)
        mock_client.get.assert_called_once_with(
            "diagnostics/interface/getInterfaceNames"
        )
        assert result == {"em0": "WAN", "em1": "LAN"}

    async def test_returns_response_unchanged(self, mock_client: AsyncMock) -> None:
        payload = {"em0": "WAN", "em1": "LAN", "em2": "OPT1"}
        mock_client.get.return_value = payload
        assert await _interface_list(mock_client) == payload


class TestInterfaceConfig:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        payload = {"em0": {"ipaddr": "203.0.113.1", "macaddr": "aa:bb:cc:dd:ee:ff"}}
        mock_client.get.return_value = payload
        result = await _interface_config(mock_client)
        mock_client.get.assert_called_once_with(
            "diagnostics/interface/getInterfaceConfig"
        )
        assert result == payload

    async def test_returns_response_unchanged(self, mock_client: AsyncMock) -> None:
        payload = {"em1": {"ipaddr": "192.168.1.1", "subnet": "24"}}
        mock_client.get.return_value = payload
        assert await _interface_config(mock_client) == payload


class TestInterfaceArpTable:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        entries = [{"ip": "192.168.1.2", "mac": "aa:bb:cc:dd:ee:ff", "intf": "em1"}]
        mock_client.get_list.return_value = entries
        result = await _interface_arp_table(mock_client)
        mock_client.get_list.assert_called_once_with("diagnostics/interface/getArp")
        assert result == entries

    async def test_returns_response_unchanged(self, mock_client: AsyncMock) -> None:
        payload = [{"ip": "10.0.0.1", "mac": "ff:ee:dd:cc:bb:aa", "intf": "em0"}]
        mock_client.get_list.return_value = payload
        assert await _interface_arp_table(mock_client) == payload


class TestInterfaceNdpTable:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        entries = [{"ipv6": "fe80::1", "mac": "aa:bb:cc:dd:ee:ff", "intf": "em1"}]
        mock_client.get_list.return_value = entries
        result = await _interface_ndp_table(mock_client)
        mock_client.get_list.assert_called_once_with("diagnostics/interface/getNdp")
        assert result == entries

    async def test_returns_response_unchanged(self, mock_client: AsyncMock) -> None:
        payload = [{"ipv6": "::1", "mac": "00:00:00:00:00:01", "intf": "lo0"}]
        mock_client.get_list.return_value = payload
        assert await _interface_ndp_table(mock_client) == payload
