from unittest.mock import AsyncMock

import pytest

from opnsense_mcp.errors import OPNsenseAPIError, ToolError
from opnsense_mcp.tools.routes import (
    _route_add,
    _route_apply,
    _route_delete,
    _route_list,
    _route_update,
)


class TestRouteList:
    async def test_calls_post_with_default_payload(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.return_value = {
            "rows": [],
            "rowCount": 0,
            "total": 0,
            "current": 1,
        }
        await _route_list(mock_client)
        mock_client.post.assert_called_once_with(
            "routes/routes/searchroute",
            {"current": 1, "rowCount": -1, "searchPhrase": ""},
        )

    async def test_returns_rows(self, mock_client: AsyncMock) -> None:
        rows = [{"uuid": "r1", "network": "10.0.0.0/8", "gateway": "GW_WAN"}]
        mock_client.post.return_value = {"rows": rows, "total": 1, "current": 1}
        result = await _route_list(mock_client)
        assert result["rows"] == rows

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.side_effect = OPNsenseAPIError(
            status_code=500, body={}, path="routes/routes/searchroute", method="POST"
        )
        with pytest.raises(ToolError) as exc_info:
            await _route_list(mock_client)
        assert "500" in str(exc_info.value)


class TestRouteAdd:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        route = {"network": "192.168.100.0/24", "gateway": "GW_LAN"}
        mock_client.post.return_value = {"result": "saved", "uuid": "new-route-uuid"}
        await _route_add(mock_client, route=route)
        mock_client.post.assert_called_once_with(
            "routes/routes/addroute", {"route": route}
        )

    async def test_returns_uuid(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved", "uuid": "new-route-uuid"}
        result = await _route_add(
            mock_client, route={"network": "10.0.0.0/8", "gateway": "GW_WAN"}
        )
        assert result["uuid"] == "new-route-uuid"

    async def test_validation_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.side_effect = OPNsenseAPIError(
            status_code=400,
            body={"validations": {"route.network": "Invalid network"}},
            path="routes/routes/addroute",
            method="POST",
        )
        with pytest.raises(ToolError) as exc_info:
            await _route_add(mock_client, route={"network": "bad", "gateway": "GW_WAN"})
        assert "400" in str(exc_info.value)


class TestRouteUpdate:
    async def test_calls_endpoint_with_uuid(self, mock_client: AsyncMock) -> None:
        route = {"descr": "updated description"}
        mock_client.post.return_value = {"result": "saved"}
        await _route_update(mock_client, uuid="route-uuid-1", route=route)
        mock_client.post.assert_called_once_with(
            "routes/routes/setroute/route-uuid-1", {"route": route}
        )

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.side_effect = OPNsenseAPIError(
            status_code=404, body={}, path="routes/routes/setroute/bad", method="POST"
        )
        with pytest.raises(ToolError):
            await _route_update(mock_client, uuid="bad", route={})


class TestRouteDelete:
    async def test_calls_endpoint_with_uuid(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "deleted"}
        result = await _route_delete(mock_client, uuid="route-uuid-1")
        mock_client.post.assert_called_once_with(
            "routes/routes/delroute/route-uuid-1", None
        )
        assert result["result"] == "deleted"

    async def test_api_error_surfaced_as_tool_error(
        self, mock_client: AsyncMock
    ) -> None:
        mock_client.post.side_effect = OPNsenseAPIError(
            status_code=404, body={}, path="routes/routes/delroute/bad", method="POST"
        )
        with pytest.raises(ToolError):
            await _route_delete(mock_client, uuid="bad")


class TestRouteApply:
    async def test_calls_correct_endpoint(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"status": "ok"}
        result = await _route_apply(mock_client)
        mock_client.post.assert_called_once_with("routes/routes/reconfigure", None)
        assert result["status"] == "ok"
