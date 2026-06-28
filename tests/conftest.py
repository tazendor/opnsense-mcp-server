from unittest.mock import AsyncMock

import pytest

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.config import Config


@pytest.fixture
def test_config() -> Config:
    return Config(
        url="https://fake.opnsense.example",
        api_key="test-api-key",
        api_secret="test-api-secret",
    )


@pytest.fixture
def mock_client() -> AsyncMock:
    client: AsyncMock = AsyncMock(spec=OPNsenseClient)
    client.get = AsyncMock(return_value={})
    client.get_list = AsyncMock(return_value=[])
    client.get_text = AsyncMock(return_value="")
    client.post = AsyncMock(return_value={})
    return client
