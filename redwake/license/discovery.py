"""License server endpoint discovery.

Three-stage fallback chain:
1. Cached endpoint (1h TTL)
2. DNS TXT record at _redwake-lic.<your-domain> (encoded base64)
3. Hardcoded obfuscated fallback list (binary-də literal URL yoxdur)

Returns discovered endpoint URL or raises LicenseServerUnreachableError.
"""
from __future__ import annotations

import base64
import json
import os
import socket
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

from ._obfuscate import decode_fallback_endpoints
from .exceptions import LicenseServerUnreachableError

CACHE_DIR = Path.home() / ".redwake"
CACHE_FILE = CACHE_DIR / ".endpoint"
CACHE_TTL = 3600  # 1 hour

# DNS TXT discovery suffix (admin sets _redwake-lic.<domain> TXT record)
DNS_DISCOVERY_DOMAIN = os.environ.get("REDWAKE_DISCOVERY_DOMAIN", "redwake.rf.gd")
DNS_TXT_NAME = f"_redwake-lic.{DNS_DISCOVERY_DOMAIN}"

# HTML scrape discovery — admin embeds endpoint in homepage <meta> tag
HTML_DISCOVERY_URL = f"https://{DNS_DISCOVERY_DOMAIN}/"

# Network timeout per stage
DISCOVERY_TIMEOUT = 5.0


def _read_cache() -> str | None:
    """Returns cached endpoint if not expired, else None."""
    try:
        if not CACHE_FILE.exists():
            return None
        data = json.loads(CACHE_FILE.read_text())
        if data.get("ts", 0) + CACHE_TTL > time.time():
            return data.get("endpoint")
    except (OSError, json.JSONDecodeError):
        pass
    return None


def _write_cache(endpoint: str) -> None:
    """Persist discovered endpoint to disk."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({"endpoint": endpoint, "ts": time.time()}))
    except OSError:
        pass


def _probe_endpoint(url: str) -> bool:
    """Returns True if endpoint responds with /health 200."""
    try:
        r = httpx.get(f"{url.rstrip('/')}/health", timeout=DISCOVERY_TIMEOUT)
        return r.status_code == 200
    except Exception:
        return False


def _discover_via_dns_txt() -> str | None:
    """Query DNS TXT record, decode base64-encoded endpoint URL."""
    try:
        import dns.resolver  # type: ignore
    except ImportError:
        return None
    try:
        answers = dns.resolver.resolve(DNS_TXT_NAME, "TXT")
        for rdata in answers:
            txt = "".join(s.decode() for s in rdata.strings)
            try:
                decoded = base64.b64decode(txt).decode()
                if decoded.startswith("http"):
                    return decoded.rstrip("/")
            except Exception:
                continue
    except Exception:
        pass
    return None


def _discover_via_html_scrape() -> str | None:
    """Scrape HTML page for hidden <meta name="redwake-lic" content="..."> tag."""
    try:
        r = httpx.get(HTML_DISCOVERY_URL, timeout=DISCOVERY_TIMEOUT, follow_redirects=True)
        # Look for <meta name="redwake-lic" content="<base64>">
        import re

        m = re.search(rb'<meta\s+name=["\']redwake-lic["\']\s+content=["\']([A-Za-z0-9+/=]+)["\']', r.content)
        if m:
            decoded = base64.b64decode(m.group(1)).decode()
            if decoded.startswith("http"):
                return decoded.rstrip("/")
        # Fallback: zero-width steganography (HTML contains zero-width chars forming payload)
        # For simplicity, scan for endpoint-shaped substrings
        m = re.search(rb"https?://[a-zA-Z0-9._\-]+/api/v\d+/lic[^\s\"'<>]+", r.content)
        if m:
            return m.group(0).decode().rstrip("/")
    except Exception:
        pass
    return None


def _discover_via_hardcoded() -> list[str]:
    """Return obfuscated fallback endpoints."""
    return decode_fallback_endpoints()


def discover() -> str:
    """Discover the active license server endpoint.

    Tries (in order):
    1. Cached endpoint (1h TTL)
    2. DNS TXT discovery
    3. HTML scrape discovery
    4. Hardcoded obfuscated fallback list (probes each)

    Returns validated endpoint URL or raises LicenseServerUnreachableError.
    """
    # 1. Cache
    cached = _read_cache()
    if cached and _probe_endpoint(cached):
        return cached

    # 2. DNS TXT
    endpoint = _discover_via_dns_txt()
    if endpoint and _probe_endpoint(endpoint):
        _write_cache(endpoint)
        return endpoint

    # 3. HTML scrape
    endpoint = _discover_via_html_scrape()
    if endpoint and _probe_endpoint(endpoint):
        _write_cache(endpoint)
        return endpoint

    # 4. Hardcoded fallback list (probe each)
    attempts = []
    for fb in _discover_via_hardcoded():
        attempts.append(fb)
        if _probe_endpoint(fb):
            _write_cache(fb)
            return fb

    # Override via env (last resort, for emergency)
    override = os.environ.get("REDWAKE_LICENSE_SERVER", "").strip()
    if override:
        attempts.append(override)
        if _probe_endpoint(override):
            _write_cache(override)
            return override

    raise LicenseServerUnreachableError(attempts=attempts)
