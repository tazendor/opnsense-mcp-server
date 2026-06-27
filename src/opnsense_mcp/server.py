from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.config import Config
from opnsense_mcp.tools import dhcp, dns, firewall, interfaces, routes, services, system


def create_server(config: Config) -> FastMCP:
    mcp: FastMCP = FastMCP(
        "opnsense-mcp-server",
        host=config.http_host,
        port=config.http_port,
    )
    client = OPNsenseClient(config)
    for module in (system, firewall, interfaces, routes, dhcp, dns, services):
        module.register_tools(mcp, client)
    return mcp
