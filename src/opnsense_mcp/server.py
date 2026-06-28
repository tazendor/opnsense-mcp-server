from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.config import Config
from opnsense_mcp.tools import dhcp, dns, firewall, interfaces, routes, services, system


def create_server(
    config: Config, client: OPNsenseClient | None = None
) -> FastMCP:
    if client is None:
        client = OPNsenseClient(config)

    @asynccontextmanager
    async def lifespan(app: FastMCP) -> AsyncGenerator[None, None]:
        try:
            yield
        finally:
            await client.aclose()

    mcp: FastMCP = FastMCP(
        "opnsense-mcp-server",
        host=config.http_host,
        port=config.http_port,
        lifespan=lifespan,
    )
    for module in (system, firewall, interfaces, routes, dhcp, dns, services):
        module.register_tools(mcp, client)
    return mcp
