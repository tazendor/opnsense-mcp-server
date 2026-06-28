"""Verify OPNsenseClient emits structured JSON log lines to stderr."""

import json

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


def _parse_log(err: str) -> dict:  # type: ignore[type-arg]
    line = err.strip().splitlines()[0]
    return json.loads(line)  # type: ignore[no-any-return]


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

        record = _parse_log(capsys.readouterr().err)
        assert record["method"] == "GET"
        assert record["path"] == "core/dashboard/get"
        assert record["status_code"] == 200
        assert record["outcome"] == "success"

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

        record = _parse_log(capsys.readouterr().err)
        assert record["method"] == "GET"
        assert record["status_code"] == 401
        assert record["outcome"] == "error"

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

        record = _parse_log(capsys.readouterr().err)
        assert record["ts"].startswith("202")

    @respx.mock
    async def test_log_line_is_valid_json(
        self,
        client_config: Config,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        respx.get("https://opnsense.test/api/core/system/status").mock(
            return_value=httpx.Response(200, json={})
        )
        async with OPNsenseClient(client_config) as client:
            await client.get("core/system/status")

        err = capsys.readouterr().err.strip()
        parsed = json.loads(err)
        assert {"ts", "method", "path", "status_code", "outcome"} <= parsed.keys()


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

        record = _parse_log(capsys.readouterr().err)
        assert record["method"] == "POST"
        assert record["path"] == "firewall/filter/search_rule"
        assert record["status_code"] == 200
        assert record["outcome"] == "success"

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

        record = _parse_log(capsys.readouterr().err)
        assert record["method"] == "POST"
        assert record["status_code"] == 400
        assert record["outcome"] == "error"


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

        record = _parse_log(capsys.readouterr().err)
        assert record["method"] == "GET"
        assert record["path"] == "core/backup/download/this"
        assert record["outcome"] == "success"


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
