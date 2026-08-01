from pathlib import Path

import pytest

from opnsense_mcp.config import Config


class TestConfigConstruction:
    def test_required_fields(self) -> None:
        cfg = Config(url="https://192.168.1.1", api_key="key", api_secret="secret")
        assert cfg.url == "https://192.168.1.1"
        assert cfg.api_key == "key"
        assert cfg.api_secret == "secret"

    def test_defaults(self) -> None:
        cfg = Config(url="https://192.168.1.1", api_key="key", api_secret="secret")
        assert cfg.verify_tls is True
        assert cfg.connect_timeout == 10.0
        assert cfg.read_timeout == 60.0
        assert cfg.transport == "stdio"
        assert cfg.http_host == "127.0.0.1"
        assert cfg.http_port == 8000


class TestConfigValidation:
    def test_rejects_http_url(self) -> None:
        with pytest.raises(ValueError, match="https://"):
            Config(url="http://192.168.1.1", api_key="key", api_secret="secret")

    def test_rejects_missing_api_key(self) -> None:
        with pytest.raises(ValueError, match="api_key"):
            Config(url="https://192.168.1.1", api_key="", api_secret="secret")

    def test_rejects_missing_api_secret(self) -> None:
        with pytest.raises(ValueError, match="api_secret"):
            Config(url="https://192.168.1.1", api_key="key", api_secret="")

    def test_rejects_zero_connect_timeout(self) -> None:
        with pytest.raises(ValueError, match="connect_timeout"):
            Config(
                url="https://192.168.1.1",
                api_key="key",
                api_secret="secret",
                connect_timeout=0.0,
            )

    def test_rejects_negative_read_timeout(self) -> None:
        with pytest.raises(ValueError, match="read_timeout"):
            Config(
                url="https://192.168.1.1",
                api_key="key",
                api_secret="secret",
                read_timeout=-1.0,
            )

    def test_rejects_port_zero(self) -> None:
        with pytest.raises(ValueError, match="http_port"):
            Config(
                url="https://192.168.1.1",
                api_key="key",
                api_secret="secret",
                http_port=0,
            )

    def test_rejects_port_above_max(self) -> None:
        with pytest.raises(ValueError, match="http_port"):
            Config(
                url="https://192.168.1.1",
                api_key="key",
                api_secret="secret",
                http_port=65536,
            )


class TestConfigFromEnv:
    def test_loads_required_fields(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPNSENSE_URL", "https://192.168.1.1")
        monkeypatch.setenv("OPNSENSE_API_KEY", "envkey")
        monkeypatch.setenv("OPNSENSE_API_SECRET", "envsecret")
        cfg = Config.from_env()
        assert cfg.url == "https://192.168.1.1"
        assert cfg.api_key == "envkey"
        assert cfg.api_secret == "envsecret"

    def test_loads_connect_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPNSENSE_URL", "https://192.168.1.1")
        monkeypatch.setenv("OPNSENSE_API_KEY", "key")
        monkeypatch.setenv("OPNSENSE_API_SECRET", "secret")
        monkeypatch.setenv("OPNSENSE_CONNECT_TIMEOUT", "5.0")
        assert Config.from_env().connect_timeout == 5.0

    def test_loads_read_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPNSENSE_URL", "https://192.168.1.1")
        monkeypatch.setenv("OPNSENSE_API_KEY", "key")
        monkeypatch.setenv("OPNSENSE_API_SECRET", "secret")
        monkeypatch.setenv("OPNSENSE_READ_TIMEOUT", "30.0")
        assert Config.from_env().read_timeout == 30.0

    def test_loads_http_transport(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPNSENSE_URL", "https://192.168.1.1")
        monkeypatch.setenv("OPNSENSE_API_KEY", "key")
        monkeypatch.setenv("OPNSENSE_API_SECRET", "secret")
        monkeypatch.setenv("OPNSENSE_TRANSPORT", "http")
        assert Config.from_env().transport == "http"

    def test_loads_verify_tls_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPNSENSE_URL", "https://192.168.1.1")
        monkeypatch.setenv("OPNSENSE_API_KEY", "key")
        monkeypatch.setenv("OPNSENSE_API_SECRET", "secret")
        monkeypatch.setenv("OPNSENSE_VERIFY_TLS", "false")
        assert Config.from_env().verify_tls is False

    def test_loads_http_host_and_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPNSENSE_URL", "https://192.168.1.1")
        monkeypatch.setenv("OPNSENSE_API_KEY", "key")
        monkeypatch.setenv("OPNSENSE_API_SECRET", "secret")
        monkeypatch.setenv("OPNSENSE_HTTP_HOST", "0.0.0.0")
        monkeypatch.setenv("OPNSENSE_HTTP_PORT", "9000")
        cfg = Config.from_env()
        assert cfg.http_host == "0.0.0.0"
        assert cfg.http_port == 9000


class TestConfigFromToml:
    def test_loads_required_fields(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'url = "https://192.168.1.1"\n'
            'api_key = "tomlkey"\n'
            'api_secret = "tomlsecret"\n'
        )
        cfg = Config.from_toml(config_file)
        assert cfg.url == "https://192.168.1.1"
        assert cfg.api_key == "tomlkey"
        assert cfg.api_secret == "tomlsecret"

    def test_loads_timeouts(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'url = "https://192.168.1.1"\n'
            'api_key = "key"\n'
            'api_secret = "secret"\n'
            "connect_timeout = 5.0\n"
            "read_timeout = 30.0\n"
        )
        cfg = Config.from_toml(config_file)
        assert cfg.connect_timeout == 5.0
        assert cfg.read_timeout == 30.0

    def test_loads_transport(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'url = "https://192.168.1.1"\n'
            'api_key = "key"\n'
            'api_secret = "secret"\n'
            'transport = "http"\n'
        )
        assert Config.from_toml(config_file).transport == "http"

    def test_loads_verify_tls_false(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'url = "https://192.168.1.1"\n'
            'api_key = "key"\n'
            'api_secret = "secret"\n'
            "verify_tls = false\n"
        )
        assert Config.from_toml(config_file).verify_tls is False


class TestConfigLoad:
    def test_env_overrides_toml_url(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'url = "https://toml.example.com"\n'
            'api_key = "tomlkey"\n'
            'api_secret = "tomlsecret"\n'
        )
        monkeypatch.setenv("OPNSENSE_URL", "https://env.example.com")
        monkeypatch.delenv("OPNSENSE_API_KEY", raising=False)
        monkeypatch.delenv("OPNSENSE_API_SECRET", raising=False)
        cfg = Config.load(toml_path=config_file)
        assert cfg.url == "https://env.example.com"

    def test_env_overrides_toml_key(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'url = "https://192.168.1.1"\n'
            'api_key = "tomlkey"\n'
            'api_secret = "tomlsecret"\n'
        )
        monkeypatch.setenv("OPNSENSE_API_KEY", "envkey")
        monkeypatch.delenv("OPNSENSE_URL", raising=False)
        monkeypatch.delenv("OPNSENSE_API_SECRET", raising=False)
        cfg = Config.load(toml_path=config_file)
        assert cfg.api_key == "envkey"

    def test_falls_back_to_toml_when_env_absent(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'url = "https://toml.example.com"\n'
            'api_key = "tomlkey"\n'
            'api_secret = "tomlsecret"\n'
        )
        for var in ("OPNSENSE_URL", "OPNSENSE_API_KEY", "OPNSENSE_API_SECRET"):
            monkeypatch.delenv(var, raising=False)
        cfg = Config.load(toml_path=config_file)
        assert cfg.url == "https://toml.example.com"
        assert cfg.api_key == "tomlkey"

    def test_toml_optional_when_env_provides_all(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPNSENSE_URL", "https://192.168.1.1")
        monkeypatch.setenv("OPNSENSE_API_KEY", "key")
        monkeypatch.setenv("OPNSENSE_API_SECRET", "secret")
        cfg = Config.load(toml_path=None)
        assert cfg.url == "https://192.168.1.1"


class TestConfirmTtlConfig:
    """FR-010 / plan.md: OPNSENSE_CONFIRM_TTL bounds how long a pending high-risk
    confirmation stays valid."""

    def test_default_confirm_ttl(self) -> None:
        cfg = Config(url="https://192.168.1.1", api_key="key", api_secret="secret")
        assert cfg.confirm_ttl_seconds == 120.0

    def test_rejects_non_positive_confirm_ttl(self) -> None:
        with pytest.raises(ValueError, match="confirm_ttl_seconds"):
            Config(
                url="https://192.168.1.1",
                api_key="key",
                api_secret="secret",
                confirm_ttl_seconds=0.0,
            )

    def test_loads_confirm_ttl_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPNSENSE_URL", "https://192.168.1.1")
        monkeypatch.setenv("OPNSENSE_API_KEY", "key")
        monkeypatch.setenv("OPNSENSE_API_SECRET", "secret")
        monkeypatch.setenv("OPNSENSE_CONFIRM_TTL", "30.0")
        assert Config.from_env().confirm_ttl_seconds == 30.0

    def test_loads_confirm_ttl_from_toml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'url = "https://192.168.1.1"\n'
            'api_key = "key"\n'
            'api_secret = "secret"\n'
            "confirm_ttl_seconds = 45.0\n"
        )
        assert Config.from_toml(config_file).confirm_ttl_seconds == 45.0

    def test_env_overrides_toml_confirm_ttl(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'url = "https://192.168.1.1"\n'
            'api_key = "key"\n'
            'api_secret = "secret"\n'
            "confirm_ttl_seconds = 45.0\n"
        )
        monkeypatch.setenv("OPNSENSE_CONFIRM_TTL", "30.0")
        for var in ("OPNSENSE_URL", "OPNSENSE_API_KEY", "OPNSENSE_API_SECRET"):
            monkeypatch.delenv(var, raising=False)
        assert Config.load(toml_path=config_file).confirm_ttl_seconds == 30.0
