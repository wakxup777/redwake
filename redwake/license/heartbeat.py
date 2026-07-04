"""Background heartbeat to license server.

Runs in daemon thread, sends periodic events while scan is active. Allows server
to detect license abuse (sharing, IP rotation, scan-target anomalies).
"""
from __future__ import annotations

import os
import threading
import time
from typing import Optional

import httpx

from .discovery import discover
from .fingerprint import fingerprint as compute_fingerprint
from .exceptions import LicenseServerUnreachableError, RevokedLicenseKeyError


class _Heartbeat:
    """Background thread state holder."""

    def __init__(self, scan_id: str, interval: float = 60.0):
        self.scan_id = scan_id
        self.interval = interval
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._last_error: Optional[str] = None
        self._revoked = threading.Event()

    def _loop(self) -> None:
        """Send heartbeat every interval. Stop on revoke or stop signal."""
        key = os.environ.get("REDWAKE_LICENSE_KEY", "").strip()
        if not key:
            return
        fp = compute_fingerprint()

        # First heartbeat immediately
        self._send(key, fp)

        while not self._stop.wait(self.interval):
            self._send(key, fp)

    def _send(self, key: str, fp: str) -> None:
        try:
            endpoint = discover()
        except LicenseServerUnreachableError:
            return  # best-effort; don't crash scan on transient network

        try:
            r = httpx.post(
                f"{endpoint}/api/v1/license/heartbeat",
                json={"key": key, "fingerprint": fp, "scan_id": self.scan_id, "action": "scan_running"},
                timeout=5.0,
            )
            if r.status_code == 403:
                # Auto-revoked by server (anomaly detection)
                self._revoked.set()
                self._last_error = r.json().get("detail", "auto-revoked")
                os._exit(143)  # SIGTERM-ish — silent exit
        except Exception as e:
            self._last_error = repr(e)

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    @property
    def revoked(self) -> bool:
        return self._revoked.is_set()


_active: Optional[_Heartbeat] = None


def start_heartbeat(scan_id: str, interval: float = 60.0) -> _Heartbeat:
    """Start global heartbeat thread. Call once per scan."""
    global _active
    if _active is not None:
        _active.stop()
    _active = _Heartbeat(scan_id, interval=interval)
    _active.start()
    return _active


def stop_heartbeat() -> None:
    """Stop the active heartbeat thread."""
    global _active
    if _active is not None:
        _active.stop()
        _active = None
