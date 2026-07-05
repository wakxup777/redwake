"""Tests for notify webhook summary builder + dispatcher."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest

from redwake.interface import _notify
from redwake.interface._notify import (
    _build_summary_message,
    _notify_scan_complete,
    _send_webhook_background,
)
from redwake.tools.notify.tool import _do_notify


# --- _build_summary_message ---


def test_build_summary_no_findings_returns_valid_markdown():
    snapshot = ("scan-abc", 0, {})
    msg = _build_summary_message("completed", snapshot)
    assert isinstance(msg, str)
    assert "`completed`" in msg
    assert "0 total" in msg
    assert "scan-abc" in msg


def test_build_summary_with_findings_counts_severities():
    sev_counts = {"critical": 1, "high": 1, "low": 2, "info": 1, "medium": 0}
    snapshot = ("scan-xyz", 5, sev_counts)
    msg = _build_summary_message("completed", snapshot)
    assert "5 total" in msg
    assert "high: 1" in msg
    assert "critical: 1" in msg
    assert "low: 2" in msg
    assert "info: 1" in msg


def test_build_summary_handles_empty_snapshot():
    """Defensive: empty snapshot tuple should not crash."""
    msg = _build_summary_message("error", ("unknown", 0, {}))
    assert isinstance(msg, str)
    assert "error" in msg


def test_snapshot_report_extracts_data():
    """_snapshot_report extracts scan_id + sev_counts from report_state."""
    from redwake.interface._notify import _snapshot_report

    state = SimpleNamespace(
        scan_id="scan-xyz",
        vulnerability_reports=[
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "low"},
        ],
    )
    scan_id, n_vulns, sev_counts = _snapshot_report(state)
    assert scan_id == "scan-xyz"
    assert n_vulns == 3
    assert sev_counts["high"] == 2
    assert sev_counts["low"] == 1


# --- _notify_scan_complete ---


@pytest.fixture
def mock_settings(monkeypatch):
    """Patch load_settings to return controllable NotifySettings."""

    def _factory(url, enabled=True, timeout=10):
        return SimpleNamespace(
            notify=SimpleNamespace(
                webhook_url=url,
                notify_on_scan_end=enabled,
                timeout=timeout,
            )
        )

    return _factory


def test_notify_disabled_no_url_does_nothing(mock_settings, monkeypatch, caplog):
    monkeypatch.setattr(_notify, "load_settings", lambda: mock_settings(None))
    with caplog.at_level("INFO"):
        _notify_scan_complete("completed", SimpleNamespace(scan_id="s1", vulnerability_reports=[]))
    # No thread, no log message about webhook
    assert "Webhook" not in caplog.text


def test_notify_disabled_flag_does_nothing(mock_settings, monkeypatch, caplog):
    monkeypatch.setattr(_notify, "load_settings", lambda: mock_settings("https://example.com/hook", enabled=False))
    with caplog.at_level("INFO"):
        _notify_scan_complete("completed", SimpleNamespace(scan_id="s1", vulnerability_reports=[]))
    assert "Webhook" not in caplog.text


def test_notify_fires_thread_when_enabled(monkeypatch):
    sent_payloads = []

    def _mock_post(url, json, timeout):
        req = httpx.Request("POST", url, json=json)
        sent_payloads.append((url, json, timeout))
        return httpx.Response(200, request=req)

    fake_settings = SimpleNamespace(
        notify=SimpleNamespace(
            webhook_url="https://hooks.example.com/x",
            notify_on_scan_end=True,
            timeout=5,
        )
    )
    monkeypatch.setattr(_notify, "load_settings", lambda: fake_settings)
    monkeypatch.setattr("redwake.tools.notify.tool.httpx.post", _mock_post)

    state = SimpleNamespace(
        scan_id="scan-789",
        vulnerability_reports=[{"severity": "high"}],
    )
    _notify_scan_complete("completed", state)
    # Wait for thread (daemon=True, so test must join or sleep)
    import threading
    for t in threading.enumerate():
        if t.name.startswith("Thread-"):
            t.join(timeout=2)

    assert len(sent_payloads) == 1
    url, payload, timeout = sent_payloads[0]
    assert url == "https://hooks.example.com/x"
    assert "text" in payload
    assert "scan-789" in payload["text"]


# --- _do_notify ---


def test_do_notify_posts_json_with_text_field(monkeypatch):
    captured = []

    def _mock_post(url, json, timeout):
        captured.append({"url": url, "json": json, "timeout": timeout})
        req = httpx.Request("POST", url)
        return httpx.Response(200, request=req)

    monkeypatch.setattr("redwake.tools.notify.tool.httpx.post", _mock_post)

    # Set short timeout via settings
    fake = SimpleNamespace(notify=SimpleNamespace(timeout=5))
    monkeypatch.setattr("redwake.tools.notify.tool.load_settings", lambda: fake)

    result = _do_notify("https://x.example/h", "Test message", "info")
    assert result["success"] is True
    assert result["status_code"] == 200
    assert len(captured) == 1
    payload = captured[0]["json"]
    assert "text" in payload
    assert "Test message" in payload["text"]
    assert ":information_source:" in payload["text"]


def test_do_notify_handles_connection_error(monkeypatch):
    def _mock_post(url, json, timeout):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr("redwake.tools.notify.tool.httpx.post", _mock_post)
    fake = SimpleNamespace(notify=SimpleNamespace(timeout=5))
    monkeypatch.setattr("redwake.tools.notify.tool.load_settings", lambda: fake)

    result = _do_notify("https://x.example/h", "Test", "info")
    assert result["success"] is False
    assert "ConnectError" in result["error"] or "refused" in result["error"]


def test_do_notify_normalizes_severity(monkeypatch):
    captured = []

    def _mock_post(url, json, timeout):
        captured.append(json)
        req = httpx.Request("POST", url)
        return httpx.Response(200, request=req)

    monkeypatch.setattr("redwake.tools.notify.tool.httpx.post", _mock_post)
    fake = SimpleNamespace(notify=SimpleNamespace(timeout=5))
    monkeypatch.setattr("redwake.tools.notify.tool.load_settings", lambda: fake)

    # Invalid severity → falls back to "info"
    _do_notify("https://x.example/h", "M", "garbage")
    assert "INFO" in captured[0]["text"]
