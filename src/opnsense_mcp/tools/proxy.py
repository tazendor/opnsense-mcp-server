"""Web Proxy (Squid) domain. FR-014. Requires the os-squid plugin.

Settings (incl. the flat forward.acl allow/deny lists), remote blacklist feeds, and PAC
generation rules stage; proxy_apply reconfigures. All standard risk. Blacklist feed
`password` is redacted on reads. The os-OPNProxy policy ACL engine is out of scope
(spec Assumptions — enumerated coverage exclusions)."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp._validators import validate_uuid
from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.redaction import redact_rows, redact_wrapped
from opnsense_mcp.tools._common import get_or_raise, post_or_raise

_SET = "proxy/settings"
_BLACKLIST_SECRETS = frozenset({"password"})


def register_tools(mcp: FastMCP, client: OPNsenseClient) -> None:
    @mcp.tool()
    async def proxy_settings_get() -> dict[str, Any]:
        """Retrieve the full Squid proxy configuration, including the forward.acl
        allow/deny lists (allowedSubnets, bannedHosts, whiteList, blackList, ...)."""
        return await get_or_raise(client, f"{_SET}/get")

    @mcp.tool()
    async def proxy_settings_update(proxy: dict[str, Any]) -> dict[str, Any]:
        """Update Squid proxy configuration, including access-control lists. Staged
        until proxy_apply."""
        return await post_or_raise(client, f"{_SET}/set", {"proxy": proxy})

    # --- Remote blacklist feeds (password redacted) ---
    @mcp.tool()
    async def proxy_remote_blacklist_list() -> dict[str, Any]:
        """List downloadable blacklist feeds. Feed passwords are redacted."""
        return redact_rows(
            await get_or_raise(client, f"{_SET}/search_remote_blacklist"),
            _BLACKLIST_SECRETS,
        )

    @mcp.tool()
    async def proxy_remote_blacklist_get(uuid: str) -> dict[str, Any]:
        """Get one blacklist feed by UUID. Feed password is redacted."""
        validate_uuid(uuid)
        return redact_wrapped(
            await get_or_raise(client, f"{_SET}/get_remote_blacklist/{uuid}"),
            "blacklist",
            _BLACKLIST_SECRETS,
        )

    @mcp.tool()
    async def proxy_remote_blacklist_add(blacklist: dict[str, Any]) -> dict[str, Any]:
        """Add a downloadable blacklist feed."""
        return await post_or_raise(
            client, f"{_SET}/add_remote_blacklist", {"blacklist": blacklist}
        )

    @mcp.tool()
    async def proxy_remote_blacklist_update(
        uuid: str, blacklist: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a blacklist feed by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(
            client, f"{_SET}/set_remote_blacklist/{uuid}", {"blacklist": blacklist}
        )

    @mcp.tool()
    async def proxy_remote_blacklist_toggle(uuid: str) -> dict[str, Any]:
        """Enable/disable a blacklist feed by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(
            client, f"{_SET}/toggle_remote_blacklist/{uuid}", None
        )

    @mcp.tool()
    async def proxy_remote_blacklist_delete(uuid: str) -> dict[str, Any]:
        """Delete a blacklist feed by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(client, f"{_SET}/del_remote_blacklist/{uuid}", None)

    # --- PAC rule / proxy / match: identical 5-action CRUD ---
    def _register_pac(kind: str, obj_key: str) -> None:
        @mcp.tool(
            name=f"proxy_pac_{kind}_list", description=f"List proxy PAC {kind} entries."
        )
        async def _list() -> dict[str, Any]:
            return await get_or_raise(client, f"{_SET}/search_pac_{kind}")

        @mcp.tool(
            name=f"proxy_pac_{kind}_get",
            description=f"Get one proxy PAC {kind} entry by UUID.",
        )
        async def _get(uuid: str) -> dict[str, Any]:
            validate_uuid(uuid)
            return await get_or_raise(client, f"{_SET}/get_pac_{kind}/{uuid}")

        @mcp.tool(
            name=f"proxy_pac_{kind}_add",
            description=f"Add a proxy PAC {kind} entry. Staged until proxy_apply.",
        )
        async def _add(entry: dict[str, Any]) -> dict[str, Any]:
            return await post_or_raise(
                client, f"{_SET}/add_pac_{kind}", {obj_key: entry}
            )

        @mcp.tool(
            name=f"proxy_pac_{kind}_update",
            description=f"Update a proxy PAC {kind} entry by UUID.",
        )
        async def _update(uuid: str, entry: dict[str, Any]) -> dict[str, Any]:
            validate_uuid(uuid)
            return await post_or_raise(
                client, f"{_SET}/set_pac_{kind}/{uuid}", {obj_key: entry}
            )

        @mcp.tool(
            name=f"proxy_pac_{kind}_delete",
            description=f"Delete a proxy PAC {kind} entry by UUID.",
        )
        async def _delete(uuid: str) -> dict[str, Any]:
            validate_uuid(uuid)
            return await post_or_raise(client, f"{_SET}/del_pac_{kind}/{uuid}", None)

    _register_pac("rule", "rule")
    _register_pac("proxy", "proxy")
    _register_pac("match", "match")

    # --- Service ---
    @mcp.tool()
    async def proxy_service_start() -> dict[str, Any]:
        """Start the Squid proxy service."""
        return await post_or_raise(client, "proxy/service/start", None)

    @mcp.tool()
    async def proxy_service_stop() -> dict[str, Any]:
        """Stop the Squid proxy service."""
        return await post_or_raise(client, "proxy/service/stop", None)

    @mcp.tool()
    async def proxy_service_restart() -> dict[str, Any]:
        """Restart the Squid proxy service."""
        return await post_or_raise(client, "proxy/service/restart", None)

    @mcp.tool()
    async def proxy_service_reset() -> dict[str, Any]:
        """Clear the Squid cache."""
        return await post_or_raise(client, "proxy/service/reset", None)

    @mcp.tool()
    async def proxy_apply() -> dict[str, Any]:
        """Reconfigure Squid to apply staged settings/ACL/blacklist/PAC changes."""
        return await post_or_raise(client, "proxy/service/reconfigure", None)
