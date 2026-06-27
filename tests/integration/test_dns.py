from collections.abc import AsyncGenerator

import pytest

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.config import Config
from opnsense_mcp.tools.dns import (
    _dns_apply,
    _dns_host_override_add,
    _dns_host_override_delete,
    _dns_host_override_list,
    _dns_settings_get,
)


@pytest.fixture
async def live_client() -> AsyncGenerator[OPNsenseClient, None]:
    config = Config.load()
    async with OPNsenseClient(config) as client:
        yield client


@pytest.mark.integration
class TestDnsIntegration:
    async def test_settings_get_returns_unbound_key(
        self, live_client: OPNsenseClient
    ) -> None:
        result = await _dns_settings_get(live_client)
        assert "unbound" in result

    async def test_host_override_list_has_rows_key(
        self, live_client: OPNsenseClient
    ) -> None:
        result = await _dns_host_override_list(live_client)
        assert "rows" in result

    async def test_host_override_crud_cycle(self, live_client: OPNsenseClient) -> None:
        host = {
            "enabled": "1",
            "host": "mcp-integ-test",
            "domain": "internal.test",
            "rr": "A",
            "server": "203.0.113.42",
            "description": "mcp-integration-test",
        }

        added = await _dns_host_override_add(live_client, host=host)
        uuid = added.get("uuid", "")
        assert uuid, "Expected a UUID from dns_host_override_add"

        try:
            listing = await _dns_host_override_list(live_client)
            uuids = [r.get("uuid") for r in listing.get("rows", [])]
            assert uuid in uuids

            applied = await _dns_apply(live_client)
            assert applied.get("status") == "ok"
        finally:
            await _dns_host_override_delete(live_client, uuid=uuid)
            await _dns_apply(live_client)
