"""Compliance framework mapping for findings.

Static lookup tables that map vulnerability type strings to:

- OWASP Top 10 (2021)
- CWE IDs
- PCI-DSS v4 requirement IDs
- NIST SP 800-53 control IDs

Plus ``enrich_finding()`` that augments a finding dict with a
``compliance`` block ready for SARIF ``properties.compliance``.
"""

from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mapping tables (defensive: vuln_type → IDs). Unknown types map to "".
# ---------------------------------------------------------------------------

OWASP_TOP_10_2021: dict[str, str] = {
    # A01 Broken Access Control
    "IDOR": "A01:2021 - Broken Access Control",
    "Broken Access Control": "A01:2021 - Broken Access Control",
    "Privilege Escalation": "A01:2021 - Broken Access Control",
    "Missing Authorization": "A01:2021 - Broken Access Control",
    # A02 Cryptographic Failures
    "Weak Cryptography": "A02:2021 - Cryptographic Failures",
    "Plaintext Storage": "A02:2021 - Cryptographic Failures",
    "Hardcoded Credentials": "A02:2021 - Cryptographic Failures",
    # A03 Injection
    "SQL Injection": "A03:2021 - Injection",
    "NoSQL Injection": "A03:2021 - Injection",
    "Command Injection": "A03:2021 - Injection",
    "XSS Reflected": "A03:2021 - Injection",
    "XSS Stored": "A03:2021 - Injection",
    "LDAP Injection": "A03:2021 - Injection",
    "XPath Injection": "A03:2021 - Injection",
    "SSTI": "A03:2021 - Injection",
    "Header Injection": "A03:2021 - Injection",
    "Log Injection": "A03:2021 - Injection",
    # A04 Insecure Design
    "Insecure Design": "A04:2021 - Insecure Design",
    "Business Logic Flaw": "A04:2021 - Insecure Design",
    "Race Condition": "A04:2021 - Insecure Design",
    # A05 Security Misconfiguration
    "Security Misconfiguration": "A05:2021 - Security Misconfiguration",
    "Default Credentials": "A05:2021 - Security Misconfiguration",
    "Exposed Admin Interface": "A05:2021 - Security Misconfiguration",
    "Verbose Error Messages": "A05:2021 - Security Misconfiguration",
    # A06 Vulnerable Components
    "Vulnerable Component": "A06:2021 - Vulnerable and Outdated Components",
    "Outdated Dependency": "A06:2021 - Vulnerable and Outdated Components",
    # A07 Auth Failures
    "Weak Credentials": "A07:2021 - Identification and Authentication Failures",
    "Credential Stuffing": "A07:2021 - Identification and Authentication Failures",
    "Missing MFA": "A07:2021 - Identification and Authentication Failures",
    "Session Fixation": "A07:2021 - Identification and Authentication Failures",
    # A08 Software & Data Integrity
    "Insecure Deserialization": "A08:2021 - Software and Data Integrity Failures",
    "Missing Signature Verification": "A08:2021 - Software and Data Integrity Failures",
    # A09 Logging Failures
    "Missing Audit Log": "A09:2021 - Security Logging and Monitoring Failures",
    # A10 SSRF
    "SSRF": "A10:2021 - Server-Side Request Forgery",
}


CWE_MAP: dict[str, str] = {
    "SQL Injection": "CWE-89",
    "NoSQL Injection": "CWE-943",
    "Command Injection": "CWE-78",
    "XSS Reflected": "CWE-79",
    "XSS Stored": "CWE-79",
    "LDAP Injection": "CWE-90",
    "XPath Injection": "CWE-643",
    "SSTI": "CWE-1336",
    "Header Injection": "CWE-93",
    "IDOR": "CWE-639",
    "Broken Access Control": "CWE-284",
    "Privilege Escalation": "CWE-269",
    "Weak Cryptography": "CWE-327",
    "Plaintext Storage": "CWE-312",
    "Hardcoded Credentials": "CWE-798",
    "Weak Credentials": "CWE-521",
    "Credential Stuffing": "CWE-307",
    "Missing Authorization": "CWE-862",
    "Missing MFA": "CWE-308",
    "SSRF": "CWE-918",
    "Insecure Design": "CWE-657",
    "Business Logic Flaw": "CWE-840",
    "Race Condition": "CWE-362",
    "Security Misconfiguration": "CWE-16",
    "Default Credentials": "CWE-1392",
    "Exposed Admin Interface": "CWE-284",
    "Verbose Error Messages": "CWE-209",
    "Vulnerable Component": "CWE-1104",
    "Outdated Dependency": "CWE-937",
    "Session Fixation": "CWE-384",
    "Insecure Deserialization": "CWE-502",
    "Missing Signature Verification": "CWE-347",
    "Missing Audit Log": "CWE-778",
    "Path Traversal": "CWE-22",
    "Open Redirect": "CWE-601",
    "CSRF": "CWE-352",
    "XXE": "CWE-611",
    "Deserialization": "CWE-502",
}


# Inverted: requirement ID -> list of vulnerability types. Used to answer
# the reverse query "which PCI-DSS requirements does this finding touch?"
PCI_DSS_V4: dict[str, list[str]] = {
    "6.2.4": [
        "SQL Injection",
        "NoSQL Injection",
        "Command Injection",
        "XSS Reflected",
        "XSS Stored",
        "LDAP Injection",
        "XPath Injection",
        "SSTI",
        "Header Injection",
        "Path Traversal",
        "XXE",
        "Insecure Deserialization",
        "Deserialization",
    ],
    "6.2.1": ["Broken Access Control", "IDOR", "Missing Authorization"],
    "6.3.1": ["Weak Credentials", "Credential Stuffing", "Hardcoded Credentials"],
    "6.4.1": ["Missing MFA"],
    "6.5.5": ["Insecure Deserialization"],
    "8.2.1": ["Weak Cryptography", "Plaintext Storage"],
    "10.2.1": ["SSRF"],
    "11.3.1": ["Missing Audit Log"],
    "6.5.1": ["Business Logic Flaw"],
    "6.5.10": ["Session Fixation", "CSRF"],
    "6.5.8": ["Default Credentials", "Exposed Admin Interface"],
    "8.3.2": ["Verbose Error Messages"],
}


NIST_800_53: dict[str, list[str]] = {
    "SI-10": [
        "SQL Injection",
        "NoSQL Injection",
        "Command Injection",
        "XSS Reflected",
        "XSS Stored",
        "LDAP Injection",
        "XPath Injection",
        "SSTI",
        "Header Injection",
        "Path Traversal",
        "XXE",
    ],
    "AC-3": ["Broken Access Control", "IDOR", "Missing Authorization"],
    "AC-6": ["Privilege Escalation", "Exposed Admin Interface"],
    "IA-2": ["Weak Credentials", "Credential Stuffing"],
    "IA-5": ["Hardcoded Credentials", "Missing MFA"],
    "SC-8": ["Plaintext Storage"],
    "SC-13": ["Weak Cryptography"],
    "SC-23": ["Session Fixation"],
    "SI-7": ["Vulnerable Component", "Outdated Dependency"],
    "SI-11": ["Missing Audit Log"],
    "AU-2": ["Missing Audit Log"],
    "SI-15": ["Business Logic Flaw", "Race Condition"],
    "SC-39": ["Verbose Error Messages"],
    "SI-4": ["Security Misconfiguration"],
    "SI-10.1": ["Insecure Deserialization"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _vuln_type(finding: dict[str, Any]) -> str:
    """Extract a normalised vulnerability type from a finding dict."""
    return str(
        finding.get("vulnerability_type") or finding.get("type") or finding.get("category") or ""
    )


def _requirements_for(vuln_type: str, table: dict[str, list[str]]) -> list[str]:
    """Inverse lookup: which requirements include this vuln_type?"""
    if not vuln_type:
        return []
    return sorted(req for req, types in table.items() if vuln_type in types)


def enrich_finding(finding: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``finding`` augmented with a ``compliance`` block.

    The block contains:
        - owasp_top_10: human-readable "A03:2021 - Injection" (or "")
        - cwe: "CWE-89" (or "")
        - pci_dss: ["6.2.4", ...]
        - nist_800_53: ["SI-10", ...]

    Returns the original dict untouched (caller decides whether to mutate).
    """
    vuln_type = _vuln_type(finding)

    owasp = OWASP_TOP_10_2021.get(vuln_type, "")
    cwe = CWE_MAP.get(vuln_type, "")
    pci_dss = _requirements_for(vuln_type, PCI_DSS_V4)
    nist = _requirements_for(vuln_type, NIST_800_53)

    compliance = {
        "owasp_top_10": owasp,
        "cwe": cwe,
        "pci_dss": pci_dss,
        "nist_800_53": nist,
    }

    # If we got nothing useful, don't pollute the finding.
    if not any(compliance.values()):
        compliance = {"owasp_top_10": "", "cwe": "", "pci_dss": [], "nist_800_53": []}

    if not owasp:
        logger.debug(
            "Compliance: no OWASP mapping for vuln_type=%r (finding id=%s)",
            vuln_type,
            finding.get("id"),
        )

    return {**finding, "compliance": compliance}
