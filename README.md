# RedWake — Multi-Agent AI Penetration Testing

<p align="center">
  <a href="https://redwake.rf.gd"><img src="https://img.shields.io/badge/Website-redwake.rf.gd-2b9246?style=for-the-badge" alt="Website"></a>
  <a href="https://docs.redwake.rf.gd"><img src="https://img.shields.io/badge/Docs-docs.redwake.rf.gd-3b82f6?style=for-the-badge" alt="Docs"></a>
  <a href="https://redwake.rf.gd/contact"><img src="https://img.shields.io/badge/Contact-redwake.rf.gd%2Fcontact-f0f0f0?style=for-the-badge" alt="Contact"></a>
</p>

**Avtonom AI penetration testing agentləri — real hacker kimi davranır, kodu dinamik olaraq işlədir, zəiflikləri tapır və real proof-of-concept-lərlə təsdiqləyir.**

RedWake, **RedWake Security Labs** tərəfindən hazırlanmış çox-agentli AI penetration testing platformasıdır. Avtonom agentlər real hacker kimi davranır, kodu dinamik olaraq işlədir, zəiflikləri tapır və real proof-of-concept-lərlə təsdiqləyir.

---

## ✨ Xüsusiyyətlər

- **Multi-agent orchestration** — root agent subagent-ləri idarə edir, paralel scan, tapıntıları bir araya gətirir
- **Real exploit validation** — false positive yox, real PoC-lərlə təsdiq
- **OWASP Top 10 + biznes məntiq flaw-ları** — SQLi, XSS, IDOR, SSRF, RCE, auth bypass, race conditions, mass assignment, broken access control və s.
- **Tam recon** — subfinder, httpx, katana, nuclei ilə attack surface mapping
- **Multi-target** — bir neçə URL/repo eyni anda
- **Source-aware (white-box)** — kodla birlikdə scan, semgrep/AST/secrets/supply-chain
- **CI/CD integration** — SARIF output, GitHub Actions, fail-on-findings mode
- **Sandbox isolation** — Docker container, NET_ADMIN + Caido proxy ilə bütün trafik qeydə alınır
- **Token + budget control** — `--max-budget-usd` ilə maliyyə limiti
- **Resume** — `--resume <run-name>` ilə yarımçıq scan-i davam etdirmək

---

## 📋 Tələblər

- **Python 3.12+**
- **Docker** (Docker Desktop və ya Linux daemon)
- **LLM API açarı** — OpenAI-compatible endpoint (OpenAI, Anthropic, local LLM, və ya proxy)
- **uv** — https://github.com/astral-sh/uv (`pip install uv` və ya `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Sandbox image (~3GB, ilk run-da avtomatik çəkilir)

Default: `ghcr.io/redwake/redwake-sandbox:1.0.0`.

---

## 🚀 Quraşdırma

### 1. Repo klonla

```bash
git clone https://github.com/redwake/redwake.git
cd redwake
```

### 2. Asılılıqları qur

```bash
uv sync
```

### 3. Environment variables təyin et

RedWake **9 env var** istifadə edir (hamısı `REDWAKE_*` prefiksi ilə; OpenAI-compatible adlar da alias kimi qəbul edilir):

```bash
# Minimum (OpenAI-compatible endpoint üçün)
export REDWAKE_LLM='gpt-4o'                            # və ya 'provider/model' (custom endpoint üçün)
export REDWAKE_API_KEY='sk-...'
export REDWAKE_BASE_URL='https://api.openai.com/v1'    # və ya öz proxy endpoint

# Opsional
export REDWAKE_IMAGE='ghcr.io/redwake/redwake-sandbox:1.0.0'  # sandbox image override
export REDWAKE_TELEMETRY='false'                              # telemetriya söndür
export REDWAKE_REASONING_EFFORT='high'                        # none|minimal|low|medium|high|xhigh
export REDWAKE_RUNTIME_BACKEND='docker'                       # gələcəkdə podman/k8s
export REDWAKE_MAX_LOCAL_COPY_MB='1024'                       # local target üçün MB limiti
export REDWAKE_DEBUG='0'                                      # debug logging
```

**Yaxşı təcrübə:** `.envrc` və ya shell rc-yə yaz ki, hər scan-də source etmək lazım olmasın.

---

## 🎯 İstifadə

### Əsas scan

```bash
redwake -t https://target.com --non-interactive --scan-mode quick
```

| Rejim | Vaxt | Dərinlik |
|---|---|---|
| `--scan-mode quick` | 5-10 dəq | Recon + high-probability vectors |
| `--scan-mode standard` | 15-30 dəq | Genişləndirilmiş test siyahısı |
| `--scan-mode deep` | 30-90 dəq | Tam attack surface + biznes məntiq |

### Çoxlu target

```bash
redwake -t https://app.com -t https://api.app.com -t ./repo --non-interactive
```

### İnteraktiv TUI (real-time vizual)

```bash
redwake -t https://target.com
# qısa yollar: F1=Help, Esc=Stop, Ctrl+Q=Quit
```

### Fokus verilmiş scan

```bash
redwake -t https://target.com --non-interactive \
    --instruction "Focus on authentication bypass, IDOR, and SSRF. Test with multiple sessions."
```

### Büdcə limiti (CI/CD üçün)

```bash
redwake -t https://target.com --non-interactive --max-budget-usd 2.00
```

### Dayandırılmış scan-i davam etdirmək

```bash
redwake --resume target-com_a4f2
```

### Custom instruction faylı

```bash
redwake -t https://target.com --non-interactive --instruction-file ./redwake-rules.md
```

---

## ⚙️ Konfiqurasiya

### Config fayl (persistent)

Default path: `~/.redwake/cli-config.json`. Format:

```json
{
  "env": {
    "REDWAKE_LLM": "<provider>/<model>",
    "REDWAKE_API_KEY": "sk-...",
    "REDWAKE_BASE_URL": "<your-llm-endpoint>",
    "REDWAKE_IMAGE": "ghcr.io/redwake/redwake-sandbox:1.0.0",
    "REDWAKE_TELEMETRY": "false"
  }
}
```

Və ya `--config /path/to/cli-config.json` ilə alternativ path.

### LLM seçimi

`REDWAKE_LLM` istənilən OpenAI-compatible model adını qəbul edir:

- Bare adlar (`gpt-4o`, `claude-opus-4-8`) OpenAI providerinə route olunur.
- Custom endpoint üçün provider prefix istifadə edin: `provider/model` formatı.
- OpenAI-compatible alternativlər provider prefix istifadə edərək (custom endpoint vasitəsilə) işləyir.

Model seçimi sənin endpoint-in və LLM provider-in üzərindən qurulur — yuxarıdakı nümunələr üçün provider sənə uyğun model adı verəcək.

---

## 🏗️ Arxitektura

```
Root Agent (orchestrator)
   │
   ├── Recon subagents (parallel)
   │     ├── subdomain enum (subfinder)
   │     ├── HTTP probe (httpx)
   │     ├── crawl (katana, hakrawler)
   │     ├── tech detection
   │     └── parameter mining (arjun, paramspider)
   │
   ├── Vulnerability assessment subagents (parallel)
   │     ├── SQLi / NoSQLi / SSTI
   │     ├── XSS / CSRF / open redirect
   │     ├── IDOR / BFLA / auth bypass
   │     ├── SSRF / XXE / path traversal
   │     ├── File upload / RCE
   │     ├── Race conditions
   │     └── Business logic
   │
   └── Exploit + validate subagents
         └── PoC, impact demo, chain exploits
```

**Skill system:** Hər subagent kontekst-uyğun **max 5 skill** yükləyir (`~/.redwake/skills/custom/`-dən). Default skills 11 kateqoriyada gəlir: vulnerabilities, frameworks, technologies, protocols, tooling, cloud, reconnaissance, scan_modes, coordination, custom.

**Sandbox:** Hər scan üçün ayrı Docker container — image `REDWAKE_IMAGE`, NET_ADMIN cap ilə trafik interception (Caido proxy), bütün tool-lar pre-installed (`/usr/bin/sqlmap`, `/usr/bin/nuclei`, `/home/pentester/go/bin/httpx` və s.).

---

## 🔧 Inkişaf

### Dev quraşdırma

```bash
git clone https://github.com/redwake/redwake.git
cd redwake
uv sync                    # bütün dev deps (pytest, mypy, ruff, pyinstaller ...)
uv run pre-commit install  # optional hooks
```

### Build (PyInstaller binary)

```bash
uv run pyinstaller --clean redwake.spec
# Çıxış: dist/redwake (~66MB stripped ELF)
cp dist/redwake ~/.local/bin/redwake
```

### Test

```bash
uv run pytest                          # tam test suite
uv run pytest tests/test_sarif.py      # tək fayl
uv run ruff check redwake              # linting
uv run mypy redwake                    # type-check (strict mode)
```

### Custom skill əlavə et

```bash
mkdir -p ~/.redwake/skills/custom
cat > ~/.redwake/skills/custom/azerbaijan-banking.md << 'EOF'
---
name: azerbaijan-banking
description: IDOR patterns specific to Azeri banking APIs (IBAN/account manipulation, session token reuse)
---

# Azeri Banking IDOR Testing

## Endpoints
- /api/v1/account/{iban}/balance
- /api/v1/transfer

## Techniques
...
EOF
```

Sonra scan zamanı `--instruction "Use azerbaijan-banking skill"` ilə çağır.

---

## 🏷️ Haqqında

RedWake **RedWake Security Labs** məhsuludur. Bütün kod Apache 2.0 lisenziyası altında açıq mənbədir.

---

## 🤝 Töhfə

PR-lar qəbul edilir. Əsasən:
- Yeni skill faylları (`redwake/skills/custom/`)
- Yeni tool support
- Yeni LLM provider integration
- Bug fixes və performance

Yeni skill yazmaq üçün bax: [`redwake/skills/README.md`](redwake/skills/README.md).

---

## 📜 Lisenziya

Apache License 2.0 — bax: [LICENSE](LICENSE).

Müəllif: RedWake Security Labs.
Fork maintainer: **RedWake Security Labs** <hi@redwake.rf.gd>.

---

## ⚖️ Hüquqi xəbərdarlıq

Bu alət **yalnız sizin sahib olduğunuz və ya yazılı icazəniz olan sistemlərə** qarşı istifadə üçündür. İcazəsiz istifadə qanunsuzdur və RedWake Security Labs buna görə məsuliyyət daşımır. Həmişə responsible disclosure prinsiplərinə riayət edin.

> Only test apps you own or have permission to test. You are responsible for using RedWake ethically and legally.
