"""OpenVPN domain (unified Instances model). FR-012/FR-013.

Instance/static-key/client-override mutations stage; openvpn_apply reconfigures the
service. Deleting an instance is configuration teardown → gated by the confirmation
mechanism (FR-007). Static-key `key` material is redacted on reads (FR-017); the
gen_key generator returns fresh material by explicit request and is not redacted."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opnsense_mcp._validators import validate_uuid
from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.confirmation import PendingOperationStore
from opnsense_mcp.errors import OPNsenseAPIError, ToolError
from opnsense_mcp.highrisk import run_high_risk
from opnsense_mcp.redaction import redact_rows, redact_wrapped

_STATIC_KEY_SECRETS = frozenset({"key"})


async def _get(client: OPNsenseClient, path: str) -> dict[str, Any]:
    try:
        return await client.get(path)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def _post(
    client: OPNsenseClient, path: str, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    try:
        return await client.post(path, data)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


# --- Instances ---------------------------------------------------------------
async def _openvpn_instance_list(client: OPNsenseClient) -> dict[str, Any]:
    return await _get(client, "openvpn/instances/search")


async def _openvpn_instance_get(client: OPNsenseClient, uuid: str) -> dict[str, Any]:
    validate_uuid(uuid)
    return await _get(client, f"openvpn/instances/get/{uuid}")


async def _openvpn_instance_add(
    client: OPNsenseClient, instance: dict[str, Any]
) -> dict[str, Any]:
    return await _post(client, "openvpn/instances/add", {"instance": instance})


async def _openvpn_instance_update(
    client: OPNsenseClient, uuid: str, instance: dict[str, Any]
) -> dict[str, Any]:
    validate_uuid(uuid)
    return await _post(client, f"openvpn/instances/set/{uuid}", {"instance": instance})


async def _openvpn_instance_toggle(client: OPNsenseClient, uuid: str) -> dict[str, Any]:
    validate_uuid(uuid)
    return await _post(client, f"openvpn/instances/toggle/{uuid}", None)


# --- Static keys (redacted) --------------------------------------------------
async def _openvpn_static_key_list(client: OPNsenseClient) -> dict[str, Any]:
    return redact_rows(
        await _get(client, "openvpn/instances/search_static_key"), _STATIC_KEY_SECRETS
    )


async def _openvpn_static_key_get(client: OPNsenseClient, uuid: str) -> dict[str, Any]:
    validate_uuid(uuid)
    return redact_wrapped(
        await _get(client, f"openvpn/instances/get_static_key/{uuid}"),
        "statickey",
        _STATIC_KEY_SECRETS,
    )


async def _openvpn_static_key_add(
    client: OPNsenseClient, statickey: dict[str, Any]
) -> dict[str, Any]:
    return await _post(
        client, "openvpn/instances/add_static_key", {"statickey": statickey}
    )


async def _openvpn_static_key_update(
    client: OPNsenseClient, uuid: str, statickey: dict[str, Any]
) -> dict[str, Any]:
    validate_uuid(uuid)
    return await _post(
        client, f"openvpn/instances/set_static_key/{uuid}", {"statickey": statickey}
    )


async def _openvpn_static_key_delete(
    client: OPNsenseClient, uuid: str
) -> dict[str, Any]:
    validate_uuid(uuid)
    return await _post(client, f"openvpn/instances/del_static_key/{uuid}", None)


async def _openvpn_static_key_generate(
    client: OPNsenseClient, key_type: str
) -> dict[str, Any]:
    # Not redacted: one-shot generation the caller explicitly requested (FR-017 note).
    return await _get(client, f"openvpn/instances/gen_key/{key_type}")


# --- Client overrides (CSO) --------------------------------------------------
async def _openvpn_client_override_list(client: OPNsenseClient) -> dict[str, Any]:
    return await _get(client, "openvpn/client_overwrites/search")


async def _openvpn_client_override_get(
    client: OPNsenseClient, uuid: str
) -> dict[str, Any]:
    validate_uuid(uuid)
    return await _get(client, f"openvpn/client_overwrites/get/{uuid}")


async def _openvpn_client_override_add(
    client: OPNsenseClient, cso: dict[str, Any]
) -> dict[str, Any]:
    return await _post(client, "openvpn/client_overwrites/add", {"cso": cso})


async def _openvpn_client_override_update(
    client: OPNsenseClient, uuid: str, cso: dict[str, Any]
) -> dict[str, Any]:
    validate_uuid(uuid)
    return await _post(client, f"openvpn/client_overwrites/set/{uuid}", {"cso": cso})


async def _openvpn_client_override_delete(
    client: OPNsenseClient, uuid: str
) -> dict[str, Any]:
    validate_uuid(uuid)
    return await _post(client, f"openvpn/client_overwrites/del/{uuid}", None)


# --- Service / status --------------------------------------------------------
async def _openvpn_session_list(client: OPNsenseClient) -> dict[str, Any]:
    return await _get(client, "openvpn/service/search_sessions")


async def _openvpn_route_list(client: OPNsenseClient) -> dict[str, Any]:
    return await _get(client, "openvpn/service/search_routes")


async def _openvpn_session_kill(
    client: OPNsenseClient, session_id: str
) -> dict[str, Any]:
    return await _post(client, "openvpn/service/kill_session", {"id": session_id})


async def _openvpn_service_start(client: OPNsenseClient, vpnid: str) -> dict[str, Any]:
    return await _post(client, "openvpn/service/start_service", {"id": vpnid})


async def _openvpn_service_stop(client: OPNsenseClient, vpnid: str) -> dict[str, Any]:
    return await _post(client, "openvpn/service/stop_service", {"id": vpnid})


async def _openvpn_service_restart(
    client: OPNsenseClient, vpnid: str
) -> dict[str, Any]:
    return await _post(client, "openvpn/service/restart_service", {"id": vpnid})


async def _openvpn_apply(client: OPNsenseClient) -> dict[str, Any]:
    return await _post(client, "openvpn/service/reconfigure", None)


def register_tools(
    mcp: FastMCP, client: OPNsenseClient, store: PendingOperationStore
) -> None:
    @mcp.tool()
    async def openvpn_instance_list() -> dict[str, Any]:
        """List all configured OpenVPN instances (servers and clients)."""
        return await _openvpn_instance_list(client)

    @mcp.tool()
    async def openvpn_instance_get(uuid: str) -> dict[str, Any]:
        """Retrieve one OpenVPN instance by UUID."""
        return await _openvpn_instance_get(client, uuid)

    @mcp.tool()
    async def openvpn_instance_add(instance: dict[str, Any]) -> dict[str, Any]:
        """Add an OpenVPN instance (role=server|client). Staged until openvpn_apply."""
        return await _openvpn_instance_add(client, instance)

    @mcp.tool()
    async def openvpn_instance_update(
        uuid: str, instance: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an OpenVPN instance by UUID. Staged until openvpn_apply."""
        return await _openvpn_instance_update(client, uuid, instance)

    @mcp.tool()
    async def openvpn_instance_toggle(uuid: str) -> dict[str, Any]:
        """Enable/disable an OpenVPN instance by UUID. Staged until openvpn_apply."""
        return await _openvpn_instance_toggle(client, uuid)

    @mcp.tool()
    async def openvpn_instance_delete(
        uuid: str, confirm: str | None = None
    ) -> dict[str, Any]:
        """Delete an OpenVPN instance (configuration teardown). HIGH-RISK: call once
        without `confirm` to preview, then again with the returned confirm token."""
        validate_uuid(uuid)

        async def execute(token: str) -> dict[str, Any]:
            try:
                return await client.post(
                    f"openvpn/instances/del/{uuid}", None, token=token
                )
            except OPNsenseAPIError as exc:
                raise ToolError.from_api_error(exc) from exc

        return await run_high_risk(
            client,
            store,
            tool_name="openvpn_instance_delete",
            arguments={"uuid": uuid},
            description=(
                f"Will delete OpenVPN instance {uuid} and its configuration. "
                "Active tunnels using it will drop. Apply is required afterwards."
            ),
            confirm=confirm,
            execute=execute,
        )

    @mcp.tool()
    async def openvpn_static_key_list() -> dict[str, Any]:
        """List OpenVPN TLS/static keys. Key material is redacted."""
        return await _openvpn_static_key_list(client)

    @mcp.tool()
    async def openvpn_static_key_get(uuid: str) -> dict[str, Any]:
        """Get one OpenVPN static key by UUID. Key material is redacted."""
        return await _openvpn_static_key_get(client, uuid)

    @mcp.tool()
    async def openvpn_static_key_add(statickey: dict[str, Any]) -> dict[str, Any]:
        """Add an OpenVPN static/TLS key (mode, key, description)."""
        return await _openvpn_static_key_add(client, statickey)

    @mcp.tool()
    async def openvpn_static_key_update(
        uuid: str, statickey: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an OpenVPN static/TLS key by UUID."""
        return await _openvpn_static_key_update(client, uuid, statickey)

    @mcp.tool()
    async def openvpn_static_key_delete(uuid: str) -> dict[str, Any]:
        """Delete an OpenVPN static/TLS key by UUID."""
        return await _openvpn_static_key_delete(client, uuid)

    @mcp.tool()
    async def openvpn_static_key_generate(key_type: str) -> dict[str, Any]:
        """Generate a new static/TLS key (type=secret|auth-token|tls-auth|tls-crypt|
        tls-crypt-v2-server). Returns the material once (not persisted, not redacted —
        you explicitly requested it); add it with openvpn_static_key_add to keep it."""
        return await _openvpn_static_key_generate(client, key_type)

    @mcp.tool()
    async def openvpn_client_override_list() -> dict[str, Any]:
        """List OpenVPN per-client config overrides (CSO)."""
        return await _openvpn_client_override_list(client)

    @mcp.tool()
    async def openvpn_client_override_get(uuid: str) -> dict[str, Any]:
        """Get one OpenVPN client override by UUID."""
        return await _openvpn_client_override_get(client, uuid)

    @mcp.tool()
    async def openvpn_client_override_add(cso: dict[str, Any]) -> dict[str, Any]:
        """Add an OpenVPN per-client override. Staged until openvpn_apply."""
        return await _openvpn_client_override_add(client, cso)

    @mcp.tool()
    async def openvpn_client_override_update(
        uuid: str, cso: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an OpenVPN per-client override by UUID."""
        return await _openvpn_client_override_update(client, uuid, cso)

    @mcp.tool()
    async def openvpn_client_override_delete(uuid: str) -> dict[str, Any]:
        """Delete an OpenVPN per-client override by UUID."""
        return await _openvpn_client_override_delete(client, uuid)

    @mcp.tool()
    async def openvpn_session_list() -> dict[str, Any]:
        """List currently connected OpenVPN sessions (live status)."""
        return await _openvpn_session_list(client)

    @mcp.tool()
    async def openvpn_route_list() -> dict[str, Any]:
        """List OpenVPN routes (live status)."""
        return await _openvpn_route_list(client)

    @mcp.tool()
    async def openvpn_session_kill(session_id: str) -> dict[str, Any]:
        """Disconnect a single connected OpenVPN session (it may reconnect)."""
        return await _openvpn_session_kill(client, session_id)

    @mcp.tool()
    async def openvpn_service_start(vpnid: str) -> dict[str, Any]:
        """Start an OpenVPN instance's service by id."""
        return await _openvpn_service_start(client, vpnid)

    @mcp.tool()
    async def openvpn_service_stop(vpnid: str) -> dict[str, Any]:
        """Stop an OpenVPN instance's service by id."""
        return await _openvpn_service_stop(client, vpnid)

    @mcp.tool()
    async def openvpn_service_restart(vpnid: str) -> dict[str, Any]:
        """Restart an OpenVPN instance's service by id."""
        return await _openvpn_service_restart(client, vpnid)

    @mcp.tool()
    async def openvpn_apply() -> dict[str, Any]:
        """Reconfigure OpenVPN to apply staged instance/key/override changes."""
        return await _openvpn_apply(client)
