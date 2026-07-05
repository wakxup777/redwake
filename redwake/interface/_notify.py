"""Background webhook notification dispatcher.

Called by main.py after scan completes. Runs in a daemon thread so the
CLI process does not block waiting for the webhook to respond.

Important: We snapshot the report_state data BEFORE spawning the thread,
because report_state is owned by the scan-loop's asyncio context. Accessing
its attributes from a thread that outlives the loop triggers an SDK warning
("scan loop is not ready") even though our reads are read-only.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from redwake.config import load_settings
from redwake.tools.notify.tool import _do_notify


logger = logging.getLogger(__name__)


def _snapshot_report(report_state: Any) -> tuple[str, int, dict[str, int]]:
    """Read all data needed for the webhook from report_state NOW (sync).

    Returns: (scan_id, n_vulns, sev_counts)
    """
    scan_id = str(getattr(report_state, "scan_id", None) or "unknown")
    vulns = getattr(report_state, "vulnerability_reports", None) or []
    n_vulns = len(vulns) if hasattr(vulns, "__len__") else 0

    sev_counts: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for v in vulns:
        sev = (v.get("severity", "") or "").lower() if isinstance(v, dict) else ""
        if sev in sev_counts:
            sev_counts[sev] += 1
        elif sev:
            sev_counts["info"] += 1
    return scan_id, n_vulns, sev_counts


def _build_summary_message(exit_reason: str, snapshot: tuple[str, int, dict[str, int]]) -> str:
    """Build a Markdown summary from a pre-snapshotted (scan_id, n_vulns, sev_counts)."""
    scan_id, n_vulns, sev_counts = snapshot
    lines = [
        f"*Status:* `{exit_reason}`",
        f"*Vulnerabilities:* {n_vulns} total",
    ]
    if any(sev_counts.values()):
        breakdown = ", ".join(
            f"{k}: {v}" for k, v in sev_counts.items() if v
        )
        lines.append(f"*Breakdown:* {breakdown}")
    lines.append(f"*Run ID:* `{scan_id}`")
    return "\n".join(lines)


def _send_webhook_background(url: str, message: str, severity: str) -> None:
    """Thread target: POST webhook without blocking main flow.

    Receives a plain message string — does NOT touch report_state or any
    other loop-owned object — so it cannot trigger SDK lifecycle warnings.
    """
    try:
        result = _do_notify(url, message, severity)
        if result.get("success"):
            logger.info("Webhook notification sent to %s", url)
        else:
            logger.warning("Webhook notification failed: %s", result.get("error"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Webhook notification raised exception: %s", exc)


def _notify_scan_complete(exit_reason: str, report_state: Any) -> None:
    """Background-fire webhook if REDWAKE_WEBHOOK_URL is set.

    Snapshots report_state into a plain tuple BEFORE spawning the thread,
    so the thread only sees safe primitive data.
    """
    settings = load_settings()
    notify = settings.notify
    if not notify.notify_on_scan_end:
        return
    url = notify.webhook_url
    if not url:
        return

    # Snapshot inside the calling (loop) context, before the thread spawns.
    snapshot = _snapshot_report(report_state) if report_state else ("unknown", 0, {})
    sev = "error" if exit_reason == "error" else "info"
    message = _build_summary_message(exit_reason, snapshot)

    thread = threading.Thread(
        target=_send_webhook_background,
        args=(url, message, sev),
        daemon=True,
    )
    thread.start()
