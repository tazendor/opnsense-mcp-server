"""Representative WireGuard tests. The contract scanner guarantees all 24 tools are
registered/documented; these cover endpoints, redaction, and gating by group."""

from unittest.mock import AsyncMock

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.confirmation import PendingOperationStore
from opnsense_mcp.tools import wireguard

UUID = "12345678-1234-1234-1234-123456789abc"


def _fn(mock_client: AsyncMock, name: str, store: PendingOperationStore | None = None):  # type: ignore[no-untyped-def]
    mcp = FastMCP("t")
    wireguard.register_tools(mcp, mock_client, store or PendingOperationStore())
    return mcp._tool_manager._tools[name].fn


class TestServer:
    async def test_add_wraps_body(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved"}
        await _fn(mock_client, "wireguard_server_add")({"name": "wg0"})
        mock_client.post.assert_called_once_with(
            "wireguard/server/add_server", {"server": {"name": "wg0"}}
        )

    async def test_list_redacts_privkey(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"rows": [{"name": "wg0", "privkey": "S"}]}
        result = await _fn(mock_client, "wireguard_server_list")()
        assert "privkey" not in result["rows"][0]

    async def test_keypair_generate_not_redacted(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"privkey": "FRESH", "pubkey": "PUB"}
        result = await _fn(mock_client, "wireguard_server_keypair_generate")()
        assert result["privkey"] == "FRESH"


class TestClient:
    async def test_get_redacts_psk(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"client": {"name": "p", "psk": "S"}}
        result = await _fn(mock_client, "wireguard_client_get")(UUID)
        assert "psk" not in result["client"]

    async def test_add_uses_client_wrapper(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved"}
        await _fn(mock_client, "wireguard_client_add")({"pubkey": "PUB"})
        mock_client.post.assert_called_once_with(
            "wireguard/client/add_client", {"client": {"pubkey": "PUB"}}
        )

    async def test_client_delete_is_standard(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "deleted"}
        result = await _fn(mock_client, "wireguard_client_delete")(UUID)
        assert result == {"result": "deleted"}
        mock_client.post.assert_called_once_with(
            f"wireguard/client/del_client/{UUID}", None
        )


class TestServerDeleteHighRisk:
    async def test_preview_no_post(self, mock_client: AsyncMock) -> None:
        store = PendingOperationStore()
        fn = _fn(mock_client, "wireguard_server_delete", store)
        result = await fn(uuid=UUID)
        assert result["status"] == "confirmation_required"
        mock_client.post.assert_not_called()

    async def test_confirm_posts_once(self, mock_client: AsyncMock) -> None:
        store = PendingOperationStore()
        fn = _fn(mock_client, "wireguard_server_delete", store)
        preview = await fn(uuid=UUID)
        mock_client.post.return_value = {"result": "deleted"}
        await fn(uuid=UUID, confirm=preview["confirm_token"])
        mock_client.post.assert_called_once_with(
            f"wireguard/server/del_server/{UUID}",
            None,
            token=preview["confirm_token"],
        )


class TestStatusAndApply:
    async def test_status_show(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"rows": []}
        await _fn(mock_client, "wireguard_status")()
        mock_client.get.assert_called_once_with("wireguard/service/show")

    async def test_apply(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"status": "ok"}
        await _fn(mock_client, "wireguard_apply")()
        mock_client.post.assert_called_once_with("wireguard/service/reconfigure", None)
