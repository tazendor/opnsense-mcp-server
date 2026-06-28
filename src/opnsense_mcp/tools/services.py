from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.errors import OPNsenseAPIError, ToolError

SUPPORTED_MODULES: frozenset[str] = frozenset(
    {"unbound", "kea", "firmware", "ids", "cron"}
)


def _validate_module(module: str) -> None:
    if module not in SUPPORTED_MODULES:
        raise ToolError(
            f"Unknown module '{module}'. Supported modules: "
            + ", ".join(sorted(SUPPORTED_MODULES))
        )


async def _service_status(client: OPNsenseClient, module: str) -> dict[str, Any]:
    _validate_module(module)
    try:
        return await client.get(f"{module}/service/status")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _service_start(client: OPNsenseClient, module: str) -> dict[str, Any]:
    _validate_module(module)
    try:
        return await client.post(f"{module}/service/start", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _service_stop(client: OPNsenseClient, module: str) -> dict[str, Any]:
    _validate_module(module)
    try:
        return await client.post(f"{module}/service/stop", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _service_restart(client: OPNsenseClient, module: str) -> dict[str, Any]:
    _validate_module(module)
    try:
        return await client.post(f"{module}/service/restart", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


def register_tools(mcp: FastMCP, client: OPNsenseClient) -> None:
    @mcp.tool()
    async def service_status(module: str) -> dict[str, Any]:
        """Retrieve the running/stopped status of a core OPNsense service.
        Supported modules: unbound, kea, firmware, ids, cron."""
        return await _service_status(client, module)

    @mcp.tool()
    async def service_start(module: str) -> dict[str, Any]:
        """Start a core OPNsense service. Has no effect if already running.
        Supported modules: unbound, kea, firmware, ids, cron."""
        return await _service_start(client, module)

    @mcp.tool()
    async def service_stop(module: str) -> dict[str, Any]:
        """Stop a core OPNsense service. Has no effect if already stopped.
        Supported modules: unbound, kea, firmware, ids, cron."""
        return await _service_stop(client, module)

    @mcp.tool()
    async def service_restart(module: str) -> dict[str, Any]:
        """Restart a core OPNsense service, applying any pending configuration.
        Supported modules: unbound, kea, firmware, ids, cron."""
        return await _service_restart(client, module)
