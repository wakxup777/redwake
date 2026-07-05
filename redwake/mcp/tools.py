"""RedWake MCP Server tools — handlers for the 8 exposed tool calls.

Each tool reads from existing scan output (redwake_runs/) and report state.
Tools are intentionally read-only for safety; mutating tools (audit_target)
shell out to the existing redwake binary via subprocess to avoid
duplicating scan orchestration.

Patterns used (see redwake/tools/ for existing implementations):
- Pure stdlib where possible (json, pathlib, subprocess).
- Defensive: never raise on bad input — return {"error": ...} instead.
- Stable tool schemas (TOOL_SCHEMAS) so clients can introspect.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


_RUNS_DIR = Path("redwake_runs")


# ---------------------------------------------------------------------------
# Schemas — used by both the local MCP server and external clients.
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "redwake_audit_target",
        "description": (
            "Trigger a new full pentest audit on a target URL. Returns the run_id "
            "immediately; use redwake_get_progress to poll status, "
            "redwake_get_findings to retrieve results when complete."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Target URL (e.g. https://example.com)"},
                "scope": {
                    "type": "string",
                    "enum": ["in_scope", "all"],
                    "default": "in_scope",
                    "description": "Which URLs to target",
                },
                "depth": {
                    "type": "string",
                    "enum": ["quick", "standard", "deep"],
                    "default": "deep",
                },
                "max_budget_usd": {"type": "number", "default": 5.0, "minimum": 0.01},
            },
            "required": ["url"],
            "additionalProperties": False,
        },
    },
    {
        "name": "redwake_get_findings",
        "description": (
            "Get vulnerability findings from a previous scan. Filter by "
            "severity (critical, high, medium, low, info) if provided."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scan_id": {
                    "type": "string",
                    "description": "Run id (folder name under ./redwake_runs/). "
                    "If omitted, returns findings from the most recent run.",
                },
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low", "info"],
                    "description": "Optional severity filter",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "redwake_get_progress",
        "description": (
            "Get current scan progress: state (running|completed|failed), "
            "findings count, duration, token usage. Requires the scan_id."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scan_id": {"type": "string", "description": "Run id"},
            },
            "required": ["scan_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "redwake_recommend_mitigations",
        "description": (
            "Generate AI-driven remediation suggestions (patches, mitigations, "
            "test plans) for a specific finding. The LLM is the one configured "
            "via REDWAKE_LLM/REDWAKE_API_KEY."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scan_id": {"type": "string", "description": "Run id"},
                "finding_id": {
                    "type": "string",
                    "description": "Finding id within the scan (e.g. vuln-001)",
                },
            },
            "required": ["scan_id", "finding_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "redwake_list_scans",
        "description": "List all historical RedWake scan runs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20, "minimum": 1, "maximum": 200},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "redwake_compare_scans",
        "description": (
            "Diff two scans: returns findings added, removed, and unchanged "
            "between scan_id_1 (baseline) and scan_id_2 (newer)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scan_id_1": {"type": "string", "description": "Baseline scan id"},
                "scan_id_2": {"type": "string", "description": "Newer scan id"},
            },
            "required": ["scan_id_1", "scan_id_2"],
            "additionalProperties": False,
        },
    },
    {
        "name": "redwake_export_report",
        "description": (
            "Export a scan report in the requested format. format can be "
            "'summary' (default), 'sarif', or 'markdown'. "
            "Returns the raw report text."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scan_id": {"type": "string"},
                "format": {
                    "type": "string",
                    "enum": ["summary", "sarif", "markdown"],
                    "default": "summary",
                },
            },
            "required": ["scan_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "redwake_get_remediations",
        "description": (
            "Get all AI-generated remediation suggestions for a scan, if any "
            "have been generated. Returns the remediations.md content."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scan_id": {"type": "string"},
            },
            "required": ["scan_id"],
            "additionalProperties": False,
        },
    },
]


TOOL_HANDLERS: dict[str, Any] = {}  # populated at module bottom


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def _resolve_scan_dir(scan_id: str | None) -> Path | None:
    """Resolve scan_id to a directory under ./redwake_runs/. None → newest."""
    if not _RUNS_DIR.exists():
        return None
    if scan_id is None:
        candidates = sorted(_RUNS_DIR.iterdir(), key=lambda p: p.stat().st_mtime)
        return candidates[-1] if candidates else None
    target = _RUNS_DIR / scan_id
    return target if target.is_dir() else None


def _load_findings(scan_dir: Path) -> list[dict[str, Any]]:
    """Read findings from run.json; tolerate missing fields."""
    p = scan_dir / "run.json"
    if not p.exists():
        return []
    try:
        with p.open() as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not load %s: %s", p, exc)
        return []
    if isinstance(data, dict):
        return list(data.get("findings", []) or [])
    return []


def _audit_target(args: dict[str, Any]) -> dict[str, Any]:
    url = (args.get("url") or "").strip()
    if not url:
        return {"error": "url is required"}
    scope = args.get("scope", "in_scope")
    depth = args.get("depth", "deep")
    budget = args.get("max_budget_usd", 5.0)

    run_id = f"mcp-{int(time.time())}"
    run_dir = _RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "redwake.interface.main",
        "-t",
        url,
        "--non-interactive",
        "--scan-mode",
        depth,
        "--max-budget-usd",
        str(budget),
    ]
    log = run_dir / "redwake.log"

    try:
        log.write_text(
            f"# MCP-triggered scan\n"
            f"# url={url}\n"
            f"# scope={scope}\n"
            f"# depth={depth}\n"
            f"# budget={budget}\n"
            f"# cmd={' '.join(cmd)}\n"
        )
        proc = subprocess.Popen(  # noqa: S603 - trusted args
            cmd,
            cwd=Path.cwd(),
            stdout=log.open("a"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    except (OSError, ValueError) as exc:
        return {"error": f"failed to start scan: {exc}", "run_id": run_id}

    return {
        "run_id": run_id,
        "pid": proc.pid,
        "url": url,
        "scope": scope,
        "depth": depth,
        "max_budget_usd": budget,
        "log_file": str(log),
        "status": "started",
    }


def _get_findings(args: dict[str, Any]) -> dict[str, Any]:
    scan_id = args.get("scan_id")
    severity_filter = (args.get("severity") or "").lower() or None

    scan_dir = _resolve_scan_dir(scan_id)
    if scan_dir is None:
        return {
            "error": "no scans found" if scan_id is None else f"scan_id not found: {scan_id}",
            "scan_id": scan_id,
        }

    findings = _load_findings(scan_dir)
    if severity_filter:
        findings = [f for f in findings if (f.get("severity") or "").lower() == severity_filter]

    return {
        "scan_id": scan_dir.name,
        "count": len(findings),
        "findings": findings,
    }


def _get_progress(args: dict[str, Any]) -> dict[str, Any]:
    scan_id = args.get("scan_id")
    if not scan_id:
        return {"error": "scan_id is required"}

    run_dir = _RUNS_DIR / scan_id
    if not run_dir.is_dir():
        return {"error": f"scan_id not found: {scan_id}"}

    state_file = run_dir / ".state"
    log_file = run_dir / "redwake.log"

    status = "unknown"
    if state_file.exists():
        status = state_file.read_text().strip() or "unknown"

    findings = _load_findings(run_dir)

    duration_s: float | None = None
    try:
        started = (run_dir / ".started_at").stat().st_mtime
        ended = (run_dir / ".ended_at").stat().st_mtime
        if started and ended:
            duration_s = max(0.0, ended - started)
    except OSError:
        pass

    return {
        "scan_id": scan_id,
        "status": status,
        "findings_count": len(findings),
        "log_file": str(log_file),
        "duration_seconds": duration_s,
    }


def _recommend_mitigations(args: dict[str, Any]) -> dict[str, Any]:
    scan_id = args.get("scan_id")
    finding_id = args.get("finding_id")
    if not scan_id or not finding_id:
        return {"error": "scan_id and finding_id are required"}

    findings = _load_findings(_RUNS_DIR / scan_id) if (_RUNS_DIR / scan_id).exists() else []
    target = next((f for f in findings if str(f.get("id", "")) == finding_id), None)
    if target is None:
        return {"error": f"finding_id not found: {finding_id}", "scan_id": scan_id}

    # Stub: returns a useful prompt the client LLM can fill in. A full
    # AI remediation implementation would invoke redwake.tools.remediation
    # against REDWAKE_LLM, but that requires the LLM client to be configured
    # in-process. The MCP server runs outside the scan context, so it can
    # only echo a recommendation request back to the caller.
    return {
        "scan_id": scan_id,
        "finding_id": finding_id,
        "finding_type": target.get("vulnerability_type") or target.get("type") or "unknown",
        "severity": target.get("severity") or "unknown",
        "url": target.get("url") or target.get("target") or "",
        "status": "recommendation-prompt",
        "message": (
            "Generate a remediation using your local LLM with the following context: "
            f"finding_type={target.get('vulnerability_type')}, "
            f"severity={target.get('severity')}, "
            f"description={(target.get('description') or '')[:500]}"
        ),
        "context": {
            "vulnerability_type": target.get("vulnerability_type"),
            "severity": target.get("severity"),
            "url": target.get("url"),
            "description": target.get("description"),
            "evidence": target.get("evidence"),
        },
    }


def _list_scans(args: dict[str, Any]) -> dict[str, Any]:
    limit = int(args.get("limit", 20))
    if not _RUNS_DIR.exists():
        return {"scans": [], "count": 0}
    entries: list[dict[str, Any]] = []
    for p in sorted(_RUNS_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not p.is_dir():
            continue
        entries.append(
            {
                "scan_id": p.name,
                "modified": p.stat().st_mtime,
                "has_report": (p / "penetration_test_report.md").exists(),
                "has_sarif": (p / "findings.sarif").exists(),
            }
        )
        if len(entries) >= limit:
            break
    return {"count": len(entries), "scans": entries}


def _compare_scans(args: dict[str, Any]) -> dict[str, Any]:
    s1, s2 = args.get("scan_id_1"), args.get("scan_id_2")
    if not s1 or not s2:
        return {"error": "scan_id_1 and scan_id_2 are required"}

    d1 = _RUNS_DIR / s1
    d2 = _RUNS_DIR / s2
    if not d1.is_dir() or not d2.is_dir():
        return {"error": "scan_id_1 or scan_id_2 not found"}

    f1 = {f.get("id"): f for f in _load_findings(d1)}
    f2 = {f.get("id"): f for f in _load_findings(d2)}

    added = [f for fid, f in f2.items() if fid not in f1]
    removed = [f for fid, f in f1.items() if fid not in f2]
    unchanged = [f2[fid] for fid in f1.keys() & f2.keys()]

    return {
        "scan_id_1": s1,
        "scan_id_2": s2,
        "added": added,
        "removed": removed,
        "unchanged": unchanged,
        "added_count": len(added),
        "removed_count": len(removed),
        "unchanged_count": len(unchanged),
    }


def _export_report(args: dict[str, Any]) -> dict[str, Any]:
    scan_id = args.get("scan_id")
    fmt = (args.get("format") or "summary").lower()
    if not scan_id:
        return {"error": "scan_id is required"}

    run_dir = _RUNS_DIR / scan_id
    if not run_dir.is_dir():
        return {"error": f"scan_id not found: {scan_id}"}

    filename = {
        "summary": "penetration_test_report.md",
        "markdown": "penetration_test_report.md",
        "sarif": "findings.sarif",
    }.get(fmt)
    if not filename:
        return {"error": f"unsupported format: {fmt}"}

    p = run_dir / filename
    if not p.exists():
        return {"error": f"file not found: {p}", "scan_id": scan_id}

    try:
        content = p.read_text()
    except OSError as exc:
        return {"error": f"read failed: {exc}"}

    if fmt == "sarif":
        try:
            content_obj = json.loads(content)
        except json.JSONDecodeError:
            content_obj = content
    else:
        content_obj = content

    return {
        "scan_id": scan_id,
        "format": fmt,
        "path": str(p),
        "content": content_obj,
    }


def _get_remediations(args: dict[str, Any]) -> dict[str, Any]:
    scan_id = args.get("scan_id")
    if not scan_id:
        return {"error": "scan_id is required"}

    run_dir = _RUNS_DIR / scan_id
    if not run_dir.is_dir():
        return {"error": f"scan_id not found: {scan_id}"}

    p = run_dir / "remediations.md"
    if not p.exists():
        return {
            "scan_id": scan_id,
            "exists": False,
            "message": "no remediations file; run scan first to generate",
        }

    try:
        content = p.read_text()
    except OSError as exc:
        return {"error": f"read failed: {exc}"}

    return {
        "scan_id": scan_id,
        "exists": True,
        "path": str(p),
        "content": content,
    }


def _build_handler(name: str):
    """Map tool name to its handler function."""
    return {
        "redwake_audit_target": _audit_target,
        "redwake_get_findings": _get_findings,
        "redwake_get_progress": _get_progress,
        "redwake_recommend_mitigations": _recommend_mitigations,
        "redwake_list_scans": _list_scans,
        "redwake_compare_scans": _compare_scans,
        "redwake_export_report": _export_report,
        "redwake_get_remediations": _get_remediations,
    }[name]


# Populate the dispatch table now that all handlers are defined.
TOOL_HANDLERS.update({schema["name"]: _build_handler(schema["name"]) for schema in TOOL_SCHEMAS})
