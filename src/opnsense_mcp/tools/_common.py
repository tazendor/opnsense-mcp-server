"""Shared request helpers for domain tool modules.

Wrap OPNsenseAPIError from the client as a ToolError for MCP callers."""

from __future__ import annotations

from typing import Any

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.errors import OPNsenseAPIError, ToolError


async def get_or_raise(client: OPNsenseClient, path: str) -> dict[str, Any]:
    try:
        return await client.get(path)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def post_or_raise(
    client: OPNsenseClient, path: str, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    try:
        return await client.post(path, data)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc


async def get_list_or_raise(client: OPNsenseClient, path: str) -> list[dict[str, Any]]:
    try:
        return await client.get_list(path)
    except OPNsenseAPIError as exc:
        raise ToolError.from_api_error(exc) from exc
