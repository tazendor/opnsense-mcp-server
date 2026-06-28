"""End-to-end server wiring tests — catches client lifecycle bugs."""

import httpx
import pytest
import respx

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.config import Config
from opnsense_mcp.server import create_server
from opnsense_mcp.tools.system import _system_status


@pytest.fixture
def server_config() -> Config:
    return Config(url="https://opnsense.test", api_key="k", api_secret="s")


class TestClientLazyInit:
    @respx.mock
    async def test_client_works_without_async_context_manager(
        self, server_config: Config
    ) -> None:
        """Regression: client must not require async with before first call.

        Without lazy init, OPNsenseClient._client raises RuntimeError when
        create_server creates the client without entering the async context manager.
        """
        respx.get("https://opnsense.test/api/core/dashboard/get").mock(
            return_value=httpx.Response(200, json={"versions": {"product": "24.7"}})
        )
        client = OPNsenseClient(server_config)
        result = await _system_status(client)
        assert "versions" in result

    @respx.mock
    async def test_create_server_tool_calls_reach_opnsense(
        self, server_config: Config
    ) -> None:
        """Tool registered via create_server makes real HTTP calls end-to-end."""
        respx.get("https://opnsense.test/api/core/dashboard/get").mock(
            return_value=httpx.Response(200, json={"versions": {"product": "24.7"}})
        )
        mcp = create_server(server_config)
        tool_fn = mcp._tool_manager._tools["system_status"].fn
        result = await tool_fn()
        assert isinstance(result, dict)
        assert "versions" in result


class TestServerWiring:
    def test_all_42_tools_registered(self, server_config: Config) -> None:
        mcp = create_server(server_config)
        assert len(mcp._tool_manager._tools) == 42

    def test_tool_names_are_unique(self, server_config: Config) -> None:
        mcp = create_server(server_config)
        names = list(mcp._tool_manager._tools.keys())
        assert len(names) == len(set(names))
