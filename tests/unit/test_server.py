"""End-to-end server wiring tests — catches client lifecycle bugs."""

import httpx
import pytest
import respx

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.config import Config
from opnsense_mcp.server import create_server
from opnsense_mcp.tools.system import _system_status

_STATUS_RESP = {"metadata": {"system": {"status": 2}}}


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
        respx.get("https://opnsense.test/api/core/system/status").mock(
            return_value=httpx.Response(200, json=_STATUS_RESP)
        )
        client = OPNsenseClient(server_config)
        result = await _system_status(client)
        assert "metadata" in result

    @respx.mock
    async def test_create_server_tool_calls_reach_opnsense(
        self, server_config: Config
    ) -> None:
        """Tool registered via create_server makes real HTTP calls end-to-end."""
        respx.get("https://opnsense.test/api/core/system/status").mock(
            return_value=httpx.Response(200, json=_STATUS_RESP)
        )
        mcp = create_server(server_config)
        tool_fn = mcp._tool_manager._tools["system_status"].fn
        result = await tool_fn()
        assert isinstance(result, dict)
        assert "metadata" in result


class TestClientShutdown:
    @respx.mock
    async def test_aclose_closes_http_client(self, server_config: Config) -> None:
        respx.get("https://opnsense.test/api/core/dashboard/get").mock(
            return_value=httpx.Response(200, json={})
        )
        client = OPNsenseClient(server_config)
        await client.get("core/dashboard/get")
        assert client._http is not None

        await client.aclose()

        assert client._http is None

    @respx.mock
    async def test_lifespan_closes_client_on_shutdown(
        self, server_config: Config
    ) -> None:
        client = OPNsenseClient(server_config)
        mcp = create_server(server_config, client=client)
        respx.get("https://opnsense.test/api/core/dashboard/get").mock(
            return_value=httpx.Response(200, json={})
        )
        await client.get("core/dashboard/get")
        assert client._http is not None

        async with mcp.settings.lifespan(mcp):
            pass

        assert client._http is None


class TestServerWiring:
    def test_all_42_tools_registered(self, server_config: Config) -> None:
        mcp = create_server(server_config)
        assert len(mcp._tool_manager._tools) == 42

    def test_tool_names_are_unique(self, server_config: Config) -> None:
        mcp = create_server(server_config)
        names = list(mcp._tool_manager._tools.keys())
        assert len(names) == len(set(names))

    @respx.mock
    async def test_create_server_reuses_passed_client(
        self, server_config: Config
    ) -> None:
        """Startup probe and server share one OPNsenseClient instance."""
        client = OPNsenseClient(server_config)
        respx.get("https://opnsense.test/api/core/dashboard/get").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.get("https://opnsense.test/api/core/system/status").mock(
            return_value=httpx.Response(200, json=_STATUS_RESP)
        )
        await client.get("core/dashboard/get")
        http_after_probe = client._http

        mcp = create_server(server_config, client=client)
        tool_fn = mcp._tool_manager._tools["system_status"].fn
        await tool_fn()

        assert client._http is http_after_probe
