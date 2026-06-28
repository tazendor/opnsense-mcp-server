from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.errors import OPNsenseAPIError, ToolError


async def _interface_list(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.get("diagnostics/interface/getInterfaceNames")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _interface_config(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.get("diagnostics/interface/getInterfaceConfig")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _interface_arp_table(client: OPNsenseClient) -> list[dict[str, Any]]:
    try:
        return await client.get_list("diagnostics/interface/getArp")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _interface_ndp_table(client: OPNsenseClient) -> list[dict[str, Any]]:
    try:
        return await client.get_list("diagnostics/interface/getNdp")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


def register_tools(mcp: FastMCP, client: OPNsenseClient) -> None:
    @mcp.tool()
    async def interface_list() -> dict[str, Any]:
        """List the names and identifiers of all network interfaces configured
        on OPNsense (e.g., WAN, LAN, OPT1)."""
        return await _interface_list(client)

    @mcp.tool()
    async def interface_config() -> dict[str, Any]:
        """Retrieve the full configuration and status of all network interfaces,
        including MAC address, IP address, subnet mask, link state, and MTU."""
        return await _interface_config(client)

    @mcp.tool()
    async def interface_arp_table() -> list[dict[str, Any]]:
        """Retrieve the current ARP table — the mapping of IP addresses to
        MAC addresses for devices on locally connected networks."""
        return await _interface_arp_table(client)

    @mcp.tool()
    async def interface_ndp_table() -> list[dict[str, Any]]:
        """Retrieve the current NDP (Neighbor Discovery Protocol) table —
        the IPv6 equivalent of the ARP table."""
        return await _interface_ndp_table(client)
