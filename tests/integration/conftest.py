import os
from collections.abc import AsyncGenerator

import pytest

from opnsense_mcp.__main__ import _DEFAULT_CONFIG
from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.config import Config


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: mark test as requiring a live OPNsense instance",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    if os.environ.get("OPNSENSE_URL") or _DEFAULT_CONFIG.exists():
        return
    reason = (
        "OPNSENSE_URL not set and ~/.config/opnsense-mcp/config.toml not found"
        " — live OPNsense instance required"
    )
    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if item.get_closest_marker("integration"):
            item.add_marker(skip)


@pytest.fixture
async def live_client() -> AsyncGenerator[OPNsenseClient, None]:
    config = Config.load(_DEFAULT_CONFIG)
    async with OPNsenseClient(config) as client:
        yield client
