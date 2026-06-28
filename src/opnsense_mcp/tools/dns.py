from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.errors import OPNsenseAPIError, ToolError


async def _dns_settings_get(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.get("unbound/settings/get")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _dns_host_override_list(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.get("unbound/settings/searchHostOverride")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _dns_host_override_add(
    client: OPNsenseClient, host: dict[str, Any]
) -> dict[str, Any]:
    try:
        return await client.post("unbound/settings/addHostOverride", {"host": host})
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _dns_host_override_update(
    client: OPNsenseClient, uuid: str, host: dict[str, Any]
) -> dict[str, Any]:
    try:
        return await client.post(
            f"unbound/settings/setHostOverride/{uuid}", {"host": host}
        )
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _dns_host_override_delete(
    client: OPNsenseClient, uuid: str
) -> dict[str, Any]:
    try:
        return await client.post(f"unbound/settings/delHostOverride/{uuid}", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _dns_lookup(client: OPNsenseClient, hostname: str) -> dict[str, Any]:
    try:
        return await client.get(f"unbound/diagnostics/lookup/{hostname}")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _dns_flush_cache(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.post("unbound/diagnostics/clearCache", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _dns_apply(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.post("unbound/service/reconfigure", None)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


def register_tools(mcp: FastMCP, client: OPNsenseClient) -> None:
    @mcp.tool()
    async def dns_settings_get() -> dict[str, Any]:
        """Retrieve the full Unbound DNS Resolver configuration."""
        return await _dns_settings_get(client)

    @mcp.tool()
    async def dns_host_override_list() -> dict[str, Any]:
        """List all DNS host overrides configured in the Unbound resolver."""
        return await _dns_host_override_list(client)

    @mcp.tool()
    async def dns_host_override_add(host: dict[str, Any]) -> dict[str, Any]:
        """Add a DNS host override. Staged until dns_apply is called."""
        return await _dns_host_override_add(client, host)

    @mcp.tool()
    async def dns_host_override_update(
        uuid: str, host: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing DNS host override by UUID."""
        return await _dns_host_override_update(client, uuid, host)

    @mcp.tool()
    async def dns_host_override_delete(uuid: str) -> dict[str, Any]:
        """Delete a DNS host override by UUID."""
        return await _dns_host_override_delete(client, uuid)

    @mcp.tool()
    async def dns_lookup(hostname: str) -> dict[str, Any]:
        """Perform a DNS lookup for a hostname using the local Unbound resolver.
        Returns all records found including A, AAAA, CNAME, and TTL information."""
        return await _dns_lookup(client, hostname)

    @mcp.tool()
    async def dns_flush_cache() -> dict[str, Any]:
        """Flush the entire Unbound DNS resolver cache. Use after making DNS
        changes that need to propagate immediately."""
        return await _dns_flush_cache(client)

    @mcp.tool()
    async def dns_apply() -> dict[str, Any]:
        """Reconfigure and restart the Unbound DNS Resolver to apply all staged
        changes. Causes a brief DNS outage while Unbound reloads."""
        return await _dns_apply(client)
