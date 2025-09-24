"""Utilities for interacting with the n8n-MCP HTTP server.

The client supports both real HTTP mode and a lightweight simulation mode
(backed by JSON fixtures) so the project can be tested without a running
container.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import requests


class MCPClientError(RuntimeError):
    """Raised when the MCP server returns an error response."""


@dataclass
class MCPResponse:
    method: str
    payload: Dict[str, Any]

    @property
    def result(self) -> Any:
        if "result" not in self.payload:
            raise MCPClientError(f"No result field present in response: {self.payload}")
        return self.payload["result"]


class MCPClient:
    """HTTP/JSON-RPC client for the n8n-MCP server."""

    def __init__(
        self,
        base_url: str,
        auth_token: str,
        *,
        mode: str = "real",
        simulation_fixtures: Optional[Path] = None,
        timeout: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.mode = mode
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        })
        self._simulation_payloads: Dict[str, Any] = {}
        if self.mode == "simulation":
            if not simulation_fixtures or not simulation_fixtures.exists():
                raise ValueError(
                    "Simulation mode requires a valid fixture file via MCP_SIMULATION_FIXTURES"
                )
            with simulation_fixtures.open("r", encoding="utf-8") as handle:
                self._simulation_payloads = json.load(handle)

    @classmethod
    def from_env(cls) -> Optional["MCPClient"]:
        base_url = os.getenv("N8N_MCP_URL")
        token = os.getenv("MCP_AUTH_TOKEN")
        if not base_url or not token:
            return None
        mode = os.getenv("MCP_MODE", "real").lower()
        fixtures = os.getenv("MCP_SIMULATION_FIXTURES")
        fixture_path = Path(fixtures).expanduser() if fixtures else None
        return cls(base_url, token, mode=mode, simulation_fixtures=fixture_path)

    # ------------------------------------------------------------------
    def initialize(self, client_info: Optional[Dict[str, str]] = None) -> MCPResponse:
        params = {"protocolVersion": "1.0", "clientInfo": client_info or {"name": "bmad-mcp", "version": "0.1"}}
        return self._execute("initialize", params)

    def list_tools(self) -> Iterable[Dict[str, Any]]:
        response = self._execute("tools/list")
        return response.result.get("tools", [])

    def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = self._execute(
            "tools/call",
            {
                "name": name,
                "arguments": arguments or {},
            },
        )
        return response.result

    def call_tool_text(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """Convenience helper that unwraps the MCP text content format."""
        result = self.call_tool(name, arguments)
        content = result.get("content", [])
        if not content:
            return ""
        first = content[0]
        if first.get("type") == "text":
            return first.get("text", "")
        return json.dumps(first, indent=2)

    # ----------------------- High-level helpers -----------------------
    def has_tool(self, name: str) -> bool:
        return any(t.get("name") == name for t in self.list_tools())

    def require_tools(self, names: Iterable[str]) -> None:
        available = {t.get("name") for t in self.list_tools()}
        missing = [n for n in names if n not in available]
        if missing:
            raise MCPClientError(f"Missing required MCP tools: {', '.join(missing)}")

    # Management wrappers (if server exposes n8n_* tools)
    def create_workflow(self, name: str, nodes: Optional[list] = None, connections: Optional[dict] = None, settings: Optional[dict] = None) -> Dict[str, Any]:
        args: Dict[str, Any] = {"name": name, "nodes": nodes or [], "connections": connections or {}}
        if settings:
            args["settings"] = settings
        return self.call_tool("n8n_create_workflow", args)

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        return self.call_tool("n8n_get_workflow", {"id": workflow_id})

    def get_workflow_details(self, workflow_id: str) -> Dict[str, Any]:
        return self.call_tool("n8n_get_workflow_details", {"id": workflow_id})

    def update_partial_workflow(self, workflow_id: str, operations: list, validate_only: bool = False) -> Dict[str, Any]:
        return self.call_tool("n8n_update_partial_workflow", {"id": workflow_id, "operations": operations, "validateOnly": validate_only})

    # ------------------------------------------------------------------
    def _execute(self, method: str, params: Optional[Dict[str, Any]] = None) -> MCPResponse:
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params is not None:
            payload["params"] = params

        if self.mode == "simulation":
            key = self._simulation_key(method, params)
            if key not in self._simulation_payloads:
                raise MCPClientError(
                    f"No simulation fixture for method '{method}' with params key '{key}'."
                )
            return MCPResponse(method, self._simulation_payloads[key])

        response = self._session.post(
            f"{self.base_url}/mcp",
            data=json.dumps(payload),
            timeout=self.timeout,
        )
        try:
            data = response.json()
        except ValueError as exc:
            raise MCPClientError(f"Non-JSON response from MCP server: {response.text}") from exc

        if "error" in data:
            raise MCPClientError(str(data["error"]))

        return MCPResponse(method, data)

    @staticmethod
    def _simulation_key(method: str, params: Optional[Dict[str, Any]]) -> str:
        if method != "tools/call":
            return method
        name = params.get("name") if params else ""
        args = params.get("arguments") if params else {}
        args_key = json.dumps(args, sort_keys=True)
        return f"tools/call::{name}::{args_key}"


__all__ = ["MCPClient", "MCPClientError", "MCPResponse"]
