import pytest

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.tools.routes import (
    _route_add,
    _route_apply,
    _route_delete,
    _route_list,
)
from opnsense_mcp.tools.services import _service_status


@pytest.mark.integration
class TestRouteIntegration:
    async def test_route_list_has_rows_key(self, live_client: OPNsenseClient) -> None:
        result = await _route_list(live_client)
        assert "rows" in result

    async def test_route_crud_cycle(self, live_client: OPNsenseClient) -> None:
        route = {
            "network": "203.0.113.0/24",
            "gateway": "Null4",
            "descr": "mcp-integration-test",
            "disabled": "0",
        }

        added = await _route_add(live_client, route=route)
        uuid = added.get("uuid", "")
        assert uuid, "Expected a UUID from route_add"

        try:
            applied = await _route_apply(live_client)
            assert applied.get("status") == "ok"

            listing = await _route_list(live_client)
            uuids = [r.get("uuid") for r in listing.get("rows", [])]
            assert uuid in uuids
        finally:
            await _route_delete(live_client, uuid=uuid)
            await _route_apply(live_client)


@pytest.mark.integration
class TestServiceStatusIntegration:
    async def test_unbound_status_returns_status_key(
        self, live_client: OPNsenseClient
    ) -> None:
        result = await _service_status(live_client, module="unbound")
        assert "status" in result

    async def test_kea_status_returns_status_key(
        self, live_client: OPNsenseClient
    ) -> None:
        result = await _service_status(live_client, module="kea")
        assert "status" in result
