from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.confirmation import PendingOperationStore
from opnsense_mcp.errors import OPNsenseAPIError, ToolError
from opnsense_mcp.highrisk import run_high_risk
from opnsense_mcp.tools._common import get_or_raise, post_or_raise

_ASSIGN = "interfaces/assignment"


async def _interface_list(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.get("diagnostics/interface/getInterfaceNames")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _interface_config(client: OPNsenseClient) -> dict[str, Any]:
    try:
        return await client.get("diagnostics/interface/getInterfaceConfig")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _interface_arp_table(client: OPNsenseClient) -> list[dict[str, Any]]:
    try:
        return await client.get_list("diagnostics/interface/getArp")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _interface_ndp_table(client: OPNsenseClient) -> list[dict[str, Any]]:
    try:
        return await client.get_list("diagnostics/interface/getNdp")
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


def register_tools(
    mcp: FastMCP, client: OPNsenseClient, store: PendingOperationStore
) -> None:
    @mcp.tool()
    async def interface_list() -> dict[str, Any]:
        """List the names and identifiers of all network interfaces configured
        on OPNsense (e.g., WAN, LAN, OPT1)."""
        return await _interface_list(client)

    @mcp.tool()
    async def interface_config() -> dict[str, Any]:
        """Retrieve the full configuration and status of all network interfaces,
        including MAC address, IP address, subnet mask, link state, and MTU."""
        return await _interface_config(client)

    @mcp.tool()
    async def interface_arp_table() -> list[dict[str, Any]]:
        """Retrieve the current ARP table — the mapping of IP addresses to
        MAC addresses for devices on locally connected networks."""
        return await _interface_arp_table(client)

    @mcp.tool()
    async def interface_ndp_table() -> list[dict[str, Any]]:
        """Retrieve the current NDP (Neighbor Discovery Protocol) table —
        the IPv6 equivalent of the ARP table."""
        return await _interface_ndp_table(client)

    # --- Assignment (reassignment only; enable/disable + IP config not exposed) ---
    @mcp.tool()
    async def interface_assignment_list() -> dict[str, Any]:
        """List physical-device-to-logical-interface assignments (e.g. igb2 → opt3)."""
        return await get_or_raise(client, f"{_ASSIGN}/search_item")

    @mcp.tool()
    async def interface_assignment_get(ifname: str) -> dict[str, Any]:
        """Get one interface assignment by logical name."""
        return await get_or_raise(client, f"{_ASSIGN}/get_item/{ifname}")

    @mcp.tool()
    async def interface_assignment_add(assignment: dict[str, Any]) -> dict[str, Any]:
        """Assign a physical device to a new logical interface. Staged until
        interface_apply."""
        return await post_or_raise(
            client, f"{_ASSIGN}/add_item", {"interface": assignment}
        )

    @mcp.tool()
    async def interface_assignment_update(
        ifname: str, assignment: dict[str, Any], confirm: str | None = None
    ) -> dict[str, Any]:
        """Reassign the physical device backing a logical interface. HIGH-RISK: preview
        then confirm — may disconnect this management session."""

        async def execute(token: str) -> dict[str, Any]:
            try:
                return await client.post(
                    f"{_ASSIGN}/set_item/{ifname}",
                    {"interface": assignment},
                    token=token,
                )
            except OPNsenseAPIError as exc:
                raise ToolError.from_api_error(exc) from exc

        return await run_high_risk(
            client,
            store,
            tool_name="interface_assignment_update",
            arguments={"ifname": ifname, "assignment": assignment},
            description=(
                f"Will reassign logical interface {ifname} to physical device "
                f"{assignment.get('if', '<unspecified>')}. If {ifname} carries this "
                "session's management traffic, the session disconnects."
            ),
            confirm=confirm,
            execute=execute,
        )

    @mcp.tool()
    async def interface_assignment_delete(
        ifnames: str, confirm: str | None = None
    ) -> dict[str, Any]:
        """Remove interface assignment(s) (comma-separated logical names). HIGH-RISK:
        preview then confirm."""

        async def execute(token: str) -> dict[str, Any]:
            try:
                return await client.post(
                    f"{_ASSIGN}/del_item/{ifnames}", None, token=token
                )
            except OPNsenseAPIError as exc:
                raise ToolError.from_api_error(exc) from exc

        return await run_high_risk(
            client,
            store,
            tool_name="interface_assignment_delete",
            arguments={"ifnames": ifnames},
            description=(
                f"Will remove interface assignment(s): {ifnames}. Associated firewall "
                "rules are cleaned up. May disconnect this session."
            ),
            confirm=confirm,
            execute=execute,
        )

    @mcp.tool()
    async def interface_apply() -> dict[str, Any]:
        """Apply staged interface assignment changes and reload the packet filter."""
        return await post_or_raise(client, f"{_ASSIGN}/reconfigure", None)
