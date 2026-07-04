"""License-related exception types."""
from __future__ import annotations


class LicenseError(Exception):
    """Base class for all license errors."""


class NoLicenseKeyError(LicenseError):
    """REDWAKE_LICENSE_KEY env var not set."""

    def __init__(self) -> None:
        super().__init__(
            "REDWAKE_LICENSE_KEY not set. Contact your administrator to obtain a license key, "
            "then run: export REDWAKE_LICENSE_KEY='REDWAKE-LIC-...'"
        )


class InvalidLicenseKeyError(LicenseError):
    """License key format invalid or signature mismatch."""


class RevokedLicenseKeyError(LicenseError):
    """License key was revoked by administrator."""

    def __init__(self, reason: str = "") -> None:
        msg = "License key has been revoked."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(msg)


class ExpiredLicenseKeyError(LicenseError):
    """License key expired."""


class LicenseServerUnreachableError(LicenseError):
    """Cannot reach any license server endpoint."""

    def __init__(self, attempts: list[str] | None = None) -> None:
        msg = "License server unreachable. Verify network access and try again."
        if attempts:
            msg += f" Attempted: {attempts}"
        super().__init__(msg)


class FingerprintMismatchError(LicenseError):
    """License key is bound to a different machine."""


class DebugDetectedError(LicenseError):
    """Debugger or analysis tool detected."""
