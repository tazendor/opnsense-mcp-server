"""Representative Trust/PKI tests.

The contract scanner separately guarantees all 16 tools are registered/documented."""

from unittest.mock import AsyncMock

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.confirmation import PendingOperationStore
from opnsense_mcp.tools import trust

UUID = "12345678-1234-1234-1234-123456789abc"


def _fn(mock_client: AsyncMock, name: str, store: PendingOperationStore | None = None):  # type: ignore[no-untyped-def]
    mcp = FastMCP("t")
    trust.register_tools(mcp, mock_client, store or PendingOperationStore())
    return mcp._tool_manager._tools[name].fn


class TestRedaction:
    async def test_cert_list_redacts_prv(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {
            "rows": [{"descr": "web", "prv": "SECRET", "prv_payload": "S2"}]
        }
        result = await _fn(mock_client, "trust_certificate_list")()
        row = result["rows"][0]
        assert "prv" not in row and "prv_payload" not in row

    async def test_ca_get_redacts_prv(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"ca": {"descr": "root", "prv": "SECRET"}}
        result = await _fn(mock_client, "trust_ca_get")(UUID)
        assert "prv" not in result["ca"]

    async def test_export_not_redacted(self, mock_client: AsyncMock) -> None:
        mock_client.get.return_value = {"payload": "-----BEGIN PRIVATE KEY-----"}
        result = await _fn(mock_client, "trust_certificate_export")(UUID, "prv")
        assert "payload" in result
        mock_client.get.assert_called_once_with(f"trust/cert/generate_file/{UUID}/prv")


class TestRevokeHighRisk:
    async def test_preview_no_crl_post(self, mock_client: AsyncMock) -> None:
        store = PendingOperationStore()
        mock_client.get.return_value = {"cert": {"caref": "CA1", "refid": "R1"}}
        fn = _fn(mock_client, "trust_certificate_revoke", store)
        result = await fn(uuid=UUID)
        assert result["status"] == "confirmation_required"
        assert "R1" in result["description"]
        mock_client.post.assert_not_called()

    async def test_confirmed_does_crl_read_modify_write(
        self, mock_client: AsyncMock
    ) -> None:
        store = PendingOperationStore()
        mock_client.get.side_effect = [
            {"cert": {"caref": "CA1", "refid": "R1"}},  # preview cert get
            {"cert": {"caref": "CA1", "refid": "R1"}},  # (unused re-eval guard)
            {"crl": {"revoked_reason_0": ""}},  # execute crl get
        ]
        fn = _fn(mock_client, "trust_certificate_revoke", store)
        preview = await fn(uuid=UUID)
        mock_client.get.side_effect = [
            {"cert": {"caref": "CA1", "refid": "R1"}},
            {"crl": {"revoked_reason_0": ""}},
        ]
        mock_client.post.return_value = {"result": "saved"}
        await fn(uuid=UUID, confirm=preview["confirm_token"])
        args = mock_client.post.call_args
        assert args.args[0] == "trust/crl/set/CA1"
        assert "R1" in args.args[1]["crl"]["revoked_reason_0"]
