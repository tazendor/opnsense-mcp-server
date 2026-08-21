"""Private-key redaction for read responses (FR-017).

Each domain that can return key material applies this with an explicit field set (e.g.
OpenVPN StaticKey ``key``; IPsec KeyPair ``privateKey`` / PreSharedKey ``Key``;
WireGuard Server ``privkey``; Trust Ca/Cert ``prv`` and ``prv_payload``). An explicit
allowlist is used rather than a "looks like a secret" heuristic, to avoid both false
positives (dropping legitimate fields) and false negatives (missing an odd name)."""

from __future__ import annotations

from typing import Any


def redact_private_keys(obj: dict[str, Any], fields: frozenset[str]) -> dict[str, Any]:
    """Return a shallow copy of ``obj`` with any top-level key in ``fields`` removed.

    Does not mutate the input. No-ops cleanly when none of the fields are present."""
    return {k: v for k, v in obj.items() if k not in fields}


def redact_rows(resp: dict[str, Any], fields: frozenset[str]) -> dict[str, Any]:
    """Redact ``fields`` from each row of a search response (``{"rows": [...]}``)."""
    rows = resp.get("rows")
    if not isinstance(rows, list):
        return resp
    return {
        **resp,
        "rows": [
            redact_private_keys(r, fields) if isinstance(r, dict) else r for r in rows
        ],
    }


def redact_wrapped(
    resp: dict[str, Any], wrapper: str, fields: frozenset[str]
) -> dict[str, Any]:
    """Redact ``fields`` from ``resp[wrapper]`` (a get response like a cert object)."""
    inner = resp.get(wrapper)
    if not isinstance(inner, dict):
        return resp
    return {**resp, wrapper: redact_private_keys(inner, fields)}
