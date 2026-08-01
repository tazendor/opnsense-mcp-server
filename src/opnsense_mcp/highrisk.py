"""Shared preview→confirm→execute flow for high-risk tools (FR-007–FR-011).

Every high-risk MCP tool delegates to :func:`run_high_risk` so the confirmation
contract (preview without contacting OPNsense; single-use, argument-scoped token;
preview + execution both logged and correlated) is implemented once, not re-derived per
tool."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.confirmation import PendingOperationStore


async def run_high_risk(
    client: OPNsenseClient,
    store: PendingOperationStore,
    *,
    tool_name: str,
    arguments: dict[str, Any],
    description: str,
    confirm: str | None,
    execute: Callable[[str], Awaitable[dict[str, Any]]],
) -> dict[str, Any]:
    """Gate a high-risk operation behind a confirmation token.

    Unset ``confirm``: register a pending operation, log the preview (no request to
    OPNsense), return the token + description. Set ``confirm``: validate/consume the
    token for this exact ``tool_name`` + ``arguments``, then call ``execute(token)`` —
    which issues the real request exactly once, tagging its log record with the token so
    it correlates to the preview."""
    if confirm is None:
        op = store.create(tool_name, arguments, description)
        client.log_preview(tool_name, arguments, op.token)
        return {
            "status": "confirmation_required",
            "confirm_token": op.token,
            "description": description,
            "expires_in_seconds": store.ttl_seconds,
        }
    store.consume(confirm, tool_name, arguments)
    return await execute(confirm)
