from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.errors import OPNsenseAPIError, ToolError


async def _ids_alert_list(
    client: OPNsenseClient,
    row_count: int = 100,
    search_phrase: str = "",
) -> dict[str, Any]:
    try:
        return await client.post(
            "ids/alert/search",
            {
                "current": 1,
                "rowCount": row_count,
                "searchPhrase": search_phrase,
                "sort": {},
            },
        )
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _ids_ruleset_list(
    client: OPNsenseClient,
    row_count: int = 100,
    search_phrase: str = "",
) -> dict[str, Any]:
    try:
        return await client.post(
            "ids/settings/searchRuleset",
            {
                "current": 1,
                "rowCount": row_count,
                "searchPhrase": search_phrase,
                "sort": {},
            },
        )
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


def register_tools(mcp: FastMCP, client: OPNsenseClient) -> None:
    @mcp.tool()
    async def ids_alert_list(
        row_count: int = 100, search_phrase: str = ""
    ) -> dict[str, Any]:
        """List recent IDS/IPS alerts. Optionally filter by search_phrase.
        Returns paginated rows with alert details including signature,
        source/destination IP and port."""
        return await _ids_alert_list(
            client, row_count=row_count, search_phrase=search_phrase
        )

    @mcp.tool()
    async def ids_ruleset_list(
        row_count: int = 100, search_phrase: str = ""
    ) -> dict[str, Any]:
        """List available IDS/IPS rulesets and their enabled/disabled status.
        Optionally filter by search_phrase."""
        return await _ids_ruleset_list(
            client, row_count=row_count, search_phrase=search_phrase
        )
