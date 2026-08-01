"""Unit tests for private-key redaction on read responses (FR-017)."""

from opnsense_mcp.redaction import (
    redact_private_keys,
    redact_rows,
    redact_wrapped,
)


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


class TestRedactRows:
    def test_redacts_each_row(self) -> None:
        resp = {
            "rows": [
                {"name": "a", "privkey": "S1"},
                {"name": "b", "privkey": "S2"},
            ],
            "total": 2,
        }
        out = redact_rows(resp, frozenset({"privkey"}))
        assert all("privkey" not in r for r in out["rows"])
        assert out["total"] == 2

    def test_noop_without_rows(self) -> None:
        resp = {"result": "ok"}
        assert redact_rows(resp, frozenset({"privkey"})) == {"result": "ok"}


class TestRedactWrapped:
    def test_redacts_inner_object(self) -> None:
        resp = {"cert": {"descr": "web", "prv": "SECRET", "crt": "PUB"}}
        out = redact_wrapped(resp, "cert", frozenset({"prv"}))
        assert "prv" not in out["cert"]
        assert out["cert"]["crt"] == "PUB"

    def test_noop_when_wrapper_absent(self) -> None:
        resp = {"other": {"prv": "S"}}
        assert redact_wrapped(resp, "cert", frozenset({"prv"})) == resp
