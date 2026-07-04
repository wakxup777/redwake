"""Core license verification + 24h JWT cache."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import httpx

from ._crypto import verify_jwt
from .discovery import discover
from .exceptions import (
    ExpiredLicenseKeyError,
    FingerprintMismatchError,
    InvalidLicenseKeyError,
    LicenseServerUnreachableError,
    NoLicenseKeyError,
    RevokedLicenseKeyError,
)
from .fingerprint import fingerprint as compute_fingerprint

CACHE_DIR = Path.home() / ".redwake"
CACHE_FILE = CACHE_DIR / ".license_cache"
CACHE_TTL = 3600  # 1 hour (server issues 24h JWT, but we refresh hourly to detect revocations)


def _read_cache() -> dict | None:
    try:
        if not CACHE_FILE.exists():
            return None
        data = json.loads(CACHE_FILE.read_text())
        # Cache valid if: not expired AND same key AND same fingerprint
        fp = compute_fingerprint()
        if (
            data.get("ts", 0) + CACHE_TTL > time.time()
            and data.get("key") == os.environ.get("REDWAKE_LICENSE_KEY")
            and data.get("fingerprint") == fp
        ):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return None


def _write_cache(key: str, fp: str, token: str, expires_at: str) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(
            json.dumps(
                {
                    "key": key,
                    "fingerprint": fp,
                    "token": token,
                    "expires_at": expires_at,
                    "ts": time.time(),
                }
            )
        )
    except OSError:
        pass


def _verify_with_server(key: str, fp: str) -> dict:
    """Contact license server, get fresh JWT. Raises on any error."""
    endpoint = discover()  # raises LicenseServerUnreachableError if all fail
    try:
        r = httpx.post(
            f"{endpoint}/api/v1/license/verify",
            json={"key": key, "fingerprint": fp},
            timeout=10.0,
        )
    except httpx.RequestError as e:
        raise LicenseServerUnreachableError([f"{endpoint}: {e!r}"]) from e

    if r.status_code == 404:
        raise InvalidLicenseKeyError("License key not recognized by server.")
    if r.status_code == 403:
        detail = r.json().get("detail", "")
        if "revoked" in detail.lower():
            raise RevokedLicenseKeyError(reason=detail)
        if "expired" in detail.lower():
            raise ExpiredLicenseKeyError(detail)
        if "fingerprint" in detail.lower():
            raise FingerprintMismatchError(
                "This license key is bound to a different machine. "
                "Contact your administrator to reset the binding."
            )
        raise InvalidLicenseKeyError(detail)
    if r.status_code != 200:
        raise InvalidLicenseKeyError(f"Server returned {r.status_code}: {r.text[:200]}")

    return r.json()


def verify_or_exit() -> dict:
    """Verify current license. Returns JWT claims dict on success.

    Order of checks:
    1. REDWAKE_LICENSE_KEY env var present
    2. Cache hit (warm path, no network)
    3. JWT signature verification (local, no network)
    4. Server verify (cold path, ~500ms)
    """
    key = os.environ.get("REDWAKE_LICENSE_KEY", "").strip()
    if not key:
        raise NoLicenseKeyError()

    fp = compute_fingerprint()

    # Try cache first (warm path)
    cached = _read_cache()
    if cached:
        try:
            claims = verify_jwt(cached["token"])
            return claims
        except Exception:
            pass  # cached token invalid, fall through to server verify

    # Cold path: server verify
    result = _verify_with_server(key, fp)
    _write_cache(key, fp, result["token"], result["expires_at"])

    try:
        claims = verify_jwt(result["token"])
    except Exception as e:
        raise InvalidLicenseKeyError(f"JWT verification failed: {e!r}") from e

    return claims


def get_license_status() -> dict:
    """Returns current license state without performing verification."""
    key = os.environ.get("REDWAKE_LICENSE_KEY", "").strip()
    if not key:
        return {"has_key": False}
    cached = _read_cache()
    return {
        "has_key": True,
        "key_prefix": key[:18] + "...",
        "cached": bool(cached),
        "cache_expires_at": cached.get("expires_at") if cached else None,
        "fingerprint_bound": cached.get("fingerprint") == compute_fingerprint() if cached else False,
    }
