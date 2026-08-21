"""Representative Web Proxy tests; scanner guarantees all 28 tools are documented."""

from unittest.mock import AsyncMock

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.tools import proxy


def _fn(mock_client: AsyncMock, name: str):  # type: ignore[no-untyped-def]
    mcp = FastMCP("t")
    proxy.register_tools(mcp, mock_client)
    return mcp._tool_manager._tools[name].fn


class TestSettings:
    async def test_get(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"proxy": {}}
        await _fn(mock_client, "proxy_settings_get")()
        mock_client.get.assert_called_once_with("proxy/settings/get")

    async def test_update_wraps_proxy(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved"}
        await _fn(mock_client, "proxy_settings_update")({"forward": {}})
        mock_client.post.assert_called_once_with(
            "proxy/settings/set", {"proxy": {"forward": {}}}
        )


class TestBlacklistRedaction:
    async def test_list_redacts_password(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {
            "rows": [{"name": "feed", "password": "SECRET"}]
        }
        result = await _fn(mock_client, "proxy_remote_blacklist_list")()
        assert "password" not in result["rows"][0]


class TestPacFactory:
    async def test_pac_rule_add(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "saved"}
        await _fn(mock_client, "proxy_pac_rule_add")({"description": "r"})
        mock_client.post.assert_called_once_with(
            "proxy/settings/add_pac_rule", {"rule": {"description": "r"}}
        )

    async def test_pac_match_list(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"rows": []}
        await _fn(mock_client, "proxy_pac_match_list")()
        mock_client.get.assert_called_once_with("proxy/settings/search_pac_match")


class TestServiceApply:
    async def test_reset(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"result": "ok"}
        await _fn(mock_client, "proxy_service_reset")()
        mock_client.post.assert_called_once_with("proxy/service/reset", None)

    async def test_apply(self, mock_client: AsyncMock) -> None:
        mock_client.post.return_value = {"status": "ok"}
        await _fn(mock_client, "proxy_apply")()
        mock_client.post.assert_called_once_with("proxy/service/reconfigure", None)
