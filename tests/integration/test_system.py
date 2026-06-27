from collections.abc import AsyncGenerator

import pytest

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.config import Config
from opnsense_mcp.tools.dhcp import _dhcp_lease_list
from opnsense_mcp.tools.interfaces import _interface_list
from opnsense_mcp.tools.system import _system_status


@pytest.fixture
async def live_client() -> AsyncGenerator[OPNsenseClient, None]:
    config = Config.load()
    async with OPNsenseClient(config) as client:
        yield client


@pytest.mark.integration
class TestSystemIntegration:
    async def test_system_status_has_versions(
        self, live_client: OPNsenseClient
    ) -> None:
        result = await _system_status(live_client)
        assert "versions" in result

    async def test_interface_list_not_empty(self, live_client: OPNsenseClient) -> None:
        result = await _interface_list(live_client)
        assert isinstance(result, dict)
        assert len(result) > 0

    async def test_dhcp_lease_list_structure(self, live_client: OPNsenseClient) -> None:
        result = await _dhcp_lease_list(live_client)
        assert "rows" in result
        assert "total" in result
