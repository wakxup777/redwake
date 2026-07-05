# Changelog

All notable changes to RedWake are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [1.0.4-redwake.3] — 2026-07-04 (Open Source Release)

### Changed
- **Removed license enforcement entirely** — RedWake is now fully open source.
  No keys, no server validation, no machine fingerprinting, no heartbeat telemetry.
- All users get the full feature set without registration.
- Config path migrated from `~/.redwake/` to XDG-compliant `~/.config/redwake/`.

### Removed
- License module (`redwake/license/`): JWT verify, Ed25519 signature, anti-debug,
  heartbeat, machine fingerprint, endpoint discovery.
- Admin server infrastructure (no longer needed).
- License env vars (`REDWAKE_LICENSE_KEY`, `REDWAKE_LICENSE_BYPASS`).
- Runtime hook (`rthooks/rthook_redwake_antire.py`).

---

# Changelog

All notable changes to RedWake are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [1.0.4] — 2026-07-04

Initial public release.

### Added

- Multi-agent AI penetration testing
- License enforcement with Ed25519-signed JWT
- Anti-debug protections (ptrace, /proc/self/maps, LD_PRELOAD, timing)
- Server endpoint obfuscation (XOR-encoded URLs in binary)
- Three-stage endpoint discovery (DNS TXT → HTML scrape → hardcoded fallback)
- 60s background heartbeat with anomaly detection
- Machine fingerprint binding
- Comprehensive skill library (vulnerabilities, frameworks, technologies, protocols)
- Full scan modes (quick / standard / deep)
- Interactive TUI mode
- SARIF 2.1.0 report output
- Markdown penetration test report
- Docker sandbox isolation (NET_ADMIN + Caido proxy)
- Resume workflow for interrupted scans

### Security

- All outbound traffic through Caido interception proxy (captured for analysis)
- Anti-debug detection prevents trivial RE (gdb, strace, ltrace, lldb)
- License keys bound to machine fingerprint (sharing auto-revoked)
- Anomaly detection: >3 IPs/1h or >1 fingerprint/24h → auto-revoke
- 1h JWT cache enables offline operation
- Ed25519 signature verification (256-bit security)

### Performance

- Cold startup: ~500ms (license verify + discovery)
- Warm startup: <100ms (cache hit)
- Heartbeat: 0ms user-perceived (background thread)
- Anti-debug check: <50ms

---

## [Unreleased] — Future

- Publish sandbox image to rebranded ghcr.io/redwake registry
- Add CI/CD workflows for automated releases
- Community skill registry
