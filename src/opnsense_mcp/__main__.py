from __future__ import annotations

import asyncio
import errno
import sys
from pathlib import Path

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.config import Config
from opnsense_mcp.errors import OPNsenseAPIError, ToolError
from opnsense_mcp.server import create_server

_DEFAULT_CONFIG = Path.home() / ".config" / "opnsense-mcp" / "config.toml"


async def _startup_check(config: Config) -> None:
    if not config.verify_tls:
        print(
            "TLS verification disabled — use only on trusted networks",
            file=sys.stderr,
        )
    async with OPNsenseClient(config) as client:
        await client.get("core/dashboard/get")
    print("Startup complete", file=sys.stderr)


def main() -> None:
    try:
        config = Config.load(_DEFAULT_CONFIG)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        asyncio.run(_startup_check(config))
    except OPNsenseAPIError as exc:
        print(
            f"Startup failed: OPNsense returned {exc.status_code}"
            f" for {exc.path} — {exc.body}",
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
            if exc.errno == errno.EADDRINUSE:
                print(
                    f"Port {config.http_port} is already in use"
                    f" — choose a different OPNSENSE_HTTP_PORT",
                    file=sys.stderr,
                )
                sys.exit(1)
            raise
    else:
        mcp.run(transport="stdio")
