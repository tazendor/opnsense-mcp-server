from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.errors import OPNsenseAPIError, ToolError


async def _ids_ruleset_list(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.get("ids/settings/listRulesets")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _ids_ruleset_toggle(
    client: OPNsenseClient, filenames: str, enabled: int | None = None
) -> dict[str, Any]:
    path = f"ids/settings/toggle_ruleset/{filenames}"
    if enabled is not None:
        path += f"/{enabled}"
    try:
        return await client.post(path, None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _ids_rule_toggle(
    client: OPNsenseClient, sids: str, enabled: int | None = None
) -> dict[str, Any]:
    path = f"ids/settings/toggle_rule/{sids}"
    if enabled is not None:
        path += f"/{enabled}"
    try:
        return await client.post(path, None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _ids_apply(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.post("ids/service/reconfigure", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


def register_tools(mcp: FastMCP, client: OPNsenseClient) -> None:
    @mcp.tool()
    async def ids_ruleset_list() -> dict[str, Any]:
        """List all available IDS/IPS rulesets and their enabled/disabled status."""
        return await _ids_ruleset_list(client)

    @mcp.tool()
    async def ids_ruleset_toggle(
        filenames: str, enabled: int | None = None
    ) -> dict[str, Any]:
        """Enable or disable one or more IDS/IPS rulesets by comma-separated
        filename(s). Omit `enabled` to flip current state, or pass 0/1 to force
        disabled/enabled. Takes effect after ids_apply."""
        return await _ids_ruleset_toggle(client, filenames, enabled)

    @mcp.tool()
    async def ids_rule_toggle(sids: str, enabled: int | None = None) -> dict[str, Any]:
        """Enable or disable individual IDS/IPS rules by comma-separated SID(s).
        Omit `enabled` to flip, or pass 0/1. Takes effect after ids_apply."""
        return await _ids_rule_toggle(client, sids, enabled)

    @mcp.tool()
    async def ids_apply() -> dict[str, Any]:
        """Reconfigure and restart Suricata to apply staged ruleset/rule toggles."""
        return await _ids_apply(client)
