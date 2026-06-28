"""Startup validation and transport configuration tests (T037, T038)."""

import errno
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from opnsense_mcp.__main__ import _DEFAULT_CONFIG, main
from opnsense_mcp.config import Config
from opnsense_mcp.errors import OPNsenseAPIError, ToolError


@pytest.fixture
def base_config() -> Config:
    return Config(
        url="https://opnsense.test",
        api_key="testkey",
        api_secret="testsecret",
    )


@pytest.fixture
def mock_client_cm() -> AsyncMock:
    cm: AsyncMock = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=cm)
    cm.__aexit__ = AsyncMock(return_value=False)
    cm.get = AsyncMock(return_value={})
    return cm


class TestStartupValidation:
    def test_successful_startup_logs_complete(
        self,
        base_config: Config,
        mock_client_cm: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("opnsense_mcp.__main__.Config.load", lambda _: base_config)
        monkeypatch.setattr(
            "opnsense_mcp.__main__.OPNsenseClient",
            MagicMock(return_value=mock_client_cm),
        )
        mock_mcp = MagicMock()
        monkeypatch.setattr(
            "opnsense_mcp.__main__.create_server", lambda c, client=None: mock_mcp
        )

        main()

        assert "Startup complete" in capsys.readouterr().err

    def test_auth_failure_exits_1_with_status_in_message(
        self,
        base_config: Config,
        mock_client_cm: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_client_cm.get.side_effect = OPNsenseAPIError(
            status_code=401,
            body={"message": "Unauthorized"},
            path="core/dashboard/get",
            method="GET",
        )
        monkeypatch.setattr("opnsense_mcp.__main__.Config.load", lambda _: base_config)
        monkeypatch.setattr(
            "opnsense_mcp.__main__.OPNsenseClient",
            MagicMock(return_value=mock_client_cm),
        )

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        assert "401" in capsys.readouterr().err

    def test_connection_error_exits_1_with_host_message(
        self,
        base_config: Config,
        mock_client_cm: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_client_cm.get.side_effect = ToolError(
            "Could not connect to OPNsense for core/dashboard/get"
        )
        monkeypatch.setattr("opnsense_mcp.__main__.Config.load", lambda _: base_config)
        monkeypatch.setattr(
            "opnsense_mcp.__main__.OPNsenseClient",
            MagicMock(return_value=mock_client_cm),
        )

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "reach" in err.lower() or "connect" in err.lower()

    def test_tls_disabled_logs_warning(
        self,
        mock_client_cm: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        config = Config(
            url="https://opnsense.test",
            api_key="k",
            api_secret="s",
            verify_tls=False,
        )
        monkeypatch.setattr("opnsense_mcp.__main__.Config.load", lambda _: config)
        monkeypatch.setattr(
            "opnsense_mcp.__main__.OPNsenseClient",
            MagicMock(return_value=mock_client_cm),
        )
        mock_mcp = MagicMock()
        monkeypatch.setattr(
            "opnsense_mcp.__main__.create_server", lambda c, client=None: mock_mcp
        )

        main()

        err = capsys.readouterr().err
        assert "TLS" in err or "tls" in err.lower()


class TestTransportConfiguration:
    def test_stdio_transport_calls_stdio_run(
        self,
        base_config: Config,
        mock_client_cm: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("opnsense_mcp.__main__.Config.load", lambda _: base_config)
        monkeypatch.setattr(
            "opnsense_mcp.__main__.OPNsenseClient",
            MagicMock(return_value=mock_client_cm),
        )
        mock_mcp = MagicMock()
        monkeypatch.setattr(
            "opnsense_mcp.__main__.create_server", lambda c, client=None: mock_mcp
        )

        main()

        mock_mcp.run.assert_called_once_with(transport="stdio")

    def test_http_transport_calls_streamable_http_run(
        self,
        mock_client_cm: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = Config(
            url="https://opnsense.test",
            api_key="k",
            api_secret="s",
            transport="http",
            http_host="127.0.0.1",
            http_port=8080,
        )
        monkeypatch.setattr("opnsense_mcp.__main__.Config.load", lambda _: config)
        monkeypatch.setattr(
            "opnsense_mcp.__main__.OPNsenseClient",
            MagicMock(return_value=mock_client_cm),
        )
        mock_mcp = MagicMock()
        monkeypatch.setattr(
            "opnsense_mcp.__main__.create_server", lambda c, client=None: mock_mcp
        )

        main()

        mock_mcp.run.assert_called_once_with(transport="streamable-http")

    def test_port_conflict_exits_1_with_port_in_message(
        self,
        mock_client_cm: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        config = Config(
            url="https://opnsense.test",
            api_key="k",
            api_secret="s",
            transport="http",
            http_host="127.0.0.1",
            http_port=8080,
        )
        monkeypatch.setattr("opnsense_mcp.__main__.Config.load", lambda _: config)
        monkeypatch.setattr(
            "opnsense_mcp.__main__.OPNsenseClient",
            MagicMock(return_value=mock_client_cm),
        )
        mock_mcp = MagicMock()
        mock_mcp.run.side_effect = OSError(errno.EADDRINUSE, "Address already in use")
        monkeypatch.setattr(
            "opnsense_mcp.__main__.create_server", lambda c, client=None: mock_mcp
        )

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        assert "8080" in capsys.readouterr().err


class TestDefaultConfigPath:
    def test_default_path_is_user_config_toml(self) -> None:
        expected = Path.home() / ".config" / "opnsense-mcp" / "config.toml"
        assert expected == _DEFAULT_CONFIG

    def test_main_passes_default_path_to_config_load(
        self,
        base_config: Config,
        mock_client_cm: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_load = MagicMock(return_value=base_config)
        monkeypatch.setattr("opnsense_mcp.__main__.Config.load", mock_load)
        monkeypatch.setattr(
            "opnsense_mcp.__main__.OPNsenseClient",
            MagicMock(return_value=mock_client_cm),
        )
        mock_mcp = MagicMock()
        monkeypatch.setattr(
            "opnsense_mcp.__main__.create_server", lambda c, client=None: mock_mcp
        )

        main()

        mock_load.assert_called_once_with(_DEFAULT_CONFIG)

    def test_main_passes_client_to_create_server(
        self,
        base_config: Config,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value={})
        monkeypatch.setattr("opnsense_mcp.__main__.Config.load", lambda _: base_config)
        monkeypatch.setattr(
            "opnsense_mcp.__main__.OPNsenseClient",
            MagicMock(return_value=mock_client),
        )
        mock_mcp = MagicMock()
        mock_create = MagicMock(return_value=mock_mcp)
        monkeypatch.setattr("opnsense_mcp.__main__.create_server", mock_create)

        main()

        mock_create.assert_called_once_with(base_config, mock_client)
