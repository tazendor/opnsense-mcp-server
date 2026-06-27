from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.errors import OPNsenseAPIError, ToolError

# ---------------------------------------------------------------------------
# Firewall rules
# ---------------------------------------------------------------------------


async def _rule_list(
    client: OPNsenseClient,
    current: int = 1,
    row_count: int = -1,
    search_phrase: str = "",
) -> dict[str, Any]:
    try:
        return await client.post(
            "firewall/filter/search_rule",
            {"current": current, "rowCount": row_count, "searchPhrase": search_phrase},
        )
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _rule_get(client: OPNsenseClient, uuid: str) -> dict[str, Any]:
    try:
        return await client.get(f"firewall/filter/get_rule/{uuid}")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _rule_add(client: OPNsenseClient, rule: dict[str, Any]) -> dict[str, Any]:
    try:
        return await client.post("firewall/filter/add_rule", {"rule": rule})
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _rule_update(
    client: OPNsenseClient, uuid: str, rule: dict[str, Any]
) -> dict[str, Any]:
    try:
        return await client.post(f"firewall/filter/set_rule/{uuid}", {"rule": rule})
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _rule_delete(client: OPNsenseClient, uuid: str) -> dict[str, Any]:
    try:
        return await client.post(f"firewall/filter/del_rule/{uuid}", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _rule_apply(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.post("firewall/filter/apply", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


# ---------------------------------------------------------------------------
# Firewall aliases
# ---------------------------------------------------------------------------


async def _alias_list(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.get("firewall/alias/get")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _alias_get_uuid(client: OPNsenseClient, name: str) -> dict[str, Any]:
    try:
        return await client.get(f"firewall/alias/getAliasUUID/{name}")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _alias_add(client: OPNsenseClient, alias: dict[str, Any]) -> dict[str, Any]:
    try:
        return await client.post("firewall/alias/add_item", {"alias": alias})
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _alias_update(
    client: OPNsenseClient, uuid: str, alias: dict[str, Any]
) -> dict[str, Any]:
    try:
        return await client.post(f"firewall/alias/set_item/{uuid}", {"alias": alias})
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _alias_delete(client: OPNsenseClient, uuid: str) -> dict[str, Any]:
    try:
        return await client.post(f"firewall/alias/del_item/{uuid}", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _alias_apply(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.post("firewall/alias/reconfigure", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


# ---------------------------------------------------------------------------
# NAT rules
# ---------------------------------------------------------------------------


async def _nat_list(
    client: OPNsenseClient,
    current: int = 1,
    row_count: int = -1,
    search_phrase: str = "",
) -> dict[str, Any]:
    try:
        return await client.post(
            "firewall/nat/searchrule",
            {"current": current, "rowCount": row_count, "searchPhrase": search_phrase},
        )
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _nat_add(client: OPNsenseClient, rule: dict[str, Any]) -> dict[str, Any]:
    try:
        return await client.post("firewall/nat/addrule", {"rule": rule})
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _nat_update(
    client: OPNsenseClient, uuid: str, rule: dict[str, Any]
) -> dict[str, Any]:
    try:
        return await client.post(f"firewall/nat/setrule/{uuid}", {"rule": rule})
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _nat_delete(client: OPNsenseClient, uuid: str) -> dict[str, Any]:
    try:
        return await client.post(f"firewall/nat/delrule/{uuid}", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _nat_apply(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.post("firewall/nat/apply", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def register_tools(mcp: FastMCP, client: OPNsenseClient) -> None:
    @mcp.tool()
    async def firewall_rule_list(
        current: int = 1,
        row_count: int = -1,
        search_phrase: str = "",
    ) -> dict[str, Any]:
        """List all firewall filter rules."""
        return await _rule_list(client, current, row_count, search_phrase)

    @mcp.tool()
    async def firewall_rule_get(uuid: str) -> dict[str, Any]:
        """Retrieve full details of a single firewall rule by UUID."""
        return await _rule_get(client, uuid)

    @mcp.tool()
    async def firewall_rule_add(rule: dict[str, Any]) -> dict[str, Any]:
        """Add a new firewall filter rule. Changes are staged until
        firewall_rule_apply is called."""
        return await _rule_add(client, rule)

    @mcp.tool()
    async def firewall_rule_update(uuid: str, rule: dict[str, Any]) -> dict[str, Any]:
        """Update an existing firewall filter rule by UUID. Changes are staged
        until firewall_rule_apply is called."""
        return await _rule_update(client, uuid, rule)

    @mcp.tool()
    async def firewall_rule_delete(uuid: str) -> dict[str, Any]:
        """Delete a firewall filter rule by UUID. Changes are staged until
        firewall_rule_apply is called."""
        return await _rule_delete(client, uuid)

    @mcp.tool()
    async def firewall_rule_apply() -> dict[str, Any]:
        """Apply all staged firewall filter rule changes to the running
        configuration. Must be called after add/update/delete operations."""
        return await _rule_apply(client)

    @mcp.tool()
    async def firewall_alias_list() -> dict[str, Any]:
        """List all firewall aliases."""
        return await _alias_list(client)

    @mcp.tool()
    async def firewall_alias_get_uuid(name: str) -> dict[str, Any]:
        """Look up the UUID of a firewall alias by name."""
        return await _alias_get_uuid(client, name)

    @mcp.tool()
    async def firewall_alias_add(alias: dict[str, Any]) -> dict[str, Any]:
        """Add a new firewall alias. Changes are staged until
        firewall_alias_apply is called."""
        return await _alias_add(client, alias)

    @mcp.tool()
    async def firewall_alias_update(uuid: str, alias: dict[str, Any]) -> dict[str, Any]:
        """Update an existing firewall alias by UUID."""
        return await _alias_update(client, uuid, alias)

    @mcp.tool()
    async def firewall_alias_delete(uuid: str) -> dict[str, Any]:
        """Delete a firewall alias by UUID."""
        return await _alias_delete(client, uuid)

    @mcp.tool()
    async def firewall_alias_apply() -> dict[str, Any]:
        """Apply all staged alias changes to the running configuration."""
        return await _alias_apply(client)

    @mcp.tool()
    async def firewall_nat_list(
        current: int = 1,
        row_count: int = -1,
        search_phrase: str = "",
    ) -> dict[str, Any]:
        """List all NAT (port-forward) rules."""
        return await _nat_list(client, current, row_count, search_phrase)

    @mcp.tool()
    async def firewall_nat_add(rule: dict[str, Any]) -> dict[str, Any]:
        """Add a NAT rule. Staged until firewall_nat_apply."""
        return await _nat_add(client, rule)

    @mcp.tool()
    async def firewall_nat_update(uuid: str, rule: dict[str, Any]) -> dict[str, Any]:
        """Update a NAT rule by UUID."""
        return await _nat_update(client, uuid, rule)

    @mcp.tool()
    async def firewall_nat_delete(uuid: str) -> dict[str, Any]:
        """Delete a NAT rule by UUID."""
        return await _nat_delete(client, uuid)

    @mcp.tool()
    async def firewall_nat_apply() -> dict[str, Any]:
        """Apply all staged NAT rule changes."""
        return await _nat_apply(client)
