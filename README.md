# RedWake — Multi-Agent AI Penetration Testing

<p align="center">
  <a href="https://redwake.rf.gd"><img src="https://img.shields.io/badge/Website-redwake.rf.gd-2b9246?style=for-the-badge" alt="Website"></a>
  <a href="https://docs.redwake.rf.gd"><img src="https://img.shields.io/badge/Docs-docs.redwake.rf.gd-3b82f6?style=for-the-badge" alt="Docs"></a>
  <a href="https://redwake.rf.gd/contact"><img src="https://img.shields.io/badge/Contact-redwake.rf.gd%2Fcontact-f0f0f0?style=for-the-badge" alt="Contact"></a>
</p>

**Avtonom AI penetration testing agentləri — real hacker kimi davranır, kodu dinamik olaraq işlədir, zəiflikləri tapır və real proof-of-concept-lərlər təsdiqləyir.**

RedWake, **RedWake Security Labs** tərəfindən hazırlanmış açıq mənbəli çox-agentli AI penetration testing platformasıdır. **Pulsuz, açıq, lisenziyasız.**

---

## 🚀 Sürətli başlanğıcı (5 dəq)

**1. Repo klonla:**
```bash
git clone https://github.com/wakxup777/redwake.git
cd redwake
```

**2. Avtomatik quraşdırma:**
```bash
./install.sh
```
Bu skript Docker + `uv` qurur, binary build edir, sandbox image-i çəkir.

**3. LLM endpoint tənzimləmələri:**
```bash
export REDWAKE_LLM='gpt-4o'
export REDWAKE_API_KEY='sk-...'
export REDWAKE_BASE_URL='https://api.openai.com/v1'
```

**4. İlk scan:**
```bash
redwake -t http://testphp.vulnweb.com --non-interactive --scan-mode quick
```

**Heç bir key, login, registration yoxdur. Açıq mənbəli.**

---

## 📋 Tələblər

| Nə | Minimum | Yoxlama |
|---|---|---|
| Docker | 20.10+ | `docker --version` |
| Python | 3.12+ | `python3 --version` |
| Git | 2.30+ | `git --version` |
| OS | Linux/macOS/WSL2 | `uname -a` |
| LLM API açarı | OpenAI-compatible | — |

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

**Skill system:** Hər subagent kontekst-uyğun **max 5 skill** yükləyir (`~/.config/redwake/skills/custom/`-dən).

**Sandbox:** Hər scan üçün ayrı Docker container — image `REDWAKE_IMAGE`, NET_ADMIN cap ilə trafik interception (Caido proxy), bütün tool-lar pre-installed.

---

## 🎯 İstifadə nümunələri

### 1. Sadə scan (5 dəq)
```bash
redwake -t https://target.com --non-interactive --scan-mode quick
```

### 2. Tam recon
```bash
redwake -t https://target.com --non-interactive --scan-mode quick --max-budget-usd 0.50
```

### 3. Dərin pentest
```bash
redwake -t https://target.com --non-interactive --scan-mode deep \
    --instruction "Focus on authentication bypass and IDOR" \
    --max-budget-usd 5.00
```

### 4. Çoxlu target paralel
```bash
redwake -t https://app.com -t https://api.app.com -t ./repo --non-interactive
```

### 5. İnteraktiv TUI (real-time vizual)
```bash
redwake -t https://target.com
# Qısa yollar: F1=Help, Esc=Stop, Ctrl+Q=Quit, Enter=Send message
```

### 6. Fokus verilmiş scan
```bash
redwake -t https://target.com --non-interactive \
    --instruction "Test only IDOR and SSRF on /api/* endpoints"
```

### 7. Büdcə limiti (CI/CD üçün)
```bash
redwake -t https://target.com --non-interactive --max-budget-usd 2.00
```

### 8. Dayandırılmış scan-i davam etdirmək
```bash
redwake --resume target-com_a4f2
```

---

## ⚙️ Environment variables

```bash
# ====== LLM (mütləq) ======
export REDWAKE_LLM='gpt-4o'                            # və ya 'provider/model'
export REDWAKE_API_KEY='sk-...'
export REDWAKE_BASE_URL='https://api.openai.com/v1'    # və ya custom endpoint

# ====== Sandbox ======
export REDWAKE_IMAGE='docker.io/wakxup777/redwake-sandbox:1.0.0'  # default
export REDWAKE_RUNTIME_BACKEND='docker'
export REDWAKE_MAX_LOCAL_COPY_MB='1024'

# ====== Davranış ======
export REDWAKE_TELEMETRY='false'
export REDWAKE_REASONING_EFFORT='high'
export REDWAKE_DEBUG='0'
```

**Config fayl ilə** (`~/.config/redwake/cli-config.json`):
```json
{
  "env": {
    "REDWAKE_LLM": "gpt-4o",
    "REDWAKE_API_KEY": "sk-...",
    "REDWAKE_BASE_URL": "https://api.openai.com/v1",
    "REDWAKE_IMAGE": "docker.io/wakxup777/redwake-sandbox:1.0.0",
    "REDWAKE_TELEMETRY": "false"
  }
}
```

---

## 🔍 Scan rejimləri

| Rejim | Vaxt | Nə edir |
|---|---|---|
| `--scan-mode quick` | 5-10 dəq | Recon + high-probability vectors |
| `--scan-mode standard` | 15-30 dəq | Genişləndirilmiş test siyahısı |
| `--scan-mode deep` | 30-90 dəq | Tam attack surface + biznes məntiq |

---

## 📂 Output

```
redwake_runs/target-com_a4f2/
├── penetration_test_report.md    # oxu
├── findings.sarif                # CI/CD üçün
├── redwake.log                   # debug
└── run.json                      # machine-readable
```

---

## 🛠️ CLI reference

```bash
redwake [FLAGS]

Mütləq (biri):
  -t, --target URL          # URL, repo, IP, domain, lokal path
      --mount PATH          # bind-mount lokal qovluq
      --resume NAME         # dayandırılmış scan-i davam et

Əlavə:
  --instruction "..."          # fokus (inline)
  --instruction-file FILE     # fokus (fayldan)
  -n, --non-interactive       # TUI olmadan
  -m, --scan-mode MODE        # quick|standard|deep
      --scope-mode MODE      # auto|diff|full
      --diff-base REF        # diff-scope base branch
      --config FILE          # alternativ config
      --max-budget-usd N     # LLM cost limit
```

---

## 🐳 Sandbox image

Default: `docker.io/wakxup777/redwake-sandbox:1.0.0` (Docker Hub-dan, public).

Pre-installed: sqlmap, nuclei, httpx, katana, caido-cli, python3 və s.

**Manual pull:**
```bash
docker pull docker.io/wakxup777/redwake-sandbox:1.0.0
```

---

## 🔧 Troubleshooting

### "Failed to pull docker image" / "403 Forbidden"
```bash
docker pull docker.io/wakxup777/redwake-sandbox:1.0.0
# Override
export REDWAKE_IMAGE='ghcr.io/redwake/redwake-sandbox:1.0.0'
```

### "Docker not running"
```bash
sudo systemctl start docker
sudo usermod -aG docker $USER  # logout/login lazım
```

### "Tool 'sqlmap' not found in /tmp/"
```bash
redwake -t https://target.com --non-interactive \
    --instruction "Tools are PRE-INSTALLED at:
- /usr/bin/sqlmap
- /usr/bin/nuclei
- /home/pentester/go/bin/httpx
Never install tools to /tmp."
```

### Debug mode
```bash
export REDWAKE_DEBUG=1
redwake -t https://target.com --non-interactive
```

Tam reset:
```bash
rm -rf ~/.config/redwake redwake_runs/
docker system prune -f
```

---

## 🔧 İnkişaf

### Build binary
```bash
uv run pyinstaller --clean redwake.spec
cp dist/redwake ~/.local/bin/redwake
```

### Test
```bash
uv run pytest
uv run ruff check redwake
uv run mypy redwake
```

### Custom skill
```bash
mkdir -p ~/.config/redwake/skills/custom
cat > ~/.config/redwake/skills/custom/my-skill.md << 'EOF'
---
name: my-skill
description: My custom pentest methodology
---
# My Skill
...
EOF
```

---

## 🔌 İnteqrasiyalar

### Webhook bildirişləri (Slack / Discord / Teams)

Scan bitəndən sonra avtomatik bildiriş göndərmək üçün webhook URL təyin et:

```bash
export REDWAKE_WEBHOOK_URL='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
export REDWAKE_NOTIFY_ON_SCAN_END='true'   # default true
redwake -t https://target.com --non-interactive --scan-mode quick
```

Bildiriş Markdown formatında göndərilir, status + vulnerabilities + breakdown + run ID daxildir. Webhook timeout və ya connection fail olarsa scan dayanmır — yalnız `warning` log yazılır.

Disable etmək üçün: `REDWAKE_NOTIFY_ON_SCAN_END=false`.

### GitHub Actions (CI/CD)

`.github/workflows/pentest.yml` artıq repository-də var. İstifadə:

1. Fork et, repo-da `Settings → Secrets → Actions` bölməsinə əlavə et:
   - `REDWAKE_LLM` (model adı, məs. `gpt-4o`)
   - `REDWAKE_API_KEY` (provider API key)
   - `REDWAKE_BASE_URL` (OpenAI-compatible endpoint)
   - `SLACK_WEBHOOK_URL` (optional, bildiriş üçün)
2. Actions tab → "RedWake Pentest" workflow → "Run workflow"
3. Target URL daxil et, scan başlayır
4. Bitəndə: scan-report.md + redwake_runs/ artifact kimi yüklənir (30 gün retention)

Schedule variant da var: hər Bazar ertəsi 02:00 UTC. Manual tövsiyə olunur (hər scan üçün review lazımdır).

---

## 🤝 Töhfə

PR-lar qəbul edilir. Töhfə üçün [CONTRIBUTING.md](CONTRIBUTING.md)-ə bax.

---

## 📞 Dəstək

- **Docs:** [GETTING_STARTED.md](GETTING_STARTED.md), [USAGE.md](USAGE.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md), [FAQ.md](FAQ.md)
- **Təhlükəsizlik:** security@redwake.rf.gd
- **Issues:** https://github.com/wakxup777/redwake/issues

---

## ⚖️ Hüquqi

**Lisenziya:** Apache 2.0 — bax: [LICENSE](LICENSE)

Bu alət **yalnız sizin sahib olduğunuz və ya yazılı icazəniz olan sistemlərə qarşı** istifadə üçündür. İcazəsiz giriş qanunsuzdur. RedWake Security Labs aləti "AS IS" təqdim edir, sui-istifadəyə görə məsuliyyət daşımır.
