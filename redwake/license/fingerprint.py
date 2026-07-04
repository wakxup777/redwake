"""Stable machine fingerprint. Same physical machine always produces same hash."""
from __future__ import annotations

import hashlib
import platform
import socket
import uuid


def _read_machine_id() -> str:
    """Linux /etc/machine-id, fallback to empty."""
    for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            with open(path) as f:
                return f.read().strip()
        except OSError:
            continue
    return ""


def _first_mac() -> str:
    """First non-loopback MAC address. Returns empty string if unavailable."""
    try:
        # uuid.getnode() returns MAC as 48-bit int
        mac_int = uuid.getnode()
        if (mac_int >> 40) % 2 == 0:  # Unicast bit set = real MAC
            return ":".join(f"{(mac_int >> i) & 0xFF:02x}" for i in (40, 32, 24, 16, 8, 0))
    except Exception:
        pass
    return ""


def _hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return ""


def fingerprint() -> str:
    """Stable SHA-256 hash identifying the physical machine.

    Combines: CPU model, hostname, MAC address, OS machine-id, platform.
    """
    parts = [
        platform.machine() or "",
        platform.processor() or "",
        _hostname(),
        _first_mac(),
        _read_machine_id(),
        platform.platform(),
    ]
    joined = "|".join(parts).encode()
    return hashlib.sha256(joined).hexdigest()
