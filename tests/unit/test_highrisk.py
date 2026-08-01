"""Unit tests for the shared high-risk preview→confirm→execute flow.

Covers FR-008 (no request before confirm), SC-003, and SC-004 (exactly-once)."""

from unittest.mock import AsyncMock

import pytest

from opnsense_mcp.confirmation import PendingOperationStore
from opnsense_mcp.errors import ToolError
from opnsense_mcp.highrisk import run_high_risk


class TestRunHighRisk:
    async def test_preview_returns_token_without_executing(
        self, mock_client: AsyncMock
    ) -> None:
        store = PendingOperationStore()
        execute = AsyncMock(return_value={"status": "ok"})
        result = await run_high_risk(
            mock_client,
            store,
            tool_name="system_reboot",
            arguments={},
            description="Will reboot.",
            confirm=None,
            execute=execute,
        )
        assert result["status"] == "confirmation_required"
        assert result["confirm_token"]
        assert result["description"] == "Will reboot."
        execute.assert_not_called()
        mock_client.log_preview.assert_called_once()

    async def test_confirmed_executes_exactly_once(
        self, mock_client: AsyncMock
    ) -> None:
        store = PendingOperationStore()
        execute = AsyncMock(return_value={"status": "ok"})
        preview = await run_high_risk(
            mock_client,
            store,
            tool_name="system_reboot",
            arguments={"a": 1},
            description="d",
            confirm=None,
            execute=execute,
        )
        token = preview["confirm_token"]
        result = await run_high_risk(
            mock_client,
            store,
            tool_name="system_reboot",
            arguments={"a": 1},
            description="d",
            confirm=token,
            execute=execute,
        )
        assert result == {"status": "ok"}
        execute.assert_awaited_once_with(token)

    async def test_reused_token_rejected(self, mock_client: AsyncMock) -> None:
        store = PendingOperationStore()
        execute = AsyncMock(return_value={"status": "ok"})
        preview = await run_high_risk(
            mock_client,
            store,
            tool_name="system_reboot",
            arguments={},
            description="d",
            confirm=None,
            execute=execute,
        )
        token = preview["confirm_token"]
        await run_high_risk(
            mock_client,
            store,
            tool_name="system_reboot",
            arguments={},
            description="d",
            confirm=token,
            execute=execute,
        )
        with pytest.raises(ToolError):
            await run_high_risk(
                mock_client,
                store,
                tool_name="system_reboot",
                arguments={},
                description="d",
                confirm=token,
                execute=execute,
            )
