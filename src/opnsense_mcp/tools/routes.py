from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp._validators import validate_uuid
from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.errors import OPNsenseAPIError, ToolError


async def _route_list(
    client: OPNsenseClient,
    current: int = 1,
    row_count: int = -1,
    search_phrase: str = "",
) -> dict[str, Any]:
    try:
        return await client.post(
            "routes/routes/searchroute",
            {"current": current, "rowCount": row_count, "searchPhrase": search_phrase},
        )
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _route_add(client: OPNsenseClient, route: dict[str, Any]) -> dict[str, Any]:
    try:
        return await client.post("routes/routes/addroute", {"route": route})
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _route_update(
    client: OPNsenseClient, uuid: str, route: dict[str, Any]
) -> dict[str, Any]:
    validate_uuid(uuid)
    try:
        return await client.post(f"routes/routes/setroute/{uuid}", {"route": route})
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _route_delete(client: OPNsenseClient, uuid: str) -> dict[str, Any]:
    validate_uuid(uuid)
    try:
        return await client.post(f"routes/routes/delroute/{uuid}", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _route_apply(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.post("routes/routes/reconfigure", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


def register_tools(mcp: FastMCP, client: OPNsenseClient) -> None:
    @mcp.tool()
    async def route_list(
        current: int = 1,
        row_count: int = -1,
        search_phrase: str = "",
    ) -> dict[str, Any]:
        """List all configured static routes."""
        return await _route_list(client, current, row_count, search_phrase)

    @mcp.tool()
    async def route_add(route: dict[str, Any]) -> dict[str, Any]:
        """Add a new static route. Staged until route_apply is called."""
        return await _route_add(client, route)

    @mcp.tool()
    async def route_update(uuid: str, route: dict[str, Any]) -> dict[str, Any]:
        """Update an existing static route by UUID."""
        return await _route_update(client, uuid, route)

    @mcp.tool()
    async def route_delete(uuid: str) -> dict[str, Any]:
        """Delete a static route by UUID."""
        return await _route_delete(client, uuid)

    @mcp.tool()
    async def route_apply() -> dict[str, Any]:
        """Apply all staged static route changes to the running routing table.
        Must be called after add/update/delete operations to take effect."""
        return await _route_apply(client)
