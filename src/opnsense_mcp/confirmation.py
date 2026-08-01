"""In-process confirm-then-execute safety layer (FR-007–FR-011).

A high-risk MCP tool takes an optional ``confirm`` token. On the first (unconfirmed)
call it validates inputs, describes the effect, registers a :class:`PendingOperation`,
and returns the token WITHOUT contacting OPNsense. On the confirmed call it hands the
token back; the store verifies it is unexpired, single-use, and bound to this exact
tool + arguments, then the tool issues the real request exactly once.

The store is process-local and never persisted — confirmations do not survive a restart
(spec Assumptions)."""

from __future__ import annotations

import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from opnsense_mcp.errors import ToolError


@dataclass(frozen=True)
class PendingOperation:
    token: str
    tool_name: str
    arguments: dict[str, Any]
    description: str
    expires_at: float  # deadline on the store's monotonic clock


class PendingOperationStore:
    def __init__(
        self,
        ttl_seconds: float = 120.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_seconds
        self._clock = clock
        self._pending: dict[str, PendingOperation] = {}

    def create(
        self, tool_name: str, arguments: dict[str, Any], description: str
    ) -> PendingOperation:
        """Register a pending high-risk operation and return it (with a fresh token)."""
        self._evict_expired()
        op = PendingOperation(
            token=secrets.token_urlsafe(32),
            tool_name=tool_name,
            arguments=dict(arguments),
            description=description,
            expires_at=self._clock() + self._ttl,
        )
        self._pending[op.token] = op
        return op

    def consume(
        self, token: str, tool_name: str, arguments: dict[str, Any]
    ) -> PendingOperation:
        """Validate and single-use-consume a confirmation token.

        Raises ToolError (without consuming) if the token is unknown, expired, or bound
        to a different tool/arguments — the caller must request a fresh preview."""
        self._evict_expired()
        op = self._pending.get(token)
        if op is None:
            raise ToolError(
                "Unknown or expired confirmation token; request a new preview by "
                "calling this tool again without `confirm`."
            )
        if op.tool_name != tool_name or op.arguments != dict(arguments):
            raise ToolError(
                "Confirmation token does not match this operation; request a new "
                "preview for the exact operation you intend to perform."
            )
        del self._pending[token]
        return op

    def _evict_expired(self) -> None:
        now = self._clock()
        for token in [t for t, op in self._pending.items() if op.expires_at <= now]:
            del self._pending[token]
