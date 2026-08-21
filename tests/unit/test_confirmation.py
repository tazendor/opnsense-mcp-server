"""Unit tests for the confirm-then-execute safety layer (FR-007–FR-011)."""

import pytest

from opnsense_mcp.confirmation import PendingOperation, PendingOperationStore
from opnsense_mcp.errors import ToolError


class _Clock:
    """Controllable monotonic clock for deterministic expiry tests."""

    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


class TestCreate:
    def test_returns_pending_operation_with_fields(self) -> None:
        store = PendingOperationStore(ttl_seconds=120.0)
        op = store.create("system_reboot", {"x": 1}, "Will reboot the firewall.")
        assert isinstance(op, PendingOperation)
        assert op.tool_name == "system_reboot"
        assert op.arguments == {"x": 1}
        assert op.description == "Will reboot the firewall."
        assert op.token

    def test_tokens_are_unique(self) -> None:
        store = PendingOperationStore()
        tokens = {store.create("t", {}, "d").token for _ in range(50)}
        assert len(tokens) == 50

    def test_expiry_is_in_the_future(self) -> None:
        clock = _Clock()
        store = PendingOperationStore(ttl_seconds=120.0, clock=clock)
        op = store.create("t", {}, "d")
        assert op.expires_at == 1000.0 + 120.0

    def test_stored_arguments_are_copied(self) -> None:
        store = PendingOperationStore()
        args = {"a": 1}
        op = store.create("t", args, "d")
        args["a"] = 999
        assert op.arguments == {"a": 1}


class TestConsume:
    def test_valid_token_returns_operation(self) -> None:
        store = PendingOperationStore()
        op = store.create("system_reboot", {"a": 1}, "d")
        got = store.consume(op.token, "system_reboot", {"a": 1})
        assert got.token == op.token

    def test_single_use(self) -> None:
        store = PendingOperationStore()
        op = store.create("system_reboot", {}, "d")
        store.consume(op.token, "system_reboot", {})
        with pytest.raises(ToolError):
            store.consume(op.token, "system_reboot", {})

    def test_wrong_tool_name_rejected(self) -> None:
        store = PendingOperationStore()
        op = store.create("system_reboot", {}, "d")
        with pytest.raises(ToolError):
            store.consume(op.token, "system_halt", {})

    def test_mismatched_arguments_rejected(self) -> None:
        store = PendingOperationStore()
        op = store.create("system_reboot", {"a": 1}, "d")
        with pytest.raises(ToolError):
            store.consume(op.token, "system_reboot", {"a": 2})

    def test_mismatch_does_not_consume_for_real_owner(self) -> None:
        store = PendingOperationStore()
        op = store.create("system_reboot", {"a": 1}, "d")
        with pytest.raises(ToolError):
            store.consume(op.token, "system_reboot", {"a": 2})
        # The legitimate caller can still confirm afterwards.
        assert store.consume(op.token, "system_reboot", {"a": 1}).token == op.token

    def test_unknown_token_rejected(self) -> None:
        store = PendingOperationStore()
        with pytest.raises(ToolError):
            store.consume("nope", "system_reboot", {})

    def test_expired_token_rejected(self) -> None:
        clock = _Clock()
        store = PendingOperationStore(ttl_seconds=120.0, clock=clock)
        op = store.create("system_reboot", {}, "d")
        clock.now += 121.0
        with pytest.raises(ToolError):
            store.consume(op.token, "system_reboot", {})
