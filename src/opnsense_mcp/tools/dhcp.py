from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.errors import OPNsenseAPIError, ToolError


async def _dhcp_lease_list(
    client: OPNsenseClient,
    current: int = 1,
    row_count: int = -1,
    search_phrase: str = "",
    inactive: int = 0,
) -> dict[str, Any]:
    try:
        return await client.post(
            "kea/leases4/search",
            {
                "current": current,
                "rowCount": row_count,
                "searchPhrase": search_phrase,
                "inactive": inactive,
            },
        )
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _dhcp_settings_get(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.get("kea/dhcpv4/get")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _dhcp_static_list(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.get("kea/dhcpv4/searchReservation")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


def register_tools(mcp: FastMCP, client: OPNsenseClient) -> None:
    @mcp.tool()
    async def dhcp_lease_list(
        current: int = 1,
        row_count: int = -1,
        search_phrase: str = "",
        inactive: int = 0,
    ) -> dict[str, Any]:
        """List current DHCPv4 leases — both dynamic (assigned automatically)
        and static (MAC-bound)."""
        return await _dhcp_lease_list(
            client, current, row_count, search_phrase, inactive
        )

    @mcp.tool()
    async def dhcp_settings_get() -> dict[str, Any]:
        """Retrieve the DHCPv4 service configuration (subnet definitions,
        range settings, DNS options, and static mappings)."""
        return await _dhcp_settings_get(client)

    @mcp.tool()
    async def dhcp_static_list() -> dict[str, Any]:
        """List all static DHCP lease mappings (MAC address to fixed IP)."""
        return await _dhcp_static_list(client)
