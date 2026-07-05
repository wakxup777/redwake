"""Burp Suite Pro MCP integration for RedWake.

Auto-discovers Burp Suite Pro's MCP server on localhost (default 127.0.0.1:9876),
exposes its tools to RedWake agents, and shows status in the TUI right panel.
"""

from __future__ import annotations

from .client import (
    BurpClient,
    call_tool,
    get_scan_issues,
    get_site_map,
    get_status,
    reset_cache,
)
from .types import BurpStatus, ScanIssue, SiteMapEntry


__all__ = [
    "BurpClient",
    "BurpStatus",
    "ScanIssue",
    "SiteMapEntry",
    "call_tool",
    "get_scan_issues",
    "get_site_map",
    "get_status",
    "reset_cache",
]
