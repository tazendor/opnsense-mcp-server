"""Captive Portal domain (core module). FR-015.

Zone configuration stages; captiveportal_apply reconfigures. A single session
disconnect proceeds directly; disconnecting every session in a zone is high-risk and
gated (FR-008) — OPNsense has no bulk endpoint, so the confirmed call fans out one
disconnect per session itself."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp._validators import validate_uuid
from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.confirmation import PendingOperationStore
from opnsense_mcp.errors import OPNsenseAPIError, ToolError
from opnsense_mcp.highrisk import run_high_risk
from opnsense_mcp.tools._common import (
    get_list_or_raise,
    get_or_raise,
    post_or_raise,
)

_SET = "captiveportal/settings"
_SESS = "captiveportal/session"


async def _list_zone_sessions(
    client: OPNsenseClient, zone_id: str
) -> list[dict[str, Any]]:
    return await get_list_or_raise(client, f"{_SESS}/list/{zone_id}")


def register_tools(
    mcp: FastMCP, client: OPNsenseClient, store: PendingOperationStore
) -> None:
    # --- Zones ---
    @mcp.tool()
    async def captiveportal_zone_list() -> dict[str, Any]:
        """List captive portal zones."""
        return await get_or_raise(client, f"{_SET}/search_zones")

    @mcp.tool()
    async def captiveportal_zone_get(uuid: str) -> dict[str, Any]:
        """Get one captive portal zone by UUID."""
        validate_uuid(uuid)
        return await get_or_raise(client, f"{_SET}/get_zone/{uuid}")

    @mcp.tool()
    async def captiveportal_zone_add(zone: dict[str, Any]) -> dict[str, Any]:
        """Add a captive portal zone. Staged until captiveportal_apply."""
        return await post_or_raise(client, f"{_SET}/add_zone", {"zone": zone})

    @mcp.tool()
    async def captiveportal_zone_update(
        uuid: str, zone: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a captive portal zone by UUID. Staged until captiveportal_apply."""
        validate_uuid(uuid)
        return await post_or_raise(client, f"{_SET}/set_zone/{uuid}", {"zone": zone})

    @mcp.tool()
    async def captiveportal_zone_toggle(uuid: str) -> dict[str, Any]:
        """Enable/disable a captive portal zone by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(client, f"{_SET}/toggle_zone/{uuid}", None)

    @mcp.tool()
    async def captiveportal_zone_delete(uuid: str) -> dict[str, Any]:
        """Delete a captive portal zone by UUID. Staged until captiveportal_apply."""
        validate_uuid(uuid)
        return await post_or_raise(client, f"{_SET}/del_zone/{uuid}", None)

    @mcp.tool()
    async def captiveportal_zone_names() -> dict[str, Any]:
        """List zone id → description (lookup helper)."""
        return await get_or_raise(client, f"{_SESS}/zones")

    # --- Sessions ---
    @mcp.tool()
    async def captiveportal_session_list(zone_id: str) -> list[dict[str, Any]]:
        """List active sessions in a captive portal zone."""
        return await _list_zone_sessions(client, zone_id)

    @mcp.tool()
    async def captiveportal_session_connect(
        zone_id: str, session: dict[str, Any]
    ) -> dict[str, Any]:
        """Manually register a captive portal session in a zone."""
        return await post_or_raise(client, f"{_SESS}/connect/{zone_id}", session)

    @mcp.tool()
    async def captiveportal_session_disconnect(
        zone_id: str, session_id: str
    ) -> dict[str, Any]:
        """Disconnect a single captive portal session (proceeds directly)."""
        return await post_or_raise(
            client, f"{_SESS}/disconnect/{zone_id}", {"sessionId": session_id}
        )

    @mcp.tool()
    async def captiveportal_session_disconnect_zone(
        zone_id: str, confirm: str | None = None
    ) -> dict[str, Any]:
        """Disconnect EVERY active session in a zone. HIGH-RISK: preview then confirm.
        No bulk OPNsense endpoint exists — the confirmed call disconnects each session
        individually and reports per-session success/failure."""
        description = (
            f"Will disconnect all active sessions in captive portal zone {zone_id}."
        )
        if confirm is None:
            sessions = await _list_zone_sessions(client, zone_id)
            ids = [s.get("sessionId") for s in sessions]
            description = (
                f"Will disconnect {len(ids)} active session(s) in captive portal "
                f"zone {zone_id}: {ids}"
            )

        async def execute(token: str) -> dict[str, Any]:
            sessions = await _list_zone_sessions(client, zone_id)
            disconnected: list[str] = []
            failed: list[str] = []
            for s in sessions:
                sid = str(s.get("sessionId", ""))
                try:
                    await client.post(
                        f"{_SESS}/disconnect/{zone_id}",
                        {"sessionId": sid},
                        token=token,
                    )
                    disconnected.append(sid)
                except (OPNsenseAPIError, ToolError):
                    failed.append(sid)
            return {"disconnected": disconnected, "failed": failed}

        return await run_high_risk(
            client,
            store,
            tool_name="captiveportal_session_disconnect_zone",
            arguments={"zone_id": zone_id},
            description=description,
            confirm=confirm,
            execute=execute,
        )

    # --- Service ---
    @mcp.tool()
    async def captiveportal_service_start() -> dict[str, Any]:
        """Start the captive portal service."""
        return await post_or_raise(client, "captiveportal/service/start", None)

    @mcp.tool()
    async def captiveportal_service_stop() -> dict[str, Any]:
        """Stop the captive portal service."""
        return await post_or_raise(client, "captiveportal/service/stop", None)

    @mcp.tool()
    async def captiveportal_service_restart() -> dict[str, Any]:
        """Restart the captive portal service."""
        return await post_or_raise(client, "captiveportal/service/restart", None)

    @mcp.tool()
    async def captiveportal_apply() -> dict[str, Any]:
        """Reconfigure captive portal to apply staged zone changes."""
        return await post_or_raise(client, "captiveportal/service/reconfigure", None)
