from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


def _bool_from_str(value: str) -> bool:
    return value.lower() not in ("false", "0", "no")


@dataclass
class Config:
    url: str
    api_key: str
    api_secret: str
    verify_tls: bool = True
    connect_timeout: float = 10.0
    read_timeout: float = 60.0
    transport: Literal["stdio", "http"] = "stdio"
    http_host: str = "127.0.0.1"
    http_port: int = 8000
    confirm_ttl_seconds: float = 120.0

    def __post_init__(self) -> None:
        if not self.url.startswith("https://"):
            raise ValueError("url must use https://")
        if not self.api_key:
            raise ValueError("api_key is required")
        if not self.api_secret:
            raise ValueError("api_secret is required")
        if self.connect_timeout <= 0:
            raise ValueError("connect_timeout must be positive")
        if self.read_timeout <= 0:
            raise ValueError("read_timeout must be positive")
        if not (1 <= self.http_port <= 65535):
            raise ValueError("http_port must be 1–65535")
        if self.confirm_ttl_seconds <= 0:
            raise ValueError("confirm_ttl_seconds must be positive")

    @classmethod
    def from_env(cls) -> Config:
        transport_raw = os.environ.get("OPNSENSE_TRANSPORT", "stdio")
        transport: Literal["stdio", "http"] = (
            "http" if transport_raw == "http" else "stdio"
        )
        return cls(
            url=os.environ.get("OPNSENSE_URL", ""),
            api_key=os.environ.get("OPNSENSE_API_KEY", ""),
            api_secret=os.environ.get("OPNSENSE_API_SECRET", ""),
            verify_tls=_bool_from_str(os.environ.get("OPNSENSE_VERIFY_TLS", "true")),
            connect_timeout=float(os.environ.get("OPNSENSE_CONNECT_TIMEOUT", "10.0")),
            read_timeout=float(os.environ.get("OPNSENSE_READ_TIMEOUT", "60.0")),
            transport=transport,
            http_host=os.environ.get("OPNSENSE_HTTP_HOST", "127.0.0.1"),
            http_port=int(os.environ.get("OPNSENSE_HTTP_PORT", "8000")),
            confirm_ttl_seconds=float(os.environ.get("OPNSENSE_CONFIRM_TTL", "120.0")),
        )

    @classmethod
    def from_toml(cls, path: Path) -> Config:
        with open(path, "rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
        transport_raw = str(raw.get("transport", "stdio"))
        transport: Literal["stdio", "http"] = (
            "http" if transport_raw == "http" else "stdio"
        )
        return cls(
            url=str(raw["url"]),
            api_key=str(raw["api_key"]),
            api_secret=str(raw["api_secret"]),
            verify_tls=bool(raw.get("verify_tls", True)),
            connect_timeout=float(raw.get("connect_timeout", 10.0)),
            read_timeout=float(raw.get("read_timeout", 60.0)),
            transport=transport,
            http_host=str(raw.get("http_host", "127.0.0.1")),
            http_port=int(raw.get("http_port", 8000)),
            confirm_ttl_seconds=float(raw.get("confirm_ttl_seconds", 120.0)),
        )

    @classmethod
    def load(cls, toml_path: Path | None = None) -> Config:
        raw: dict[str, Any] = {}
        if toml_path is not None and toml_path.exists():
            with open(toml_path, "rb") as f:
                raw = tomllib.load(f)

        def _s(key: str, default: str = "") -> str:
            env = f"OPNSENSE_{key.upper()}"
            if (v := os.environ.get(env)) is not None:
                return v
            return str(raw.get(key, default))

        def _f(key: str, default: float) -> float:
            env = f"OPNSENSE_{key.upper()}"
            if (v := os.environ.get(env)) is not None:
                return float(v)
            return float(raw.get(key, default))

        def _i(key: str, default: int) -> int:
            env = f"OPNSENSE_{key.upper()}"
            if (v := os.environ.get(env)) is not None:
                return int(v)
            return int(raw.get(key, default))

        def _b(key: str, default: bool) -> bool:
            env = f"OPNSENSE_{key.upper()}"
            if (v := os.environ.get(env)) is not None:
                return _bool_from_str(v)
            return bool(raw.get(key, default))

        transport_raw = _s("transport", "stdio")
        transport: Literal["stdio", "http"] = (
            "http" if transport_raw == "http" else "stdio"
        )
        # confirm_ttl uses the env name OPNSENSE_CONFIRM_TTL (not the generic
        # OPNSENSE_CONFIRM_TTL_SECONDS the field name would imply), per plan.md.
        confirm_ttl_env = os.environ.get("OPNSENSE_CONFIRM_TTL")
        confirm_ttl = (
            float(confirm_ttl_env)
            if confirm_ttl_env is not None
            else float(raw.get("confirm_ttl_seconds", 120.0))
        )
        return cls(
            url=_s("url"),
            api_key=_s("api_key"),
            api_secret=_s("api_secret"),
            verify_tls=_b("verify_tls", True),
            connect_timeout=_f("connect_timeout", 10.0),
            read_timeout=_f("read_timeout", 60.0),
            transport=transport,
            http_host=_s("http_host", "127.0.0.1"),
            http_port=_i("http_port", 8000),
            confirm_ttl_seconds=confirm_ttl,
        )
