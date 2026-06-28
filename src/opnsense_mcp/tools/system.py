from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.errors import OPNsenseAPIError, ToolError


async def _system_status(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.get("core/system/status")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _system_firmware_status(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.get("firmware/status/check")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _system_config_backup(client: OPNsenseClient) -> str:
    try:
        return await client.get_text("core/backup/download/this")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


def register_tools(mcp: FastMCP, client: OPNsenseClient) -> None:
    @mcp.tool()
    async def system_status() -> dict[str, Any]:
        """Retrieve current system health status including any pending alerts
        or subsystem messages."""
        return await _system_status(client)

    @mcp.tool()
    async def system_firmware_status() -> dict[str, Any]:
        """Check the current firmware version and whether updates are available."""
        return await _system_firmware_status(client)

    @mcp.tool()
    async def system_config_backup() -> str:
        """Download the current OPNsense configuration as an XML document.
        Use this to take a snapshot before making changes."""
        return await _system_config_backup(client)
