# Security Policy

## Reporting a Vulnerability

RedWake Security Labs takes security vulnerabilities seriously. If you discover a security issue in RedWake:

**Email:** security@redwake.rf.gd
**PGP key:** (request via email)
**Subject line:** `[SECURITY] <short description>`

Please **do not** open a public GitHub issue for security vulnerabilities.

### What to include

1. **Description** of the vulnerability
2. **Steps to reproduce** (be specific)
3. **Affected versions** (e.g., v1.0.4-redwake.1)
4. **Impact** assessment (RCE, license bypass, info disclosure, etc.)
5. **Environment** (OS, Python version, install method)

### Response timeline

- **24 hours:** initial acknowledgement
- **72 hours:** triage and severity classification
- **7 days:** patch development for high/critical
- **30 days:** disclosure (coordinated with reporter)

### Scope

In scope:
- License enforcement bypass
- Anti-debug detection bypass
- Sandbox escape
- Server-side vulnerabilities (only if you have a test key)
- Privilege escalation in client

Out of scope:
- Vulnerabilities in dependencies (report to respective maintainers)
- Social engineering
- Physical attacks
- Denial of service (the license server is for legitimate users only)

### Bounty program

RedWake does not currently offer a monetary bug bounty. However:
- Public credit in CHANGELOG.md (if desired)
- Free license extension (1 year per valid report)
- Direct contact with security team

## Responsible Use

RedWake is a powerful offensive security tool. With great power comes great responsibility.

### ✅ Acceptable use

- Testing applications **you own** (your company, your side project)
- Authorized penetration tests with **written scope** (e.g., bug bounty program, red team engagement)
- Security research on **dedicated lab environments** (DVWA, HackTheBox, VulnHub, your own VMs)
- CTF competitions
- Academic research (with appropriate IRB approval)

### ❌ Prohibited use

- Scanning systems without **explicit written permission**
- Targeting critical infrastructure (healthcare, energy, transportation)
- DDoS / availability attacks
- Extortion (ransomware-style threats)
- Any activity that violates local, national, or international law

### Legal framework

RedWake is provided under Apache 2.0. The license includes:

> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND...

You are **solely responsible** for ensuring your use of RedWake complies with all applicable laws and regulations.

## Threat Model

RedWake protects against:
- Casual reverse engineering of the binary
- License key sharing across multiple machines
- Unauthorized mass deployment
- Simple debugging (gdb, strace)

RedWake does **NOT** protect against:
- Nation-state actors
- Sophisticated reverse engineers (2+ weeks dedicated effort)
- Insider threats (someone with admin access to your VPS)
- Physical access to your machine
- Your machine being rooted

## Cryptography

RedWake uses:
- **Ed25519** for license JWT signatures
- **XOR obfuscation** for endpoint URLs and public keys (not cryptographic — defense in depth)
- **TLS** for all server communication (when behind HTTPS reverse proxy)

## Data handling

What RedWake sends to the license server:
- License key (for verification)
- Heartbeat every 60s: scan_id, action (e.g., "scan_running")

What the license server stores:
- License keys and their metadata (issue date, expiry, revocation status)
- Heartbeat events (last 30 days, then pruned)
- Audit log (last 90 days, then pruned)

What RedWake does **NOT** send:
- Target URLs
- Scan results
- Your files or local data

## Contact

- **General:** hi@redwake.rf.gd
- **Security:** security@redwake.rf.gd
- **License support:** admin ilə birbaşa (key verən şəxs)
- **Website:** https://redwake.rf.gd
