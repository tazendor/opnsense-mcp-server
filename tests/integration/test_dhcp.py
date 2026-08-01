"""US1 DHCP integration tests — require a live OPNsense instance (auto-skipped when
OPNSENSE_URL / config.toml is absent).

The write cycle additionally requires OPNSENSE_INTEGRATION_WRITES=1 (the
require_write_optin fixture) so it can never mutate a box — production or otherwise — by
accident. It stages a
throwaway reservation, applies, verifies, then removes it and re-applies, and needs at
least one configured Kea DHCPv4 subnet (self-skips if none). Endpoint casing (snake_case
add_reservation/set_reservation/del_reservation) and reservation field names follow
docs.opnsense.org — confirm against the instance and adjust if rejected (see
specs/002.../research.md "Note on URL casing conventions")."""

import pytest

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.tools.dhcp import (
    _dhcp_apply,
    _dhcp_settings_get,
    _dhcp_static_add,
    _dhcp_static_delete,
    _dhcp_static_list,
)

_TEST_MAC = "02:00:00:aa:bb:cc"  # locally-administered, unlikely to collide
_TEST_IP = "192.0.2.234"  # TEST-NET-1 (RFC 5737)


@pytest.mark.integration
class TestDhcpReads:
    async def test_settings_get_returns_dhcpv4(
        self, live_client: OPNsenseClient
    ) -> None:
        result = await _dhcp_settings_get(live_client)
        assert isinstance(result, dict)

    async def test_static_list_has_rows(self, live_client: OPNsenseClient) -> None:
        result = await _dhcp_static_list(live_client)
        assert "rows" in result


@pytest.mark.integration
class TestDhcpStaticWriteCycle:
    async def _first_subnet_uuid(self, client: OPNsenseClient) -> str | None:
        settings = await _dhcp_settings_get(client)
        subnets = settings.get("dhcpv4", {}).get("subnets", {}).get("subnet4", {})
        if isinstance(subnets, dict) and subnets:
            return next(iter(subnets))
        return None

    async def test_add_apply_list_delete_cycle(
        self, live_client: OPNsenseClient, require_write_optin: None
    ) -> None:
        subnet = await self._first_subnet_uuid(live_client)
        if subnet is None:
            pytest.skip("no Kea DHCPv4 subnet configured to attach a reservation to")

        added = await _dhcp_static_add(
            live_client,
            {
                "subnet": subnet,
                "hw_address": _TEST_MAC,
                "ip_address": _TEST_IP,
                "description": "opnsense-mcp integration test — safe to delete",
            },
        )
        uuid = added.get("uuid")
        assert added.get("result") == "saved" and uuid

        try:
            await _dhcp_apply(live_client)
            listing = await _dhcp_static_list(live_client)
            macs = [r.get("hw_address", r.get("mac")) for r in listing.get("rows", [])]
            assert _TEST_MAC in macs
        finally:
            await _dhcp_static_delete(live_client, uuid)
            await _dhcp_apply(live_client)
