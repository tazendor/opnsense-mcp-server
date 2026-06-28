import pytest

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.tools.ids import _ids_alert_list, _ids_ruleset_list


@pytest.mark.integration
class TestIdsIntegration:
    async def test_alert_list_has_rows_key(self, live_client: OPNsenseClient) -> None:
        result = await _ids_alert_list(live_client)
        assert "rows" in result
        assert "total" in result

    async def test_ruleset_list_has_rows_key(self, live_client: OPNsenseClient) -> None:
        result = await _ids_ruleset_list(live_client)
        assert "rows" in result
        assert "total" in result

    async def test_ruleset_list_search_phrase(
        self, live_client: OPNsenseClient
    ) -> None:
        result = await _ids_ruleset_list(live_client, search_phrase="emerging")
        assert "rows" in result
