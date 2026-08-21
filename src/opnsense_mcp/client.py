from __future__ import annotations

import json
import sys
import uuid
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
        req_id: str,
        token: str | None = None,
    ) -> None:
        record: dict[str, object] = {
            "ts": datetime.now(UTC).isoformat(),
            "req_id": req_id,
            "method": method,
            "path": path.replace("\r", "").replace("\n", " "),
            "status_code": status_code,
            "outcome": outcome,
        }
        if token is not None:
            record["token"] = token
        print(json.dumps(record), file=sys.stderr, flush=True)

    def log_preview(
        self, tool_name: str, arguments: dict[str, Any], token: str
    ) -> None:
        """Emit a diagnostic record for a high-risk operation preview (FR-011/SC-005).

        Makes no HTTP request. Uses the same stderr log stream as real requests so an
        operator can audit both the preview and the later confirmed execution — which
        shares the same ``token`` — without the MCP client's session history."""
        record: dict[str, object] = {
            "ts": datetime.now(UTC).isoformat(),
            "req_id": str(uuid.uuid4()),
            "method": None,
            "path": None,
            "status_code": None,
            "outcome": "preview",
            "tool": tool_name,
            "token": token,
        }
        print(json.dumps(record), file=sys.stderr, flush=True)

    async def get(self, path: str) -> dict[str, Any]:
        req_id = str(uuid.uuid4())
        try:
            response = await self._client.get(f"/api/{path}")
        except httpx.ConnectTimeout as exc:
            self._log("GET", path, None, "timeout", req_id)
            raise ToolError(f"Connect timeout exceeded for {path}") from exc
        except httpx.ReadTimeout as exc:
            self._log("GET", path, None, "timeout", req_id)
            raise ToolError(f"Read timeout exceeded for {path}") from exc
        except httpx.ConnectError as exc:
            self._log("GET", path, None, "error", req_id)
            raise ToolError(f"Could not connect to OPNsense for {path}") from exc

        if response.is_error:
            self._log("GET", path, response.status_code, "error", req_id)
            raise OPNsenseAPIError(
                status_code=response.status_code,
                body=_safe_json(response),
                path=path,
                method="GET",
            )

        self._log("GET", path, response.status_code, "success", req_id)
        result: dict[str, Any] = response.json()
        return result

    async def get_list(self, path: str) -> list[dict[str, Any]]:
        req_id = str(uuid.uuid4())
        try:
            response = await self._client.get(f"/api/{path}")
        except httpx.ConnectTimeout as exc:
            self._log("GET", path, None, "timeout", req_id)
            raise ToolError(f"Connect timeout exceeded for {path}") from exc
        except httpx.ReadTimeout as exc:
            self._log("GET", path, None, "timeout", req_id)
            raise ToolError(f"Read timeout exceeded for {path}") from exc
        except httpx.ConnectError as exc:
            self._log("GET", path, None, "error", req_id)
            raise ToolError(f"Could not connect to OPNsense for {path}") from exc

        if response.is_error:
            self._log("GET", path, response.status_code, "error", req_id)
            raise OPNsenseAPIError(
                status_code=response.status_code,
                body=_safe_json(response),
                path=path,
                method="GET",
            )

        self._log("GET", path, response.status_code, "success", req_id)
        result: list[dict[str, Any]] = response.json()
        return result

    async def get_text(self, path: str) -> str:
        req_id = str(uuid.uuid4())
        try:
            response = await self._client.get(f"/api/{path}")
        except httpx.ConnectTimeout as exc:
            self._log("GET", path, None, "timeout", req_id)
            raise ToolError(f"Connect timeout exceeded for {path}") from exc
        except httpx.ReadTimeout as exc:
            self._log("GET", path, None, "timeout", req_id)
            raise ToolError(f"Read timeout exceeded for {path}") from exc
        except httpx.ConnectError as exc:
            self._log("GET", path, None, "error", req_id)
            raise ToolError(f"Could not connect to OPNsense for {path}") from exc

        if response.is_error:
            self._log("GET", path, response.status_code, "error", req_id)
            raise OPNsenseAPIError(
                status_code=response.status_code,
                body=_safe_json(response),
                path=path,
                method="GET",
            )

        self._log("GET", path, response.status_code, "success", req_id)
        return response.text

    async def post(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        req_id = str(uuid.uuid4())
        try:
            response = await self._client.post(f"/api/{path}", json=data)
        except httpx.ConnectTimeout as exc:
            self._log("POST", path, None, "timeout", req_id, token)
            raise ToolError(f"Connect timeout exceeded for {path}") from exc
        except httpx.ReadTimeout as exc:
            self._log("POST", path, None, "timeout", req_id, token)
            raise ToolError(f"Read timeout exceeded for {path}") from exc
        except httpx.ConnectError as exc:
            self._log("POST", path, None, "error", req_id, token)
            raise ToolError(f"Could not connect to OPNsense for {path}") from exc

        if response.is_error:
            self._log("POST", path, response.status_code, "error", req_id, token)
            raise OPNsenseAPIError(
                status_code=response.status_code,
                body=_safe_json(response),
                path=path,
                method="POST",
            )

        self._log("POST", path, response.status_code, "success", req_id, token)
        result: dict[str, Any] = response.json()
        return result


def _safe_json(response: httpx.Response) -> dict[str, Any]:
    try:
        body: dict[str, Any] = response.json()
        return body
    except ValueError:
        return {"raw": response.text}
