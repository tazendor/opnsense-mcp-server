"""Representative IPsec tests. The contract-completeness scanner separately guarantees
all 50 IPsec tools are registered and documented; these cover behavior by group."""

from unittest.mock import AsyncMock

import pytest
from mcp.server.fastmcp import FastMCP

from opnsense_mcp.confirmation import PendingOperationStore
from opnsense_mcp.errors import ToolError
from opnsense_mcp.tools import ipsec

UUID = "12345678-1234-1234-1234-123456789abc"


def _fn(mock_client: AsyncMock, name: str):  # type: ignore[no-untyped-def]
    mcp = FastMCP("t")
    ipsec.register_tools(mcp, mock_client, PendingOperationStore())
    return mcp._tool_manager._tools[name].fn


def _fn_with_store(mock_client: AsyncMock, store: PendingOperationStore, name: str):  # type: ignore[no-untyped-def]
    mcp = FastMCP("t")
    ipsec.register_tools(mcp, mock_client, store)
    return mcp._tool_manager._tools[name].fn


class TestConnectionCrud:
    async def test_list_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"rows": []}
        await _fn(mock_client, "ipsec_connection_list")()
        mock_client.get.assert_called_once_with("ipsec/connections/search_connection")

    async def test_add_wraps_body(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved"}
        await _fn(mock_client, "ipsec_connection_add")({"version": "2"})
        mock_client.post.assert_called_once_with(
            "ipsec/connections/add_connection", {"connection": {"version": "2"}}
        )


class TestChildCrudViaFactory:
    async def test_child_add_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved"}
        await _fn(mock_client, "ipsec_child_add")({"local_ts": "10.0.0.0/24"})
        mock_client.post.assert_called_once_with(
            "ipsec/connections/add_child", {"child": {"local_ts": "10.0.0.0/24"}}
        )

    async def test_child_delete_validates_uuid(self, mock_client: AsyncMock) -> None:
        with pytest.raises(ToolError):
            await _fn(mock_client, "ipsec_child_delete")("bad")


class TestRedaction:
    async def test_keypair_list_redacts_privatekey(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.get.return_value = {"rows": [{"name": "k", "privateKey": "S"}]}
        result = await _fn(mock_client, "ipsec_keypair_list")()
        assert "privateKey" not in result["rows"][0]

    async def test_psk_get_redacts_key(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"preSharedKey": {"ident": "a", "Key": "S"}}
        result = await _fn(mock_client, "ipsec_psk_get")(UUID)
        assert "Key" not in result["preSharedKey"]

    async def test_keypair_generate_not_redacted(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"privateKey": "FRESH", "publicKey": "PUB"}
        result = await _fn(mock_client, "ipsec_keypair_generate")("rsa", "2048")
        assert result["privateKey"] == "FRESH"
        mock_client.get.assert_called_once_with("ipsec/key_pairs/gen_key_pair/rsa/2048")


class TestHighRiskGating:
    async def test_connection_delete_preview_no_post(
        self, mock_client: AsyncMock
    ) -> None:
        store = PendingOperationStore()
        fn = _fn_with_store(mock_client, store, "ipsec_connection_delete")
        result = await fn(uuid=UUID)
        assert result["status"] == "confirmation_required"
        mock_client.post.assert_not_called()

    async def test_connection_delete_confirmed_posts_once(
        self, mock_client: AsyncMock
    ) -> None:
        store = PendingOperationStore()
        fn = _fn_with_store(mock_client, store, "ipsec_connection_delete")
        preview = await fn(uuid=UUID)
        mock_client.post.return_value = {"result": "deleted"}
        await fn(uuid=UUID, confirm=preview["confirm_token"])
        mock_client.post.assert_called_once_with(
            f"ipsec/connections/del_connection/{UUID}",
            None,
            token=preview["confirm_token"],
        )

    async def test_enabled_toggle_gated(self, mock_client: AsyncMock) -> None:
        store = PendingOperationStore()
        fn = _fn_with_store(mock_client, store, "ipsec_enabled_toggle")
        result = await fn()
        assert result["status"] == "confirmation_required"
        mock_client.post.assert_not_called()


class TestSessionAndApply:
    async def test_session_list_phase2(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"rows": []}
        await _fn(mock_client, "ipsec_session_list")(phase=2)
        mock_client.get.assert_called_once_with("ipsec/sessions/search_phase2")

    async def test_apply(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"status": "ok"}
        await _fn(mock_client, "ipsec_apply")()
        mock_client.post.assert_called_once_with("ipsec/service/reconfigure", None)
