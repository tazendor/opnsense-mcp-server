from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.confirmation import PendingOperationStore
from opnsense_mcp.errors import OPNsenseAPIError, ToolError
from opnsense_mcp.highrisk import run_high_risk
from opnsense_mcp.tools._common import get_or_raise, post_or_raise


async def _system_status(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.get("core/system/status")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _system_firmware_status(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.get("core/firmware/status")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _system_config_backup(client: OPNsenseClient) -> str:
    try:
        return await client.get_text("core/backup/download/this")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


def register_tools(
    mcp: FastMCP, client: OPNsenseClient, store: PendingOperationStore
) -> None:
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

    # --- Firmware (check/poll are standard; update/upgrade are high-risk) ---
    @mcp.tool()
    async def system_firmware_check() -> dict[str, Any]:
        """Kick off a firmware check (poll results via system_firmware_status)."""
        return await post_or_raise(client, "core/firmware/check", None)

    @mcp.tool()
    async def system_firmware_upgrade_status() -> dict[str, Any]:
        """Poll progress of an in-flight firmware update/upgrade."""
        return await get_or_raise(client, "core/firmware/upgradestatus")

    @mcp.tool()
    async def system_firmware_log() -> dict[str, Any]:
        """Retrieve the firmware update/upgrade log."""
        return await post_or_raise(client, "core/firmware/log", None)

    @mcp.tool()
    async def system_config_backup_list(host: str = "") -> dict[str, Any]:
        """List available configuration backup revisions (local history or a remote
        source). Use a listed revision with system_config_restore."""
        return await get_or_raise(client, f"core/backup/backups/{host}")

    # --- High-risk system operations (FR-018, gated) ---
    @mcp.tool()
    async def system_reboot(confirm: str | None = None) -> dict[str, Any]:
        """Reboot the firewall. HIGH-RISK: preview then confirm. All connections and
        tunnels drop; this management session disconnects if it depends on the box."""

        async def execute(token: str) -> dict[str, Any]:
            return await _post_token(client, "core/system/reboot", token)

        return await run_high_risk(
            client,
            store,
            tool_name="system_reboot",
            arguments={},
            description=(
                "Will reboot the firewall now. All active connections and VPN tunnels "
                "drop; this session disconnects if it relies on the firewall."
            ),
            confirm=confirm,
            execute=execute,
        )

    @mcp.tool()
    async def system_halt(confirm: str | None = None) -> dict[str, Any]:
        """Power off the firewall. HIGH-RISK: preview then confirm. Requires physical
        or out-of-band access to power back on."""

        async def execute(token: str) -> dict[str, Any]:
            return await _post_token(client, "core/system/halt", token)

        return await run_high_risk(
            client,
            store,
            tool_name="system_halt",
            arguments={},
            description="Will power off the firewall. It cannot be restarted remotely.",
            confirm=confirm,
            execute=execute,
        )

    @mcp.tool()
    async def system_firmware_update(confirm: str | None = None) -> dict[str, Any]:
        """Trigger a minor/patch firmware update. HIGH-RISK: preview then confirm."""

        async def execute(token: str) -> dict[str, Any]:
            return await _post_token(client, "core/firmware/update", token)

        return await run_high_risk(
            client,
            store,
            tool_name="system_firmware_update",
            arguments={},
            description=(
                "Will start a minor/patch firmware update. Check firmware status "
                "first for the pending version; the box may restart when done."
            ),
            confirm=confirm,
            execute=execute,
        )

    @mcp.tool()
    async def system_firmware_upgrade(confirm: str | None = None) -> dict[str, Any]:
        """Trigger a major firmware upgrade. HIGH-RISK: preview then confirm."""

        async def execute(token: str) -> dict[str, Any]:
            return await _post_token(client, "core/firmware/upgrade", token)

        return await run_high_risk(
            client,
            store,
            tool_name="system_firmware_upgrade",
            arguments={},
            description=(
                "Will start a MAJOR firmware upgrade (higher blast radius than an "
                "update). The box will restart when done."
            ),
            confirm=confirm,
            execute=execute,
        )

    @mcp.tool()
    async def system_config_restore(
        backup: str, host: str = "", confirm: str | None = None
    ) -> dict[str, Any]:
        """Revert the configuration to an existing on-box backup revision (from
        system_config_backup_list). HIGH-RISK: preview then confirm. Note: restoring an
        arbitrary externally-supplied config.xml is out of scope (no such API)."""

        async def execute(token: str) -> dict[str, Any]:
            return await _post_token(
                client, "core/backup/revert_backup", token, {"backup": backup}
            )

        return await run_high_risk(
            client,
            store,
            tool_name="system_config_restore",
            arguments={"backup": backup, "host": host},
            description=(
                f"Will revert the OPNsense configuration to backup revision '{backup}' "
                f"(source '{host or 'local'}'). This overwrites the running config and "
                "may restart services."
            ),
            confirm=confirm,
            execute=execute,
        )


async def _post_token(
    client: OPNsenseClient,
    path: str,
    token: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        return await client.post(path, data, token=token)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc
