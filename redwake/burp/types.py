"""Burp Suite Pro MCP — data types."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BurpStatus:
    """Result of probing Burp MCP server on localhost."""

    connected: bool
    url: str
    version: str = ""
    error: str = ""
    tools: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        if not self.connected:
            return f"Burp Pro: ❌ not reachable on {self.url.replace('http://', '')}"
        v = f" v{self.version}" if self.version else ""
        return f"Burp Pro: ✅ connected{v} ({len(self.tools)} tools)"


@dataclass
class SiteMapEntry:
    """Single entry from Burp's site map."""

    url: str
    method: str = "GET"
    status: int = 0
    length: int = 0
    mime_type: str = ""
    comment: str = ""

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "method": self.method,
            "status": self.status,
            "length": self.length,
            "mime_type": self.mime_type,
            "comment": self.comment,
        }


@dataclass
class ScanIssue:
    """Single finding from Burp's passive/active scanner."""

    url: str
    name: str
    severity: str = ""  # High / Medium / Low / Information
    confidence: str = ""  # Certain / Firm / Tentative
    issue_type: str = ""
    background: str = ""

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "name": self.name,
            "severity": self.severity,
            "confidence": self.confidence,
            "issue_type": self.issue_type,
            "background": self.background,
        }
