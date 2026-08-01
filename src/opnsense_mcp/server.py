from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.config import Config
from opnsense_mcp.confirmation import PendingOperationStore
from opnsense_mcp.tools import (
    dhcp,
    dns,
    firewall,
    ids,
    interfaces,
    openvpn,
    routes,
    services,
    system,
)


def create_server(config: Config, client: OPNsenseClient | None = None) -> FastMCP:
    if client is None:
        client = OPNsenseClient(config)

    # Process-local, non-persistent confirmation store for high-risk operations.
    store = PendingOperationStore(ttl_seconds=config.confirm_ttl_seconds)

    @asynccontextmanager
    async def lifespan(app: FastMCP) -> AsyncGenerator[None, None]:
        async with client:
            yield

    mcp: FastMCP = FastMCP(
        "opnsense-mcp-server",
        host=config.http_host,
        port=config.http_port,
        lifespan=lifespan,
    )
    # Standard (read/stage-then-apply) domains.
    for module in (system, firewall, interfaces, routes, dhcp, dns, ids, services):
        module.register_tools(mcp, client)
    # Domains that include high-risk tools also receive the confirmation store.
    openvpn.register_tools(mcp, client, store)
    return mcp
