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


def _log(msg: str, http_mode: bool) -> None:
    print(msg, file=sys.stderr)
    if http_mode:
        print(msg, flush=True)


async def _startup_check(config: Config, client: OPNsenseClient) -> None:
    http_mode = config.transport == "http"
    if not config.verify_tls:
        _log("TLS verification disabled — use only on trusted networks", http_mode)
    await client.get("core/system/status")
    _log("Startup complete", http_mode)


def main() -> None:
    try:
        config = Config.load(_DEFAULT_CONFIG)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    http_mode = config.transport == "http"
    client = OPNsenseClient(config)
    try:
        asyncio.run(_startup_check(config, client))
    except OPNsenseAPIError as exc:
        msg = (
            f"Startup failed: OPNsense returned {exc.status_code}"
            f" for {exc.path} — {exc.body}"
        )
        _log(msg, http_mode)
        sys.exit(1)
    except ToolError as exc:
        _log(f"Cannot reach OPNsense: {exc}", http_mode)
        sys.exit(1)

    mcp = create_server(config, client)

    if http_mode:
        _log(
            "WARNING: HTTP transport enabled — payload limits, rate limiting, "
            "and client authentication are NOT enforced; "
            "expose only on trusted local networks",
            http_mode=True,
        )
        _log(
            f"Listening on {config.http_host}:{config.http_port}",
            http_mode=True,
        )
        try:
            mcp.run(transport="streamable-http")
        except OSError as exc:
            if exc.errno == errno.EADDRINUSE:
                _log(
                    f"Port {config.http_port} is already in use"
                    f" — choose a different OPNSENSE_HTTP_PORT",
                    http_mode=True,
                )
                sys.exit(1)
            raise
    else:
        mcp.run(transport="stdio")
