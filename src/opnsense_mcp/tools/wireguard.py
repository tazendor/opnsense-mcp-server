"""WireGuard domain (core module). FR-012/FR-013.

Server (instance) and client (peer) mutations stage; wireguard_apply reconfigures.
Deleting a server is configuration teardown → gated (FR-007). Server private keys are
redacted on reads; a peer has no private key (only an optional PSK, also redacted).
The server keypair and client PSK generators return fresh material by explicit request
and are not redacted (FR-017)."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp._validators import validate_uuid
from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.confirmation import PendingOperationStore
from opnsense_mcp.errors import OPNsenseAPIError, ToolError
from opnsense_mcp.highrisk import run_high_risk
from opnsense_mcp.redaction import redact_rows, redact_wrapped
from opnsense_mcp.tools._common import get_or_raise, post_or_raise

_SERVER_SECRETS = frozenset({"privkey"})
_CLIENT_SECRETS = frozenset({"psk"})


def register_tools(
    mcp: FastMCP, client: OPNsenseClient, store: PendingOperationStore
) -> None:
    # --- Servers (instances; privkey redacted) ---
    @mcp.tool()
    async def wireguard_server_list() -> dict[str, Any]:
        """List WireGuard server instances. Private keys are redacted."""
        return redact_rows(
            await get_or_raise(client, "wireguard/server/search_server"),
            _SERVER_SECRETS,
        )

    @mcp.tool()
    async def wireguard_server_get(uuid: str) -> dict[str, Any]:
        """Get one WireGuard server by UUID. Private key is redacted."""
        validate_uuid(uuid)
        return redact_wrapped(
            await get_or_raise(client, f"wireguard/server/get_server/{uuid}"),
            "server",
            _SERVER_SECRETS,
        )

    @mcp.tool()
    async def wireguard_server_add(server: dict[str, Any]) -> dict[str, Any]:
        """Add a WireGuard server instance. Staged until wireguard_apply."""
        return await post_or_raise(
            client, "wireguard/server/add_server", {"server": server}
        )

    @mcp.tool()
    async def wireguard_server_update(
        uuid: str, server: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a WireGuard server by UUID. Staged until wireguard_apply."""
        validate_uuid(uuid)
        return await post_or_raise(
            client, f"wireguard/server/set_server/{uuid}", {"server": server}
        )

    @mcp.tool()
    async def wireguard_server_toggle(uuid: str) -> dict[str, Any]:
        """Enable/disable a WireGuard server by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(
            client, f"wireguard/server/toggle_server/{uuid}", None
        )

    @mcp.tool()
    async def wireguard_server_delete(
        uuid: str, confirm: str | None = None
    ) -> dict[str, Any]:
        """Delete a WireGuard server (teardown). HIGH-RISK: preview then confirm."""
        validate_uuid(uuid)

        async def execute(token: str) -> dict[str, Any]:
            try:
                return await client.post(
                    f"wireguard/server/del_server/{uuid}", None, token=token
                )
            except OPNsenseAPIError as exc:
                raise ToolError.from_api_error(exc) from exc

        return await run_high_risk(
            client,
            store,
            tool_name="wireguard_server_delete",
            arguments={"uuid": uuid},
            description=(
                f"Will delete WireGuard server {uuid} and its configuration. "
                "Its tunnel and all peers on it stop. Apply is required afterwards."
            ),
            confirm=confirm,
            execute=execute,
        )

    @mcp.tool()
    async def wireguard_server_keypair_generate() -> dict[str, Any]:
        """Generate a WireGuard server keypair. Returned once, not persisted, not
        redacted — you explicitly requested it."""
        return await get_or_raise(client, "wireguard/server/key_pair")

    @mcp.tool()
    async def wireguard_server_list_for_client() -> dict[str, Any]:
        """List servers available to attach a peer to (lookup helper)."""
        return await get_or_raise(client, "wireguard/client/list_servers")

    # --- Clients (peers; psk redacted, no private key exists) ---
    @mcp.tool()
    async def wireguard_client_list() -> dict[str, Any]:
        """List WireGuard peers. PSK is redacted; peers carry no private key."""
        return redact_rows(
            await get_or_raise(client, "wireguard/client/search_client"),
            _CLIENT_SECRETS,
        )

    @mcp.tool()
    async def wireguard_client_get(uuid: str) -> dict[str, Any]:
        """Get one WireGuard peer by UUID. PSK is redacted."""
        validate_uuid(uuid)
        return redact_wrapped(
            await get_or_raise(client, f"wireguard/client/get_client/{uuid}"),
            "client",
            _CLIENT_SECRETS,
        )

    @mcp.tool()
    async def wireguard_client_add(peer: dict[str, Any]) -> dict[str, Any]:
        """Add a WireGuard peer (pubkey, tunneladdress, endpoint, ...). Staged until
        wireguard_apply."""
        return await post_or_raise(
            client, "wireguard/client/add_client", {"client": peer}
        )

    @mcp.tool()
    async def wireguard_client_update(
        uuid: str, peer: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a WireGuard peer by UUID. Staged until wireguard_apply."""
        validate_uuid(uuid)
        return await post_or_raise(
            client, f"wireguard/client/set_client/{uuid}", {"client": peer}
        )

    @mcp.tool()
    async def wireguard_client_toggle(uuid: str) -> dict[str, Any]:
        """Enable/disable a WireGuard peer by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(
            client, f"wireguard/client/toggle_client/{uuid}", None
        )

    @mcp.tool()
    async def wireguard_client_delete(uuid: str) -> dict[str, Any]:
        """Delete a WireGuard peer by UUID (standard: one peer, not a teardown)."""
        validate_uuid(uuid)
        return await post_or_raise(client, f"wireguard/client/del_client/{uuid}", None)

    @mcp.tool()
    async def wireguard_client_psk_generate() -> dict[str, Any]:
        """Generate a WireGuard pre-shared key. Returned once, not persisted, not
        redacted — you explicitly requested it."""
        return await get_or_raise(client, "wireguard/client/psk")

    @mcp.tool()
    async def wireguard_client_builder_get() -> dict[str, Any]:
        """Get a pre-filled WireGuard peer template with a free tunnel IP allocated."""
        return await get_or_raise(client, "wireguard/client/get_client_builder")

    @mcp.tool()
    async def wireguard_client_builder_add(builder: dict[str, Any]) -> dict[str, Any]:
        """Create a WireGuard peer from the builder template."""
        return await post_or_raise(
            client, "wireguard/client/add_client_builder", builder
        )

    # --- General / service ---
    @mcp.tool()
    async def wireguard_general_get() -> dict[str, Any]:
        """Get WireGuard general settings."""
        return await get_or_raise(client, "wireguard/general/get")

    @mcp.tool()
    async def wireguard_general_update(settings: dict[str, Any]) -> dict[str, Any]:
        """Update WireGuard general settings. Staged until wireguard_apply."""
        return await post_or_raise(
            client, "wireguard/general/set", {"general": settings}
        )

    @mcp.tool()
    async def wireguard_service_start() -> dict[str, Any]:
        """Start the WireGuard service."""
        return await post_or_raise(client, "wireguard/service/start", None)

    @mcp.tool()
    async def wireguard_service_stop() -> dict[str, Any]:
        """Stop the WireGuard service."""
        return await post_or_raise(client, "wireguard/service/stop", None)

    @mcp.tool()
    async def wireguard_service_restart() -> dict[str, Any]:
        """Restart the WireGuard service."""
        return await post_or_raise(client, "wireguard/service/restart", None)

    @mcp.tool()
    async def wireguard_status() -> dict[str, Any]:
        """Live WireGuard status (wg show): per-peer handshake and transfer."""
        return await get_or_raise(client, "wireguard/service/show")

    @mcp.tool()
    async def wireguard_apply() -> dict[str, Any]:
        """Reconfigure WireGuard to apply staged server/peer/general changes."""
        return await post_or_raise(client, "wireguard/service/reconfigure", None)
