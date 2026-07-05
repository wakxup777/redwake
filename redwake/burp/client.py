"""Burp Suite Pro MCP JSON-RPC client.

Implements the subset of MCP (Model Context Protocol) needed for RedWake:
- initialize / initialized handshake
- tools/list discovery
- tools/call invocation

Burp Suite Pro 2025+ exposes an MCP server (default: http://127.0.0.1:9876)
that talks JSON-RPC 2.0 over HTTP POST. No auth by default (localhost trust).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

from .types import BurpStatus, ScanIssue, SiteMapEntry


logger = logging.getLogger(__name__)

MCP_PROTOCOL_VERSION = "2024-11-05"
_REQUEST_TIMEOUT = 5.0
_DEFAULT_URL = "http://127.0.0.1:9876"
_STATUS_CACHE_TTL = 60.0  # seconds


class BurpClient:
    """Minimal async JSON-RPC client for Burp Suite Pro MCP server."""

    def __init__(self, url: str = _DEFAULT_URL, timeout: float = _REQUEST_TIMEOUT) -> None:
        self._url = url.rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._initialized = False
        self._available_tools: list[str] = []
        self._version = ""
        self._lock = asyncio.Lock()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def _rpc(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send JSON-RPC 2.0 request, return result."""
        client = await self._get_client()
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
        }
        if params is not None:
            body["params"] = params

        try:
            r = await client.post(self._url, json=body)
        except (TimeoutError, httpx.ConnectError, httpx.RequestError) as exc:
            raise ConnectionError(f"{type(exc).__name__}: {exc}") from exc

        if r.status_code != 200:
            raise ConnectionError(f"HTTP {r.status_code}: {r.text[:200]}")

        data = r.json()
        if "error" in data:
            err = data["error"]
            raise RuntimeError(err.get("message", json.dumps(err)))
        return data.get("result", {})

    async def initialize(self) -> BurpStatus:
        """Probe Burp MCP server: handshake + tools/list.

        Caches the result for 60s to avoid spamming localhost.
        Returns BurpStatus (connected=True/False with details).
        """
        async with self._lock:
            try:
                result = await self._rpc(
                    "initialize",
                    {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "redwake", "version": "1.0.0"},
                    },
                )
                self._version = (result.get("serverInfo") or {}).get("version", "")
                self._initialized = True

                # Notify server we're ready (notification, no response)
                try:
                    client = await self._get_client()
                    await client.post(
                        self._url,
                        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                    )
                except Exception:
                    pass  # notification, OK to fail

                tools_resp = await self._rpc("tools/list", {})
                self._available_tools = [t.get("name", "") for t in tools_resp.get("tools", [])]

                return BurpStatus(
                    connected=True,
                    url=self._url,
                    version=self._version,
                    tools=self._available_tools,
                )
            except Exception as exc:
                return BurpStatus(
                    connected=False,
                    url=self._url,
                    error=str(exc),
                )

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Invoke a Burp MCP tool by name, return parsed result."""
        if not self._initialized:
            await self.initialize()
        return await self._rpc("tools/call", {"name": tool_name, "arguments": arguments or {}})

    async def get_site_map(self, scope: str = "in_scope") -> list[SiteMapEntry]:
        """Convenience: fetch Burp site map (uses burp_get_site_map if exposed)."""
        try:
            res = await self.call_tool("burp_get_site_map", {"scope": scope})
            return _parse_site_map(res)
        except Exception as exc:
            logger.warning("burp_get_site_map failed: %s", exc)
            return []

    async def get_scan_issues(self, severity: str = "") -> list[ScanIssue]:
        """Convenience: fetch Burp scan issues."""
        try:
            args = {"severity": severity} if severity else {}
            res = await self.call_tool("burp_get_scan_issues", args)
            return _parse_scan_issues(res)
        except Exception as exc:
            logger.warning("burp_get_scan_issues failed: %s", exc)
            return []

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()


# ---- Module-level singleton ----

_client: BurpClient | None = None
_client_url: str = ""
_status_cache: BurpStatus | None = None
_status_cache_at: float = 0.0


async def get_status(url: str = _DEFAULT_URL) -> BurpStatus:
    """Cached status probe (refreshes every 60s)."""
    global _client, _client_url, _status_cache, _status_cache_at

    now = asyncio.get_event_loop().time()
    if _client is None or _client_url != url:
        if _client is not None:
            await _client.close()
        _client = BurpClient(url=url)
        _client_url = url
        _status_cache = None

    if _status_cache is not None and (now - _status_cache_at) < _STATUS_CACHE_TTL:
        return _status_cache

    status = await _client.initialize()
    _status_cache = status
    _status_cache_at = now
    return status


async def call_tool(tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
    """Module-level convenience: call Burp tool (auto-initializes)."""
    global _client
    if _client is None:
        await get_status()
    if _client is None:  # Burp down
        return None
    return await _client.call_tool(tool_name, arguments)


async def get_site_map(scope: str = "in_scope") -> list[SiteMapEntry]:
    """Module-level convenience."""
    global _client
    if _client is None:
        await get_status()
    if _client is None:
        return []
    return await _client.get_site_map(scope)


async def get_scan_issues(severity: str = "") -> list[ScanIssue]:
    """Module-level convenience."""
    global _client
    if _client is None:
        await get_status()
    if _client is None:
        return []
    return await _client.get_scan_issues(severity)


def reset_cache() -> None:
    """Reset module-level singleton (for tests)."""
    global _client, _status_cache, _status_cache_at
    _client = None
    _status_cache = None
    _status_cache_at = 0.0


# ---- Helpers ----


def _parse_site_map(res: Any) -> list[SiteMapEntry]:
    """Normalize Burp's MCP response into SiteMapEntry list."""
    items = res if isinstance(res, list) else res.get("items") or res.get("sitemap") or []
    out: list[SiteMapEntry] = []
    for it in items:
        if isinstance(it, dict):
            out.append(
                SiteMapEntry(
                    url=it.get("url") or it.get("href") or "",
                    method=it.get("method", "GET"),
                    status=it.get("status_code") or it.get("status") or 0,
                    length=it.get("length") or it.get("response_length") or 0,
                    mime_type=it.get("mime_type") or it.get("mimeType") or "",
                    comment=it.get("comment") or "",
                )
            )
        elif isinstance(it, str):
            out.append(SiteMapEntry(url=it))
    return out


def _parse_scan_issues(res: Any) -> list[ScanIssue]:
    """Normalize Burp scan issues response."""
    items = res if isinstance(res, list) else res.get("issues") or res.get("items") or []
    out: list[ScanIssue] = []
    for it in items:
        if isinstance(it, dict):
            out.append(
                ScanIssue(
                    url=it.get("url") or it.get("host") or "",
                    name=it.get("name") or it.get("title") or "",
                    severity=it.get("severity", ""),
                    confidence=it.get("confidence", ""),
                    issue_type=it.get("type") or it.get("issue_type") or "",
                    background=it.get("background") or it.get("description") or "",
                )
            )
    return out
