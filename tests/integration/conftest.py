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


@pytest.fixture
def require_write_optin() -> None:
    """Safety gate for integration tests that MUTATE the target OPNsense.

    Read-only integration tests run whenever a config/URL is present, but a config
    can point at a production firewall (opnsense.internal), so any test that creates,
    changes, deletes, reboots, revokes, or otherwise mutates state must additionally
    require the operator to opt in explicitly via OPNSENSE_INTEGRATION_WRITES=1.
    This prevents an accidental full-suite run from writing to a live box."""
    if os.environ.get("OPNSENSE_INTEGRATION_WRITES") != "1":
        pytest.skip(
            "write/mutating integration test — set OPNSENSE_INTEGRATION_WRITES=1 to"
            " run against a disposable test instance (never production)"
        )
