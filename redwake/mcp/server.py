"""RedWake MCP Server — exposes RedWake tools over Model Context Protocol.

Implements JSON-RPC 2.0 over HTTP (single endpoint ``POST /mcp``).
Clients (Claude Code, Cursor, Windsurf, etc.) can call RedWake tools
like ``redwake_audit_target`` to trigger pentest scans or fetch findings.

Start with: ``redwake mcp serve [--port 9877] [--auth-token TOKEN]``
"""

from __future__ import annotations

import argparse
import json
import logging
import secrets
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .tools import TOOL_HANDLERS, TOOL_SCHEMAS


logger = logging.getLogger(__name__)

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "redwake", "version": "1.0.0"}


class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler that speaks JSON-RPC 2.0 for MCP."""

    auth_token: str = ""
    log_requests: bool = False

    def log_message(self, fmt: str, *args: Any) -> None:
        if self.log_requests:
            super().log_message(fmt, *args)

    def _auth_ok(self) -> bool:
        if not self.auth_token:
            return True  # auth disabled
        header = self.headers.get("Authorization", "")
        return header == f"Bearer {self.auth_token}"

    def _json_response(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()
        self.wfile.write(payload)

    def _handle_initialize(self, params: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": SERVER_INFO,
            "capabilities": {"tools": {}},
        }

    def _handle_tools_list(self, _params: dict[str, Any] | None) -> dict[str, Any]:
        return {"tools": list(TOOL_SCHEMAS)}

    def _handle_tools_call(self, params: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(params, dict):
            return {"content": [], "isError": True, "error": "params must be an object"}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(name, str) or not name:
            return {"content": [], "isError": True, "error": "missing tool name"}
        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            return {
                "content": [],
                "isError": True,
                "error": f"unknown tool: {name}",
            }
        try:
            result = handler(arguments)
        except Exception as exc:
            logger.exception("MCP tool %s failed", name)
            return {"content": [], "isError": True, "error": str(exc)}
        text = json.dumps(result, default=str, indent=2)
        return {"content": [{"type": "text", "text": text}], "isError": False}

    def do_POST(self) -> None:
        if self.path != "/mcp":
            self._json_response(404, {"error": "not found; POST /mcp"})
            return
        if not self._auth_ok():
            self._json_response(401, {"error": "unauthorized"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b""
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._json_response(400, {"error": "invalid JSON"})
            return

        method = body.get("method")
        req_id = body.get("id")
        params = body.get("params")

        if method == "initialize":
            result = self._handle_initialize(params)
        elif method == "notifications/initialized":
            # Notification: no response needed
            return
        elif method == "tools/list":
            result = self._handle_tools_list(params)
        elif method == "tools/call":
            result = self._handle_tools_call(params)
        else:
            self._json_response(
                400,
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"method not found: {method}"},
                },
            )
            return

        self._json_response(
            200,
            {"jsonrpc": "2.0", "id": req_id, "result": result},
        )

    def do_GET(self) -> None:
        """Health check at ``GET /health``."""
        if self.path == "/health":
            self._json_response(
                200,
                {"status": "ok", "server": SERVER_INFO["name"], "version": SERVER_INFO["version"]},
            )
            return
        self._json_response(404, {"error": "POST /mcp or GET /health"})

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()


def serve(
    host: str = "127.0.0.1",
    port: int = 9877,
    auth_token: str = "",
    log_requests: bool = False,
) -> None:
    """Start the MCP server (blocking call)."""
    if not auth_token:
        generated = secrets.token_urlsafe(24)
        logger.warning(
            "REDWAKE_MCP_TOKEN not set; server running WITHOUT auth. "
            "Anyone on %s can call it. "
            "Generate token: REDWAKE_MCP_TOKEN=%s",
            host,
            generated,
        )

    MCPRequestHandler.auth_token = auth_token
    MCPRequestHandler.log_requests = log_requests

    server = ThreadingHTTPServer((host, port), MCPRequestHandler)
    logger.info("RedWake MCP server listening on http://%s:%d/mcp", host, port)
    logger.info("Health check:                http://%s:%d/health", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("MCP server stopped by SIGINT")
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="redwake mcp serve")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=9877, help="Bind port")
    parser.add_argument(
        "--auth-token",
        default="",
        help="Bearer token (or set REDWAKE_MCP_TOKEN env var)",
    )
    parser.add_argument(
        "--log-requests",
        action="store_true",
        help="Log every HTTP request",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    auth_token = args.auth_token or _env_token()
    serve(
        host=args.host,
        port=args.port,
        auth_token=auth_token,
        log_requests=args.log_requests,
    )
    return 0


def _env_token() -> str:
    import os

    return os.environ.get("REDWAKE_MCP_TOKEN", "")


if __name__ == "__main__":
    sys.exit(main())
