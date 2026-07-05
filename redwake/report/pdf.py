"""PDF report generator for RedWake findings.

Uses reportlab to produce an audit-ready PDF alongside the Markdown
report. Output structure:

    1. Cover page (target, scan date, scan ID)
    2. Executive summary (total counts by severity)
    3. Findings table (severity, title, URL, CWE, OWASP)
    4. Per-finding detail section (description, evidence, remediation)

Findings are expected to be already enriched via
``redwake.report.compliance.enrich_finding``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)

# reportlab is an optional dependency. We import at module scope so that
# nested functions (like _render_finding_detail) can see the symbols;
# nested functions cannot read locals of their callers. If reportlab is
# missing, we set REPORTLAB_AVAILABLE=False and write_pdf_report raises
# a clear RuntimeError. The caller (writer.write_pdf_report) catches this
# and logs a warning, so the rest of the report pipeline keeps working.
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except ImportError as _exc:
    logger.warning("reportlab not installed — PDF report generation disabled: %s", _exc)
    REPORTLAB_AVAILABLE = False
    # Provide Any stubs so type-checkers / other tools don't choke.
    colors = None  # type: ignore[assignment]
    letter = None  # type: ignore[assignment]
    ParagraphStyle = None  # type: ignore[assignment]
    getSampleStyleSheet = None  # type: ignore[assignment]
    inch = None  # type: ignore[assignment]
    PageBreak = None  # type: ignore[assignment]
    Paragraph = None  # type: ignore[assignment]
    SimpleDocTemplate = None  # type: ignore[assignment]
    Spacer = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]
    TableStyle = None  # type: ignore[assignment]


def write_pdf_report(
    findings: list[dict[str, Any]],
    target: str,
    scan_date: str,
    output_path: Path,
) -> Path:
    """Render an audit-ready PDF report.

    Returns: ``output_path`` (the same Path passed in).
    Raises: RuntimeError if reportlab is not installed (callers catch).
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError(
            "reportlab not installed — cannot generate PDF. Install with: uv pip install reportlab"
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="RedWake Pentest Report",
    )

    styles = getSampleStyleSheet()
    h1 = styles["Title"]
    h2 = styles["Heading2"]
    h3 = styles["Heading3"]
    body = styles["BodyText"]
    body.wordWrap = "CJK"  # safe wrap for long unbreakable strings

    story: list[Any] = []

    # 1. Cover page
    story.append(Paragraph("RedWake Pentest Report", h1))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Target:</b> {target}", body))
    story.append(Paragraph(f"<b>Scan date:</b> {scan_date}", body))
    if findings:
        scan_id = findings[0].get("scan_id") or "(see scan record)"
        story.append(Paragraph(f"<b>Scan ID:</b> {scan_id}", body))
    story.append(PageBreak())

    # 2. Executive summary
    story.append(Paragraph("Executive Summary", h2))
    story.append(Spacer(1, 8))
    counts = _count_severities(findings)
    summary = (
        f"RedWake identified <b>{len(findings)}</b> potential vulnerabilities. "
        f"Severity breakdown: "
        f"<b>critical:</b> {counts['critical']}, "
        f"<b>high:</b> {counts['high']}, "
        f"<b>medium:</b> {counts['medium']}, "
        f"<b>low:</b> {counts['low']}, "
        f"<b>info:</b> {counts['info']}."
    )
    story.append(Paragraph(summary, body))
    story.append(Spacer(1, 16))

    # 3. Findings table
    if findings:
        story.append(Paragraph("Findings at a Glance", h2))
        story.append(Spacer(1, 8))
        table_data: list[list[Any]] = [
            ["#", "Severity", "Title", "URL", "CWE", "OWASP"],
        ]
        for i, f in enumerate(findings, 1):
            compliance = f.get("compliance") or {}
            title = (f.get("title") or f.get("vulnerability_type") or "")[:50]
            table_data.append(
                [
                    str(i),
                    _severity_label(f.get("severity")),
                    Paragraph(title, body),
                    Paragraph(_short_url(f.get("url")), body),
                    compliance.get("cwe", "") or "",
                    compliance.get("owasp_top_10", "") or "",
                ]
            )
        table = Table(
            table_data,
            colWidths=[
                0.3 * inch,
                0.7 * inch,
                2.3 * inch,
                2.0 * inch,
                0.7 * inch,
                1.7 * inch,
            ],
            repeatRows=1,
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("TOPPADDING", (0, 0), (-1, 0), 6),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ]
            )
        )
        story.append(table)
        story.append(PageBreak())

    # 4. Per-finding detail
    story.append(Paragraph("Detailed Findings", h2))
    story.append(Spacer(1, 8))
    for i, f in enumerate(findings, 1):
        story.extend(_render_finding_detail(f, i, h2, h3, body))
        story.append(PageBreak())

    # Build
    doc.build(story)
    logger.info("PDF report written to %s (%d findings)", output_path, len(findings))
    return output_path


def _render_finding_detail(
    finding: dict[str, Any],
    index: int,
    h2_style: Any,
    h3_style: Any,
    body_style: Any,
) -> list[Any]:
    story: list[Any] = []
    title = finding.get("title") or finding.get("vulnerability_type") or f"Finding {index}"
    severity = _severity_label(finding.get("severity"))
    story.append(
        Paragraph(f"{index}. {title} <font size=10 color='grey'>[{severity}]</font>", h2_style)
    )
    story.append(Spacer(1, 4))

    compliance = finding.get("compliance") or {}
    if compliance.get("owasp_top_10") or compliance.get("cwe"):
        meta_bits = []
        if compliance.get("cwe"):
            meta_bits.append(f"<b>CWE:</b> {compliance['cwe']}")
        if compliance.get("owasp_top_10"):
            meta_bits.append(f"<b>OWASP:</b> {compliance['owasp_top_10']}")
        story.append(Paragraph(" &nbsp;|&nbsp; ".join(meta_bits), body_style))

    if finding.get("url"):
        story.append(Paragraph(f"<b>URL:</b> {finding['url']}", body_style))

    if finding.get("description"):
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>Description</b>", h3_style))
        story.append(Paragraph(str(finding["description"]), body_style))

    if finding.get("evidence"):
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>Evidence</b>", h3_style))
        story.append(Paragraph(str(finding["evidence"]), body_style))

    if finding.get("remediation") or finding.get("recommendation"):
        rem = finding.get("remediation") or finding.get("recommendation")
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>Remediation</b>", h3_style))
        story.append(Paragraph(str(rem), body_style))

    pci = compliance.get("pci_dss") or []
    nist = compliance.get("nist_800_53") or []
    if pci or nist:
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>Compliance</b>", h3_style))
        if pci:
            story.append(Paragraph(f"<b>PCI-DSS v4:</b> {', '.join(pci)}", body_style))
        if nist:
            story.append(Paragraph(f"<b>NIST 800-53:</b> {', '.join(nist)}", body_style))

    return story


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_SEVERITY_COLORS: dict[str, str] = {
    "critical": "#7f1d1d",
    "high": "#b91c1c",
    "medium": "#c2410c",
    "low": "#1d4ed8",
    "info": "#475569",
}


def _severity_label(severity: Any) -> str:
    sev = str(severity or "unknown").lower()
    return sev.upper() if sev in _SEVERITY_COLORS else str(severity or "UNKNOWN")


def _count_severities(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = dict.fromkeys(_SEVERITY_COLORS, 0)
    for f in findings:
        sev = str(f.get("severity") or "").lower()
        if sev in counts:
            counts[sev] += 1
    return counts


def _short_url(url: Any) -> str:
    if not url:
        return ""
    s = str(url)
    return s if len(s) <= 60 else s[:57] + "..."
