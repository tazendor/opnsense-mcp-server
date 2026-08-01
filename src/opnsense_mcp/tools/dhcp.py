from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp._validators import validate_uuid
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


async def _dhcp_static_add(
    client: OPNsenseClient, reservation: dict[str, Any]
) -> dict[str, Any]:
    try:
        return await client.post(
            "kea/dhcpv4/add_reservation", {"reservation": reservation}
        )
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _dhcp_static_update(
    client: OPNsenseClient, uuid: str, reservation: dict[str, Any]
) -> dict[str, Any]:
    validate_uuid(uuid)
    try:
        return await client.post(
            f"kea/dhcpv4/set_reservation/{uuid}", {"reservation": reservation}
        )
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _dhcp_static_delete(client: OPNsenseClient, uuid: str) -> dict[str, Any]:
    validate_uuid(uuid)
    try:
        return await client.post(f"kea/dhcpv4/del_reservation/{uuid}", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _dhcp_settings_update(
    client: OPNsenseClient, settings: dict[str, Any]
) -> dict[str, Any]:
    try:
        return await client.post("kea/dhcpv4/set", {"dhcpv4": settings})
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _dhcp_apply(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.post("kea/service/reconfigure", None)
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

    @mcp.tool()
    async def dhcp_static_add(reservation: dict[str, Any]) -> dict[str, Any]:
        """Add a DHCPv4 static reservation (MAC → fixed IP). Requires subnet,
        hw_address, and ip_address. Staged until dhcp_apply is called."""
        return await _dhcp_static_add(client, reservation)

    @mcp.tool()
    async def dhcp_static_update(
        uuid: str, reservation: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing DHCPv4 static reservation by UUID. Staged until
        dhcp_apply is called."""
        return await _dhcp_static_update(client, uuid, reservation)

    @mcp.tool()
    async def dhcp_static_delete(uuid: str) -> dict[str, Any]:
        """Delete a DHCPv4 static reservation by UUID. Staged until dhcp_apply."""
        return await _dhcp_static_delete(client, uuid)

    @mcp.tool()
    async def dhcp_settings_update(settings: dict[str, Any]) -> dict[str, Any]:
        """Update DHCPv4 service settings (subnets, ranges, DNS options). Staged
        until dhcp_apply is called."""
        return await _dhcp_settings_update(client, settings)

    @mcp.tool()
    async def dhcp_apply() -> dict[str, Any]:
        """Reconfigure and restart the Kea DHCPv4 service to apply all staged
        reservation and settings changes. Causes a brief DHCP service interruption."""
        return await _dhcp_apply(client)
