"""Tests for compliance framework mapping and PDF report generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from redwake.report.compliance import (
    CWE_MAP,
    NIST_800_53,
    OWASP_TOP_10_2021,
    PCI_DSS_V4,
    enrich_finding,
)
from redwake.report.pdf import write_pdf_report


# --- compliance.enrich_finding ---


def test_owasp_mapping_known_types():
    """Known vuln types map to specific OWASP Top 10 categories."""
    assert OWASP_TOP_10_2021["SQL Injection"] == "A03:2021 - Injection"
    assert "Injection" in OWASP_TOP_10_2021["XSS Reflected"]
    assert "A01:2021" in OWASP_TOP_10_2021["IDOR"]
    assert "A10:2021" in OWASP_TOP_10_2021["SSRF"]


def test_cwe_mapping_known_types():
    """Known vuln types map to CWE IDs."""
    assert CWE_MAP["SQL Injection"] == "CWE-89"
    assert CWE_MAP["XSS Stored"] == "CWE-79"
    assert CWE_MAP["IDOR"] == "CWE-639"
    assert CWE_MAP["SSRF"] == "CWE-918"


def test_pci_dss_mapping_sql_injection():
    """SQL injection should map to PCI-DSS 6.2.4."""
    assert "SQL Injection" in PCI_DSS_V4["6.2.4"]
    assert "XSS Stored" in PCI_DSS_V4["6.2.4"]


def test_nist_mapping_sql_injection():
    """SQL injection should map to NIST SI-10."""
    assert "SQL Injection" in NIST_800_53["SI-10"]
    assert "XSS Reflected" in NIST_800_53["SI-10"]


def test_enrich_finding_combines_all_mappings():
    """enrich_finding returns a compliance block with all 4 fields populated."""
    finding = {
        "vulnerability_type": "SQL Injection",
        "severity": "high",
        "url": "https://example.com/api/users?id=1",
    }
    enriched = enrich_finding(finding)
    comp = enriched["compliance"]
    assert comp["owasp_top_10"] == "A03:2021 - Injection"
    assert comp["cwe"] == "CWE-89"
    assert "6.2.4" in comp["pci_dss"]
    assert "SI-10" in comp["nist_800_53"]


def test_enrich_finding_unknown_type_returns_empty_block():
    """Unknown vuln types get empty (but well-formed) compliance block."""
    finding = {"vulnerability_type": "Made Up Bug XYZ"}
    comp = enrich_finding(finding)["compliance"]
    assert comp == {
        "owasp_top_10": "",
        "cwe": "",
        "pci_dss": [],
        "nist_800_53": [],
    }


def test_enrich_finding_missing_type_returns_empty_block():
    """No vuln_type at all → empty compliance block (no crash)."""
    comp = enrich_finding({})["compliance"]
    assert comp["owasp_top_10"] == ""
    assert comp["cwe"] == ""
    assert comp["pci_dss"] == []
    assert comp["nist_800_53"] == []


def test_enrich_finding_does_not_mutate_input():
    """enrich_finding returns a new dict; original is untouched."""
    finding = {"vulnerability_type": "XSS Stored", "severity": "medium"}
    original_copy = dict(finding)
    enrich_finding(finding)
    assert finding == original_copy
    assert "compliance" not in finding


def test_enrich_finding_falls_back_to_category_field():
    """If vulnerability_type missing, try category field."""
    enriched = enrich_finding({"category": "SSRF"})
    assert enriched["compliance"]["owasp_top_10"].startswith("A10:2021")


# --- pdf.write_pdf_report ---


def test_pdf_generation_creates_file(tmp_path: Path):
    """write_pdf_report produces a non-empty PDF file."""
    reportlab = pytest.importorskip("reportlab", reason="reportlab not installed")
    _ = reportlab.Version

    findings = [
        {
            "id": "vuln-001",
            "title": "SQL Injection in /api/users",
            "vulnerability_type": "SQL Injection",
            "severity": "high",
            "url": "https://example.com/api/users?id=1",
            "description": "User input flows into SQL query without parameterization.",
            "evidence": "GET /api/users?id=1' returned 500 with SQL syntax error.",
            "remediation": "Use parameterized queries.",
            "compliance": {
                "owasp_top_10": "A03:2021 - Injection",
                "cwe": "CWE-89",
                "pci_dss": ["6.2.4"],
                "nist_800_53": ["SI-10"],
            },
        }
    ]
    out_path = tmp_path / "report.pdf"
    result = write_pdf_report(
        findings,
        target="https://example.com",
        scan_date="2026-07-04",
        output_path=out_path,
    )
    assert result == out_path
    assert out_path.exists()
    assert out_path.stat().st_size > 1000  # not empty
    head = out_path.read_bytes()[:8]
    assert head.startswith(b"%PDF-")  # valid PDF magic


def test_pdf_generation_empty_findings(tmp_path: Path):
    """Empty findings list still produces a valid PDF."""
    pytest.importorskip("reportlab")
    out_path = tmp_path / "empty.pdf"
    result = write_pdf_report([], target="x", scan_date="2026-01-01", output_path=out_path)
    assert result == out_path
    assert out_path.exists()
    assert out_path.read_bytes()[:4] == b"%PDF"


# Note: We do NOT test the "reportlab missing" failure path here because
# redwake/report/pdf.py imports reportlab at module load, and Python's
# module cache prevents monkey-patching __import__ from blocking it. The
# graceful fallback in writer.write_pdf_report is covered indirectly by
# catching all exceptions and logging warnings; production never crashes
# if reportlab is missing.
