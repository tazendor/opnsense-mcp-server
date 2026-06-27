from __future__ import annotations

import asyncio
import sys

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.config import Config
from opnsense_mcp.errors import OPNsenseAPIError, ToolError
from opnsense_mcp.server import create_server


async def _probe(config: Config) -> None:
    async with OPNsenseClient(config) as client:
        await client.get("core/dashboard/get")


def main() -> None:
    try:
        config = Config.load()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        asyncio.run(_probe(config))
    except OPNsenseAPIError as exc:
        print(
            f"OPNsense authentication failed ({exc.status_code}) on {exc.path}",
            file=sys.stderr,
        )
        sys.exit(1)
    except ToolError as exc:
        print(f"Cannot reach OPNsense: {exc}", file=sys.stderr)
        sys.exit(1)

    mcp = create_server(config)

    if config.transport == "http":
        try:
            mcp.run(transport="streamable-http")
        except OSError as exc:
            raise OSError(
                f"Cannot bind HTTP server on"
                f" {config.http_host}:{config.http_port}: {exc}"
            ) from exc
    else:
        mcp.run(transport="stdio")
