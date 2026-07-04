"""RedWake license enforcement — public API."""
from __future__ import annotations

from .exceptions import (
    DebugDetectedError,
    ExpiredLicenseKeyError,
    FingerprintMismatchError,
    InvalidLicenseKeyError,
    LicenseError,
    LicenseServerUnreachableError,
    NoLicenseKeyError,
    RevokedLicenseKeyError,
)
from .heartbeat import start_heartbeat, stop_heartbeat
from .license import get_license_status, verify_or_exit

__all__ = [
    "verify_or_exit",
    "get_license_status",
    "start_heartbeat",
    "stop_heartbeat",
    "LicenseError",
    "NoLicenseKeyError",
    "InvalidLicenseKeyError",
    "RevokedLicenseKeyError",
    "ExpiredLicenseKeyError",
    "LicenseServerUnreachableError",
    "FingerprintMismatchError",
    "DebugDetectedError",
]
