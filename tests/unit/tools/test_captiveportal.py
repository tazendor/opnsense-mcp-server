"""Representative Captive Portal tests.

The contract scanner separately guarantees all 15 tools are registered/documented."""

from unittest.mock import AsyncMock

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.confirmation import PendingOperationStore
from opnsense_mcp.tools import captiveportal


def _fn(mock_client: AsyncMock, name: str, store: PendingOperationStore | None = None):  # type: ignore[no-untyped-def]
    mcp = FastMCP("t")
    captiveportal.register_tools(mcp, mock_client, store or PendingOperationStore())
    return mcp._tool_manager._tools[name].fn


class TestZones:
    async def test_add_wraps_zone(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved"}
        await _fn(mock_client, "captiveportal_zone_add")({"description": "guest"})
        mock_client.post.assert_called_once_with(
            "captiveportal/settings/add_zone", {"zone": {"description": "guest"}}
        )


class TestSessions:
    async def test_session_list_by_zone(self, mock_client: AsyncMock) -> None:
        mock_client.get_list.return_value = [{"sessionId": "s1"}]
        result = await _fn(mock_client, "captiveportal_session_list")("0")
        mock_client.get_list.assert_called_once_with("captiveportal/session/list/0")
        assert result[0]["sessionId"] == "s1"

    async def test_single_disconnect_proceeds_directly(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.return_value = {"result": "ok"}
        await _fn(mock_client, "captiveportal_session_disconnect")("0", "s1")
        mock_client.post.assert_called_once_with(
            "captiveportal/session/disconnect/0", {"sessionId": "s1"}
        )


class TestZoneDisconnectHighRisk:
    async def test_preview_reads_sessions_no_disconnect(
        self, mock_client: AsyncMock
    ) -> None:
        store = PendingOperationStore()
        mock_client.get_list.return_value = [{"sessionId": "s1"}, {"sessionId": "s2"}]
        fn = _fn(mock_client, "captiveportal_session_disconnect_zone", store)
        result = await fn(zone_id="0")
        assert result["status"] == "confirmation_required"
        assert "2" in result["description"]
        mock_client.post.assert_not_called()  # no disconnect POST during preview

    async def test_confirmed_fans_out_one_post_per_session(
        self, mock_client: AsyncMock
    ) -> None:
        store = PendingOperationStore()
        mock_client.get_list.return_value = [{"sessionId": "s1"}, {"sessionId": "s2"}]
        fn = _fn(mock_client, "captiveportal_session_disconnect_zone", store)
        preview = await fn(zone_id="0")
        mock_client.post.return_value = {"result": "ok"}
        result = await fn(zone_id="0", confirm=preview["confirm_token"])
        assert result["disconnected"] == ["s1", "s2"]
        assert mock_client.post.call_count == 2


class TestApply:
    async def test_apply(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"status": "ok"}
        await _fn(mock_client, "captiveportal_apply")()
        mock_client.post.assert_called_once_with(
            "captiveportal/service/reconfigure", None
        )
