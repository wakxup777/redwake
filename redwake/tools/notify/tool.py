"""``notify_webhook`` — POST scan-completion summaries to a webhook URL.

Supports Slack, Discord, Teams, and any other endpoint that accepts a JSON
POST with a top-level ``text`` field (Slack incoming-webhook format).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from agents import RunContextWrapper, function_tool

from redwake.config import load_settings


logger = logging.getLogger(__name__)


def _do_notify(url: str, message: str, severity: str = "info") -> dict[str, Any]:
    """Synchronous notification worker."""
    if not url or not url.strip():
        return {"success": False, "error": "URL is required"}

    sev = (severity or "info").lower()
    if sev not in {"info", "warning", "error", "success"}:
        sev = "info"

    settings = load_settings()
    timeout = settings.notify.timeout

    emoji = {
        "info": ":information_source:",
        "success": ":white_check_mark:",
        "warning": ":warning:",
        "error": ":rotating_light:",
    }.get(sev, ":information_source:")

    payload = {
        "text": f"{emoji} *RedWake Pentest — {sev.upper()}*\n{message}",
        "username": "RedWake",
        "icon_emoji": ":shield:",
        # Custom fields for tools that parse them (Slack attachments fallback)
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *RedWake Pentest — {sev.upper()}*\n{message}",
                },
            }
        ],
    }

    try:
        r = httpx.post(url, json=payload, timeout=timeout)
    except (httpx.ConnectError, httpx.RequestError, httpx.TimeoutException) as exc:
        logger.warning("notify_webhook failed for %s: %s", url, exc)
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}

    if r.status_code >= 400:
        logger.warning("notify_webhook %s returned HTTP %d: %s", url, r.status_code, r.text[:200])
        return {
            "success": False,
            "error": f"HTTP {r.status_code}: {r.text[:200]}",
        }

    return {
        "success": True,
        "status_code": r.status_code,
        "url": url,
    }


@function_tool
def notify_webhook(
    ctx: RunContextWrapper,
    url: str,
    message: str,
    severity: str = "info",
) -> str:
    """Post a scan-event notification to a webhook URL.

    Args:
        url: Webhook endpoint (Slack incoming-webhook, Discord webhook, Teams
            incoming-webhook, or any JSON POST endpoint that accepts ``{"text": ...}``).
        message: Plain-text or Markdown body of the notification.
        severity: One of ``info`` (default), ``warning``, ``error``, ``success``.

    Returns:
        JSON string: ``{"success": bool, "error"?: str, "status_code"?: int}``.
    """
    result = _do_notify(url, message, severity)
    return json.dumps(result)
