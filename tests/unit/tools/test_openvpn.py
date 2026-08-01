from unittest.mock import AsyncMock

import pytest
from mcp.server.fastmcp import FastMCP

from opnsense_mcp.confirmation import PendingOperationStore
from opnsense_mcp.errors import OPNsenseAPIError, ToolError
from opnsense_mcp.tools import openvpn
from opnsense_mcp.tools.openvpn import (
    _openvpn_apply,
    _openvpn_instance_add,
    _openvpn_instance_list,
    _openvpn_instance_update,
    _openvpn_static_key_generate,
    _openvpn_static_key_get,
    _openvpn_static_key_list,
)

UUID = "12345678-1234-1234-1234-123456789abc"


def _tool_fn(store: PendingOperationStore, mock_client: AsyncMock, name: str):  # type: ignore[no-untyped-def]
    mcp = FastMCP("t")
    openvpn.register_tools(mcp, mock_client, store)
    return mcp._tool_manager._tools[name].fn


class TestInstances:
    async def test_list_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"rows": [], "total": 0}
        await _openvpn_instance_list(mock_client)
        mock_client.get.assert_called_once_with("openvpn/instances/search")

    async def test_add_wraps_instance(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved", "uuid": UUID}
        await _openvpn_instance_add(mock_client, {"role": "server"})
        mock_client.post.assert_called_once_with(
            "openvpn/instances/add", {"instance": {"role": "server"}}
        )

    async def test_update_validates_uuid(self, mock_client: AsyncMock) -> None:
        with pytest.raises(ToolError):
            await _openvpn_instance_update(mock_client, "bad", {})
        mock_client.post.assert_not_called()

    async def test_api_error_wrapped(self, mock_client: AsyncMock) -> None:
        mock_client.get.side_effect = OPNsenseAPIError(
            status_code=500, body={}, path="openvpn/instances/search", method="GET"
        )
        with pytest.raises(ToolError):
            await _openvpn_instance_list(mock_client)


class TestStaticKeyRedaction:
    async def test_list_redacts_key(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {
            "rows": [{"mode": "crypt", "key": "SECRET"}],
            "total": 1,
        }
        result = await _openvpn_static_key_list(mock_client)
        assert result["rows"][0].get("key") is None
        assert result["rows"][0]["mode"] == "crypt"

    async def test_get_redacts_key(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {
            "statickey": {"mode": "crypt", "key": "SECRET", "description": "d"}
        }
        result = await _openvpn_static_key_get(mock_client, UUID)
        assert "key" not in result["statickey"]
        assert result["statickey"]["description"] == "d"

    async def test_generate_not_redacted(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"key": "FRESH-GENERATED-MATERIAL"}
        result = await _openvpn_static_key_generate(mock_client, "tls-crypt")
        assert result["key"] == "FRESH-GENERATED-MATERIAL"
        mock_client.get.assert_called_once_with("openvpn/instances/gen_key/tls-crypt")


class TestApply:
    async def test_apply_reconfigures(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"status": "ok"}
        await _openvpn_apply(mock_client)
        mock_client.post.assert_called_once_with("openvpn/service/reconfigure", None)


class TestInstanceDeleteHighRisk:
    async def test_preview_makes_no_post(self, mock_client: AsyncMock) -> None:
        store = PendingOperationStore()
        fn = _tool_fn(store, mock_client, "openvpn_instance_delete")
        result = await fn(uuid=UUID)
        assert result["status"] == "confirmation_required"
        assert result["confirm_token"]
        mock_client.post.assert_not_called()
        mock_client.log_preview.assert_called_once()

    async def test_confirm_posts_delete_once(self, mock_client: AsyncMock) -> None:
        store = PendingOperationStore()
        fn = _tool_fn(store, mock_client, "openvpn_instance_delete")
        preview = await fn(uuid=UUID)
        mock_client.post.return_value = {"result": "deleted"}
        result = await fn(uuid=UUID, confirm=preview["confirm_token"])
        assert result == {"result": "deleted"}
        mock_client.post.assert_called_once_with(
            f"openvpn/instances/del/{UUID}", None, token=preview["confirm_token"]
        )

    async def test_bad_token_rejected(self, mock_client: AsyncMock) -> None:
        store = PendingOperationStore()
        fn = _tool_fn(store, mock_client, "openvpn_instance_delete")
        with pytest.raises(ToolError):
            await fn(uuid=UUID, confirm="not-a-real-token")
        mock_client.post.assert_not_called()
