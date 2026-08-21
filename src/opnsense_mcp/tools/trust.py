"""Trust / Certificates & PKI domain (core module). FR-016.

CA and certificate metadata is readable with private key material redacted (FR-017);
import/issue may return a freshly generated key once by explicit request (not redacted),
and the export tool returns key/pkcs12 by explicit request. Revocation has no dedicated
OPNsense endpoint — it is a CRL read-modify-write, gated as high-risk (FR-008)."""

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

_KEY_SECRETS = frozenset({"prv", "prv_payload"})


def register_tools(
    mcp: FastMCP, client: OPNsenseClient, store: PendingOperationStore
) -> None:
    # --- Certificate Authorities (key material redacted on reads) ---
    @mcp.tool()
    async def trust_ca_list() -> dict[str, Any]:
        """List certificate authorities. Private key material is redacted."""
        return redact_rows(await get_or_raise(client, "trust/ca/search"), _KEY_SECRETS)

    @mcp.tool()
    async def trust_ca_get(uuid: str) -> dict[str, Any]:
        """Get one CA by UUID. Private key material is redacted."""
        validate_uuid(uuid)
        return redact_wrapped(
            await get_or_raise(client, f"trust/ca/get/{uuid}"), "ca", _KEY_SECRETS
        )

    @mcp.tool()
    async def trust_ca_add(ca: dict[str, Any]) -> dict[str, Any]:
        """Import or issue a CA. With private_key_location=local the response returns
        the generated key ONCE (not redacted — you requested it); the default persists
        it server-side where it is redacted on future reads."""
        return await post_or_raise(client, "trust/ca/add", {"ca": ca})

    @mcp.tool()
    async def trust_ca_update(uuid: str, ca: dict[str, Any]) -> dict[str, Any]:
        """Update a CA by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(client, f"trust/ca/set/{uuid}", {"ca": ca})

    @mcp.tool()
    async def trust_ca_delete(uuid: str) -> dict[str, Any]:
        """Delete a CA by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(client, f"trust/ca/del/{uuid}", None)

    # --- Certificates ---
    @mcp.tool()
    async def trust_certificate_list() -> dict[str, Any]:
        """List certificates. Private key material is redacted."""
        return redact_rows(
            await get_or_raise(client, "trust/cert/search"), _KEY_SECRETS
        )

    @mcp.tool()
    async def trust_certificate_get(uuid: str) -> dict[str, Any]:
        """Get one certificate by UUID. Private key material is redacted."""
        validate_uuid(uuid)
        return redact_wrapped(
            await get_or_raise(client, f"trust/cert/get/{uuid}"), "cert", _KEY_SECRETS
        )

    @mcp.tool()
    async def trust_certificate_add(cert: dict[str, Any]) -> dict[str, Any]:
        """Import or issue a certificate. Same one-shot key semantics as the CA add."""
        return await post_or_raise(client, "trust/cert/add", {"cert": cert})

    @mcp.tool()
    async def trust_certificate_update(
        uuid: str, cert: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a certificate by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(client, f"trust/cert/set/{uuid}", {"cert": cert})

    @mcp.tool()
    async def trust_certificate_delete(uuid: str) -> dict[str, Any]:
        """Delete a certificate by UUID."""
        validate_uuid(uuid)
        return await post_or_raise(client, f"trust/cert/del/{uuid}", None)

    @mcp.tool()
    async def trust_certificate_export(uuid: str, export_type: str) -> dict[str, Any]:
        """Export a certificate artifact (type=crt|csr|prv|pkcs12). NOT redacted:
        prv/pkcs12 return key material by explicit request from this export tool."""
        validate_uuid(uuid)
        return await get_or_raise(
            client, f"trust/cert/generate_file/{uuid}/{export_type}"
        )

    @mcp.tool()
    async def trust_certificate_revoke(
        uuid: str, reason: int = 0, confirm: str | None = None
    ) -> dict[str, Any]:
        """Revoke a certificate (reason 0-6). HIGH-RISK: preview then confirm. No
        dedicated revoke endpoint exists — this is a CRL read-modify-write against the
        issuing CA and cannot be undone via this tool."""
        validate_uuid(uuid)
        cert = (await get_or_raise(client, f"trust/cert/get/{uuid}")).get("cert", {})
        caref = str(cert.get("caref", ""))
        refid = str(cert.get("refid", ""))
        description = (
            f"Will revoke certificate {refid or uuid} issued by CA {caref}, "
            f"reason={reason}. This cannot be undone via this tool."
        )

        async def execute(token: str) -> dict[str, Any]:
            crl_resp = await get_or_raise(client, f"trust/crl/get/{caref}")
            crl = crl_resp.get("crl", crl_resp)
            key = f"revoked_reason_{reason}"
            refids = [r for r in str(crl.get(key, "")).split(",") if r]
            if refid and refid not in refids:
                refids.append(refid)
            crl[key] = ",".join(refids)
            try:
                return await client.post(
                    f"trust/crl/set/{caref}", {"crl": crl}, token=token
                )
            except OPNsenseAPIError as exc:
                raise ToolError.from_api_error(exc) from exc

        return await run_high_risk(
            client,
            store,
            tool_name="trust_certificate_revoke",
            arguments={"uuid": uuid, "reason": reason},
            description=description,
            confirm=confirm,
            execute=execute,
        )

    # --- CRLs & settings ---
    @mcp.tool()
    async def trust_crl_list() -> dict[str, Any]:
        """List certificate revocation lists."""
        return await get_or_raise(client, "trust/crl/search")

    @mcp.tool()
    async def trust_crl_get(caref: str) -> dict[str, Any]:
        """Get the CRL state for a CA (which certs are revoked and why)."""
        return await get_or_raise(client, f"trust/crl/get/{caref}")

    @mcp.tool()
    async def trust_settings_get() -> dict[str, Any]:
        """Get general trust-store settings."""
        return await get_or_raise(client, "trust/settings/get")

    @mcp.tool()
    async def trust_settings_update(settings: dict[str, Any]) -> dict[str, Any]:
        """Update general trust-store settings."""
        return await post_or_raise(client, "trust/settings/set", {"settings": settings})
