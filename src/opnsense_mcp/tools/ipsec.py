"""IPsec domain (strongSwan, core module). FR-012/FR-013.

Connections ("phase 1"), local/remote auth rounds, children ("phase 2"), pools, key
pairs and pre-shared keys stage; ipsec_apply reconfigures. Deleting a connection or
globally disabling IPsec is configuration teardown → gated (FR-007). KeyPair private
keys and PSK secrets are redacted on reads; the keypair generator is not (FR-017)."""

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

_CONN = "ipsec/connections"
_KEYPAIR_SECRETS = frozenset({"privateKey"})
_PSK_SECRETS = frozenset({"Key"})


def register_tools(
    mcp: FastMCP, client: OPNsenseClient, store: PendingOperationStore
) -> None:
    # --- Connections (phase 1) ---
    @mcp.tool()
    async def ipsec_connection_list() -> dict[str, Any]:
        """List IPsec connections (phase 1 equivalent)."""
        return await get_or_raise(client, f"{_CONN}/search_connection")

    @mcp.tool()
    async def ipsec_connection_get(uuid: str) -> dict[str, Any]:
        """Get one IPsec connection by UUID."""
        validate_uuid(uuid)
        return await get_or_raise(client, f"{_CONN}/get_connection/{uuid}")

    @mcp.tool()
    async def ipsec_connection_add(connection: dict[str, Any]) -> dict[str, Any]:
        """Add an IPsec connection. Staged until ipsec_apply."""
        return await post_or_raise(
            client, f"{_CONN}/add_connection", {"connection": connection}
        )

    @mcp.tool()
    async def ipsec_connection_update(
        uuid: str, connection: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an IPsec connection by UUID. Staged until ipsec_apply."""
        validate_uuid(uuid)
        return await post_or_raise(
            client, f"{_CONN}/set_connection/{uuid}", {"connection": connection}
        )

    @mcp.tool()
    async def ipsec_connection_toggle(uuid: str) -> dict[str, Any]:
        """Enable/disable an IPsec connection by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(client, f"{_CONN}/toggle_connection/{uuid}", None)

    @mcp.tool()
    async def ipsec_connection_delete(
        uuid: str, confirm: str | None = None
    ) -> dict[str, Any]:
        """Delete an IPsec connection (teardown). HIGH-RISK: preview then confirm."""
        validate_uuid(uuid)

        async def execute(token: str) -> dict[str, Any]:
            try:
                return await client.post(
                    f"{_CONN}/del_connection/{uuid}", None, token=token
                )
            except OPNsenseAPIError as exc:
                raise ToolError.from_api_error(exc) from exc

        return await run_high_risk(
            client,
            store,
            tool_name="ipsec_connection_delete",
            arguments={"uuid": uuid},
            description=(
                f"Will delete IPsec connection {uuid} and its configuration. "
                "Tunnels using it will drop. Apply is required afterwards."
            ),
            confirm=confirm,
            execute=execute,
        )

    # --- Local / Remote auth rounds & Children (phase 2): same CRUD shape ---
    def _register_crud(kind: str, obj_key: str, label: str) -> None:
        @mcp.tool(name=f"ipsec_{kind}_list", description=f"List IPsec {label} entries.")
        async def _list() -> dict[str, Any]:
            return await get_or_raise(client, f"{_CONN}/search_{kind}")

        @mcp.tool(
            name=f"ipsec_{kind}_get",
            description=f"Get one IPsec {label} entry by UUID.",
        )
        async def _get(uuid: str) -> dict[str, Any]:
            validate_uuid(uuid)
            return await get_or_raise(client, f"{_CONN}/get_{kind}/{uuid}")

        @mcp.tool(
            name=f"ipsec_{kind}_add",
            description=f"Add an IPsec {label} entry. Staged until ipsec_apply.",
        )
        async def _add(entry: dict[str, Any]) -> dict[str, Any]:
            return await post_or_raise(client, f"{_CONN}/add_{kind}", {obj_key: entry})

        @mcp.tool(
            name=f"ipsec_{kind}_update",
            description=f"Update an IPsec {label} entry by UUID. Staged until apply.",
        )
        async def _update(uuid: str, entry: dict[str, Any]) -> dict[str, Any]:
            validate_uuid(uuid)
            return await post_or_raise(
                client, f"{_CONN}/set_{kind}/{uuid}", {obj_key: entry}
            )

        @mcp.tool(
            name=f"ipsec_{kind}_toggle",
            description=f"Enable/disable an IPsec {label} entry by UUID.",
        )
        async def _toggle(uuid: str) -> dict[str, Any]:
            validate_uuid(uuid)
            return await post_or_raise(client, f"{_CONN}/toggle_{kind}/{uuid}", None)

        @mcp.tool(
            name=f"ipsec_{kind}_delete",
            description=f"Delete an IPsec {label} entry by UUID. Staged until apply.",
        )
        async def _delete(uuid: str) -> dict[str, Any]:
            validate_uuid(uuid)
            return await post_or_raise(client, f"{_CONN}/del_{kind}/{uuid}", None)

    _register_crud("local", "local", "local auth-round")
    _register_crud("remote", "remote", "remote auth-round")
    _register_crud("child", "child", "child (phase 2)")

    # --- Global enable ---
    @mcp.tool()
    async def ipsec_enabled_get() -> dict[str, Any]:
        """Report whether IPsec is globally enabled."""
        return await get_or_raise(client, f"{_CONN}/is_enabled")

    @mcp.tool()
    async def ipsec_enabled_toggle(confirm: str | None = None) -> dict[str, Any]:
        """Toggle IPsec globally on/off. HIGH-RISK when disabling (all tunnels drop):
        preview then confirm."""

        async def execute(token: str) -> dict[str, Any]:
            try:
                return await client.post(f"{_CONN}/toggle", None, token=token)
            except OPNsenseAPIError as exc:
                raise ToolError.from_api_error(exc) from exc

        return await run_high_risk(
            client,
            store,
            tool_name="ipsec_enabled_toggle",
            arguments={},
            description=(
                "Will toggle the global IPsec enable state. If this disables IPsec, "
                "every tunnel drops at once."
            ),
            confirm=confirm,
            execute=execute,
        )

    # --- Key pairs (redacted) ---
    @mcp.tool()
    async def ipsec_keypair_list() -> dict[str, Any]:
        """List IPsec key pairs. Private key material is redacted."""
        return redact_rows(
            await get_or_raise(client, "ipsec/key_pairs/search_item"), _KEYPAIR_SECRETS
        )

    @mcp.tool()
    async def ipsec_keypair_get(uuid: str) -> dict[str, Any]:
        """Get one IPsec key pair by UUID. Private key material is redacted."""
        validate_uuid(uuid)
        return redact_wrapped(
            await get_or_raise(client, f"ipsec/key_pairs/get_item/{uuid}"),
            "keyPair",
            _KEYPAIR_SECRETS,
        )

    @mcp.tool()
    async def ipsec_keypair_add(keyPair: dict[str, Any]) -> dict[str, Any]:
        """Add an IPsec key pair."""
        return await post_or_raise(
            client, "ipsec/key_pairs/add_item", {"keyPair": keyPair}
        )

    @mcp.tool()
    async def ipsec_keypair_update(
        uuid: str, keyPair: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an IPsec key pair by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(
            client, f"ipsec/key_pairs/set_item/{uuid}", {"keyPair": keyPair}
        )

    @mcp.tool()
    async def ipsec_keypair_delete(uuid: str) -> dict[str, Any]:
        """Delete an IPsec key pair by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(client, f"ipsec/key_pairs/del_item/{uuid}", None)

    @mcp.tool()
    async def ipsec_keypair_generate(key_type: str, size: str) -> dict[str, Any]:
        """Generate an IPsec key pair (type=rsa|ecdsa, size in bits). Returned once,
        not persisted, not redacted — you explicitly requested it."""
        return await get_or_raise(
            client, f"ipsec/key_pairs/gen_key_pair/{key_type}/{size}"
        )

    # --- Pre-shared keys (redacted) ---
    @mcp.tool()
    async def ipsec_psk_list() -> dict[str, Any]:
        """List IPsec pre-shared keys. Secret material is redacted."""
        return redact_rows(
            await get_or_raise(client, "ipsec/pre_shared_keys/search_item"),
            _PSK_SECRETS,
        )

    @mcp.tool()
    async def ipsec_psk_get(uuid: str) -> dict[str, Any]:
        """Get one IPsec pre-shared key by UUID. Secret material is redacted."""
        validate_uuid(uuid)
        return redact_wrapped(
            await get_or_raise(client, f"ipsec/pre_shared_keys/get_item/{uuid}"),
            "preSharedKey",
            _PSK_SECRETS,
        )

    @mcp.tool()
    async def ipsec_psk_add(preSharedKey: dict[str, Any]) -> dict[str, Any]:
        """Add an IPsec pre-shared key."""
        return await post_or_raise(
            client, "ipsec/pre_shared_keys/add_item", {"preSharedKey": preSharedKey}
        )

    @mcp.tool()
    async def ipsec_psk_update(
        uuid: str, preSharedKey: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an IPsec pre-shared key by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(
            client,
            f"ipsec/pre_shared_keys/set_item/{uuid}",
            {"preSharedKey": preSharedKey},
        )

    @mcp.tool()
    async def ipsec_psk_delete(uuid: str) -> dict[str, Any]:
        """Delete an IPsec pre-shared key by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(
            client, f"ipsec/pre_shared_keys/del_item/{uuid}", None
        )

    # --- Pools ---
    @mcp.tool()
    async def ipsec_pool_list() -> dict[str, Any]:
        """List IPsec virtual-IP address pools."""
        return await get_or_raise(client, "ipsec/pools/search")

    @mcp.tool()
    async def ipsec_pool_get(uuid: str) -> dict[str, Any]:
        """Get one IPsec pool by UUID."""
        validate_uuid(uuid)
        return await get_or_raise(client, f"ipsec/pools/get/{uuid}")

    @mcp.tool()
    async def ipsec_pool_add(pool: dict[str, Any]) -> dict[str, Any]:
        """Add an IPsec pool."""
        return await post_or_raise(client, "ipsec/pools/add", {"pool": pool})

    @mcp.tool()
    async def ipsec_pool_update(uuid: str, pool: dict[str, Any]) -> dict[str, Any]:
        """Update an IPsec pool by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(client, f"ipsec/pools/set/{uuid}", {"pool": pool})

    @mcp.tool()
    async def ipsec_pool_toggle(uuid: str) -> dict[str, Any]:
        """Enable/disable an IPsec pool by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(client, f"ipsec/pools/toggle/{uuid}", None)

    @mcp.tool()
    async def ipsec_pool_delete(uuid: str) -> dict[str, Any]:
        """Delete an IPsec pool by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(client, f"ipsec/pools/del/{uuid}", None)

    # --- Sessions (live) & service ---
    @mcp.tool()
    async def ipsec_session_list(phase: int = 1) -> dict[str, Any]:
        """List live IPsec security associations (phase=1 or 2)."""
        return await get_or_raise(client, f"ipsec/sessions/search_phase{phase}")

    @mcp.tool()
    async def ipsec_session_connect(connection: str) -> dict[str, Any]:
        """Bring a configured IPsec connection up (live)."""
        return await post_or_raise(client, "ipsec/sessions/connect", {"id": connection})

    @mcp.tool()
    async def ipsec_session_disconnect(session_id: str) -> dict[str, Any]:
        """Bring an IPsec session down (live)."""
        return await post_or_raise(
            client, "ipsec/sessions/disconnect", {"id": session_id}
        )

    @mcp.tool()
    async def ipsec_service_start() -> dict[str, Any]:
        """Start the IPsec service."""
        return await post_or_raise(client, "ipsec/service/start", None)

    @mcp.tool()
    async def ipsec_service_stop() -> dict[str, Any]:
        """Stop the IPsec service."""
        return await post_or_raise(client, "ipsec/service/stop", None)

    @mcp.tool()
    async def ipsec_service_restart() -> dict[str, Any]:
        """Restart the IPsec service."""
        return await post_or_raise(client, "ipsec/service/restart", None)

    @mcp.tool()
    async def ipsec_apply() -> dict[str, Any]:
        """Reconfigure IPsec to apply staged changes."""
        return await post_or_raise(client, "ipsec/service/reconfigure", None)
