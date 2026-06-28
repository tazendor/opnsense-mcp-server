from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from typing import Any

import httpx

from opnsense_mcp.config import Config
from opnsense_mcp.errors import OPNsenseAPIError, ToolError


class OPNsenseClient:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> OPNsenseClient:
        self._http = self._make_http()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    def _make_http(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._config.url,
            auth=httpx.BasicAuth(self._config.api_key, self._config.api_secret),
            verify=self._config.verify_tls,
            timeout=httpx.Timeout(
                connect=self._config.connect_timeout,
                read=self._config.read_timeout,
                write=None,
                pool=None,
            ),
        )

    @property
    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = self._make_http()
        return self._http

    async def aclose(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    def _log(
        self,
        method: str,
        path: str,
        status_code: int | None,
        outcome: str,
    ) -> None:
        record = {
            "ts": datetime.now(UTC).isoformat(),
            "method": method,
            "path": path.replace("\r", "").replace("\n", " "),
            "status_code": status_code,
            "outcome": outcome,
        }
        print(json.dumps(record), file=sys.stderr, flush=True)

    async def get(self, path: str) -> dict[str, Any]:
        try:
            response = await self._client.get(f"/api/{path}")
        except httpx.ConnectTimeout as exc:
            self._log("GET", path, None, "timeout")
            raise ToolError(f"Connect timeout exceeded for {path}") from exc
        except httpx.ReadTimeout as exc:
            self._log("GET", path, None, "timeout")
            raise ToolError(f"Read timeout exceeded for {path}") from exc
        except httpx.ConnectError as exc:
            self._log("GET", path, None, "error")
            raise ToolError(f"Could not connect to OPNsense for {path}") from exc

        if response.is_error:
            self._log("GET", path, response.status_code, "error")
            raise OPNsenseAPIError(
                status_code=response.status_code,
                body=_safe_json(response),
                path=path,
                method="GET",
            )

        self._log("GET", path, response.status_code, "success")
        result: dict[str, Any] = response.json()
        return result

    async def get_list(self, path: str) -> list[dict[str, Any]]:
        try:
            response = await self._client.get(f"/api/{path}")
        except httpx.ConnectTimeout as exc:
            self._log("GET", path, None, "timeout")
            raise ToolError(f"Connect timeout exceeded for {path}") from exc
        except httpx.ReadTimeout as exc:
            self._log("GET", path, None, "timeout")
            raise ToolError(f"Read timeout exceeded for {path}") from exc
        except httpx.ConnectError as exc:
            self._log("GET", path, None, "error")
            raise ToolError(f"Could not connect to OPNsense for {path}") from exc

        if response.is_error:
            self._log("GET", path, response.status_code, "error")
            raise OPNsenseAPIError(
                status_code=response.status_code,
                body=_safe_json(response),
                path=path,
                method="GET",
            )

        self._log("GET", path, response.status_code, "success")
        result: list[dict[str, Any]] = response.json()
        return result

    async def get_text(self, path: str) -> str:
        try:
            response = await self._client.get(f"/api/{path}")
        except httpx.ConnectTimeout as exc:
            self._log("GET", path, None, "timeout")
            raise ToolError(f"Connect timeout exceeded for {path}") from exc
        except httpx.ReadTimeout as exc:
            self._log("GET", path, None, "timeout")
            raise ToolError(f"Read timeout exceeded for {path}") from exc
        except httpx.ConnectError as exc:
            self._log("GET", path, None, "error")
            raise ToolError(f"Could not connect to OPNsense for {path}") from exc

        if response.is_error:
            self._log("GET", path, response.status_code, "error")
            raise OPNsenseAPIError(
                status_code=response.status_code,
                body=_safe_json(response),
                path=path,
                method="GET",
            )

        self._log("GET", path, response.status_code, "success")
        return response.text

    async def post(
        self, path: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        try:
            response = await self._client.post(f"/api/{path}", json=data)
        except httpx.ConnectTimeout as exc:
            self._log("POST", path, None, "timeout")
            raise ToolError(f"Connect timeout exceeded for {path}") from exc
        except httpx.ReadTimeout as exc:
            self._log("POST", path, None, "timeout")
            raise ToolError(f"Read timeout exceeded for {path}") from exc
        except httpx.ConnectError as exc:
            self._log("POST", path, None, "error")
            raise ToolError(f"Could not connect to OPNsense for {path}") from exc

        if response.is_error:
            self._log("POST", path, response.status_code, "error")
            raise OPNsenseAPIError(
                status_code=response.status_code,
                body=_safe_json(response),
                path=path,
                method="POST",
            )

        self._log("POST", path, response.status_code, "success")
        result: dict[str, Any] = response.json()
        return result


def _safe_json(response: httpx.Response) -> dict[str, Any]:
    try:
        body: dict[str, Any] = response.json()
        return body
    except ValueError:
        return {"raw": response.text}
