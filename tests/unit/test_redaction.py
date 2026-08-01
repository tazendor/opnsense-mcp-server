"""Unit tests for private-key redaction on read responses (FR-017)."""

from opnsense_mcp.redaction import redact_private_keys


class TestRedactPrivateKeys:
    def test_removes_named_fields(self) -> None:
        obj = {"name": "srv", "privkey": "SECRET", "pubkey": "PUBLIC"}
        out = redact_private_keys(obj, frozenset({"privkey"}))
        assert "privkey" not in out
        assert out["pubkey"] == "PUBLIC"
        assert out["name"] == "srv"

    def test_removes_multiple_fields(self) -> None:
        obj = {"prv": "a", "prv_payload": "b", "descr": "c"}
        out = redact_private_keys(obj, frozenset({"prv", "prv_payload"}))
        assert out == {"descr": "c"}

    def test_noop_when_absent(self) -> None:
        obj = {"pubkey": "PUBLIC"}
        out = redact_private_keys(obj, frozenset({"privkey"}))
        assert out == {"pubkey": "PUBLIC"}

    def test_does_not_mutate_input(self) -> None:
        obj = {"privkey": "SECRET", "name": "x"}
        redact_private_keys(obj, frozenset({"privkey"}))
        assert obj["privkey"] == "SECRET"

    def test_returns_a_copy(self) -> None:
        obj = {"name": "x"}
        out = redact_private_keys(obj, frozenset({"privkey"}))
        assert out is not obj
