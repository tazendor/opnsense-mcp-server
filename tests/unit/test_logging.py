"""Verify OPNsenseClient emits structured diagnostic log lines to stderr."""

import httpx
import pytest
import respx

from opnsense_mcp.client import OPNsenseClient
from opnsense_mcp.config import Config
from opnsense_mcp.errors import OPNsenseAPIError


@pytest.fixture
def client_config() -> Config:
    return Config(
        url="https://opnsense.test",
        api_key="key",
        api_secret="secret",
    )


class TestGetLogging:
    @respx.mock
    async def test_successful_get_logs_success_outcome(
        self,
        client_config: Config,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        respx.get("https://opnsense.test/api/core/dashboard/get").mock(
            return_value=httpx.Response(200, json={"versions": {}})
        )
        async with OPNsenseClient(client_config) as client:
            await client.get("core/dashboard/get")

        err = capsys.readouterr().err
        assert "GET" in err
        assert "core/dashboard/get" in err
        assert "status=200" in err
        assert "outcome=success" in err

    @respx.mock
    async def test_failed_get_logs_error_outcome(
        self,
        client_config: Config,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        respx.get("https://opnsense.test/api/core/dashboard/get").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )
        async with OPNsenseClient(client_config) as client:
            with pytest.raises(OPNsenseAPIError):
                await client.get("core/dashboard/get")

        err = capsys.readouterr().err
        assert "GET" in err
        assert "status=401" in err
        assert "outcome=error" in err

    @respx.mock
    async def test_log_line_contains_timestamp(
        self,
        client_config: Config,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        respx.get("https://opnsense.test/api/firmware/status/check").mock(
            return_value=httpx.Response(200, json={})
        )
        async with OPNsenseClient(client_config) as client:
            await client.get("firmware/status/check")

        err = capsys.readouterr().err
        # ISO timestamp starts with year
        assert "202" in err


class TestPostLogging:
    @respx.mock
    async def test_successful_post_logs_success_outcome(
        self,
        client_config: Config,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        respx.post("https://opnsense.test/api/firewall/filter/search_rule").mock(
            return_value=httpx.Response(200, json={"rows": [], "total": 0})
        )
        async with OPNsenseClient(client_config) as client:
            await client.post(
                "firewall/filter/search_rule",
                {"current": 1, "rowCount": -1, "searchPhrase": ""},
            )

        err = capsys.readouterr().err
        assert "POST" in err
        assert "firewall/filter/search_rule" in err
        assert "status=200" in err
        assert "outcome=success" in err

    @respx.mock
    async def test_failed_post_logs_error_outcome(
        self,
        client_config: Config,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        respx.post("https://opnsense.test/api/firewall/filter/add_rule").mock(
            return_value=httpx.Response(400, json={"validations": {}})
        )
        async with OPNsenseClient(client_config) as client:
            with pytest.raises(OPNsenseAPIError):
                await client.post("firewall/filter/add_rule", {"rule": {}})

        err = capsys.readouterr().err
        assert "POST" in err
        assert "status=400" in err
        assert "outcome=error" in err


class TestGetTextLogging:
    @respx.mock
    async def test_successful_get_text_logs_success_outcome(
        self,
        client_config: Config,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        respx.get("https://opnsense.test/api/core/backup/download/this").mock(
            return_value=httpx.Response(200, text="<?xml version='1.0'?><opnsense/>")
        )
        async with OPNsenseClient(client_config) as client:
            await client.get_text("core/backup/download/this")

        err = capsys.readouterr().err
        assert "GET" in err
        assert "core/backup/download/this" in err
        assert "outcome=success" in err


class TestLogSanitization:
    @respx.mock
    async def test_cr_lf_stripped_from_path_in_log(
        self,
        client_config: Config,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        respx.get("https://opnsense.test/api/safe/path").mock(
            return_value=httpx.Response(200, json={})
        )
        async with OPNsenseClient(client_config) as client:
            await client.get("safe/path")

        err = capsys.readouterr().err
        assert "\r" not in err
        assert err.count("\n") <= 2
