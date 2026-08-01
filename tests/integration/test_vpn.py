"""US3 VPN integration tests — require a live OPNsense instance (auto-skipped without a
config). Write cycles additionally require OPNSENSE_INTEGRATION_WRITES=1 so they can
never mutate a live box by accident. Endpoint casing follows docs.opnsense.org; confirm
against the instance and adjust if rejected."""

import pytest

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.confirmation import PendingOperationStore
from opnsense_mcp.tools import ipsec, openvpn, wireguard

_STORE = PendingOperationStore()


def _tool(module, mock_or_client, name):  # type: ignore[no-untyped-def]
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("t")
    module.register_tools(mcp, mock_or_client, _STORE)
    return mcp._tool_manager._tools[name].fn


@pytest.mark.integration
class TestVpnReads:
    async def test_openvpn_instances(self, live_client: OPNsenseClient) -> None:
        result = await _tool(openvpn, live_client, "openvpn_instance_list")()
        assert "rows" in result

    async def test_openvpn_sessions(self, live_client: OPNsenseClient) -> None:
        result = await _tool(openvpn, live_client, "openvpn_session_list")()
        assert isinstance(result, dict)

    async def test_ipsec_connections(self, live_client: OPNsenseClient) -> None:
        result = await _tool(ipsec, live_client, "ipsec_connection_list")()
        assert "rows" in result

    async def test_wireguard_servers_redacted(
        self, live_client: OPNsenseClient
    ) -> None:
        result = await _tool(wireguard, live_client, "wireguard_server_list")()
        for row in result.get("rows", []):
            assert "privkey" not in row  # FR-017 holds against the live API


@pytest.mark.integration
class TestWireguardPeerWriteCycle:
    async def test_add_apply_list_remove(
        self, live_client: OPNsenseClient, require_write_optin: None
    ) -> None:
        servers = await _tool(wireguard, live_client, "wireguard_server_list")()
        rows = servers.get("rows", [])
        if not rows:
            pytest.skip("no WireGuard server configured to attach a peer to")

        gen = await _tool(wireguard, live_client, "wireguard_client_psk_generate")()
        peer = {
            "name": "opnsense-mcp-integration-peer",
            "pubkey": "0" * 43 + "=",  # placeholder; adjust if the API validates it
            "psk": gen.get("psk", ""),
            "tunneladdress": "192.0.2.240/32",
        }
        added = await _tool(wireguard, live_client, "wireguard_client_add")(peer)
        uuid = added.get("uuid")
        assert added.get("result") == "saved" and uuid
        try:
            await _tool(wireguard, live_client, "wireguard_apply")()
            listing = await _tool(wireguard, live_client, "wireguard_client_list")()
            names = [r.get("name") for r in listing.get("rows", [])]
            assert "opnsense-mcp-integration-peer" in names
        finally:
            await _tool(wireguard, live_client, "wireguard_client_delete")(uuid)
            await _tool(wireguard, live_client, "wireguard_apply")()
