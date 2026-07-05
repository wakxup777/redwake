"""RedWake MCP server — exposes RedWake tools over Model Context Protocol.

Clients (Claude Code, Cursor, Windsurf, etc.) can call RedWake tools
like ``redwake_audit_target`` to trigger pentest scans or fetch findings
via the JSON-RPC 2.0 endpoint at ``POST /mcp``.

Start the server with ``redwake mcp serve [--port 9877] [--auth-token TOKEN]``.
The auth token can also come from the ``REDWAKE_MCP_TOKEN`` environment variable.
If neither is set the server emits a one-time token on stderr and runs
unauthenticated (only safe for localhost development).
"""

from __future__ import annotations

from .server import main as main
from .server import serve as serve
from .tools import TOOL_HANDLERS, TOOL_SCHEMAS


__all__ = ["TOOL_HANDLERS", "TOOL_SCHEMAS", "main", "serve"]
