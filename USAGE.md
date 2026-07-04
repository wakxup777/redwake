# Usage — CLI Reference

Bütün RedWake əmrləri, flag-ləri və env var-ları.

---

## Əsas sintaksis

```bash
redwake [FLAGS] [OPTIONS]
```

**Mütləq:**
- `-t TARGET` və ya `--mount PATH` və ya `--resume RUN_NAME`

**Ümumi flag-lər:**

| Flag | Təsvir |
|---|---|
| `-t, --target URL` | Test et: URL, repo, IP, domain, lokal path |
| `--mount PATH` | Sandbox-a lokal qovluğu bind-mount et (read-only) |
| `--instruction "..."` | Scan fokusu (inline) |
| `--instruction-file FILE` | Scan fokusu (fayldan) |
| `-n, --non-interactive` | TUI olmadan, skript üçün |
| `-m, --scan-mode MODE` | `quick` / `standard` / `deep` (default: deep) |
| `--scope-mode MODE` | `auto` / `diff` / `full` |
| `--diff-base REF` | Diff-scope üçün base branch |
| `--config FILE` | Alternativ config faylı |
| `--max-budget-usd N` | Maks LLM maliyyəti (USD), sonra dayanır |
| `--resume NAME` | Dayandırılmış scan-i davam et |

---

## Scan rejimləri

| Mode | Vaxt | Nə edir |
|---|---|---|
| `quick` | 5-10 dəq | Recon + high-probability vectors |
| `standard` | 15-30 dəq | Genişləndirilmiş test siyahısı |
| `deep` | 30-90 dəq | Tam attack surface + biznes məntiq |

Production pentest üçün `deep`, CI/CD üçün `quick` tövsiyə olunur.

---

## Çoxlu target

```bash
redwake -t https://app.com -t https://api.app.com -t ./repo --non-interactive
```

Hər target üçün paralel scan işləyir.

---

## İnteraktiv TUI

`redwake -t https://target.com` (heç bir `--non-interactive` olmadan):

| Qısa yol | Funksiya |
|---|---|
| `F1` | Help |
| `Esc` | Scan-i dayandır |
| `Ctrl+Q` / `Ctrl+C` | Çıxış |
| `Enter` | Agent-ə mesaj göndər |
| `Tab` | Panel arasında keçid |
| `↑/↓` | Tree naviqasiya |

---

## Environment variables

### License (mütləq)

| Var | Nə edir |
|---|---|
| `REDWAKE_LICENSE_KEY` | Admin-dən alınmış `REDWAKE-LIC-...` key |
| `REDWAKE_LICENSE_BYPASS` | `1` qoy → license check skip (testing only!) |

### LLM (mütləq)

| Var | Nə edir |
|---|---|
| `REDWAKE_LLM` | Model adı: `gpt-4o`, `claude-opus-4-8`, `asdsadasad/claude-opus-4-8` |
| `REDWAKE_API_KEY` | OpenAI-compatible API key |
| `REDWAKE_BASE_URL` | Custom endpoint (proxy və ya local LLM üçün) |
| `REDWAKE_API_BASE` | Alias |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | OpenAI SDK native adları (alias kimi qəbul edilir) |

### Sandbox

| Var | Nə edir |
|---|---|
| `REDWAKE_IMAGE` | Docker image override (default: `ghcr.io/redwake/redwake-sandbox:1.0.0`) |
| `REDWAKE_RUNTIME_BACKEND` | `docker` / future `podman` |
| `REDWAKE_MAX_LOCAL_COPY_MB` | Lokal target üçün MB limiti (default: 1024) |

### Davranış

| Var | Nə edir |
|---|---|
| `REDWAKE_TELEMETRY` | `true` (default) / `false` |
| `REDWAKE_REASONING_EFFORT` | `none` / `minimal` / `low` / `medium` / `high` / `xhigh` (default: high) |
| `REDWAKE_DEBUG` | `0` (default) / `1` — verbose logging |

### Config fayl ilə persistent

`~/.redwake/cli-config.json`:
```json
{
  "env": {
    "REDWAKE_LLM": "asdsadasad/claude-opus-4-8",
    "REDWAKE_API_KEY": "sk-...",
    "REDWAKE_BASE_URL": "<your-llm-endpoint>",
    "REDWAKE_IMAGE": "ghcr.io/redwake/redwake-sandbox:1.0.0",
    "REDWAKE_TELEMETRY": "false"
  }
}
```

`--config /path/to/cli-config.json` ilə alternativ fayl.

---

## Fokus verilmiş scan

```bash
redwake -t https://target.com --non-interactive \
    --instruction "Focus only on IDOR, SSRF, and authentication bypass. Use multiple sessions."
```

`--instruction-file ./rules.md` ilə uzun instruksiyalar:

```markdown
# redwake-rules.md
You are testing an Azeri banking API.

Focus areas:
1. IDOR on /api/v1/account/{iban}/balance — test with own session vs other accounts
2. Mass assignment on /api/v1/transfer — check role and amount fields
3. JWT confusion — try alg=none, kid injection
4. SSRF on /api/v1/webhook — try internal IPs (127.0.0.1, 169.254.169.254)

Out of scope:
- DDoS / rate limit bypass
- Physical access
```

---

## Büdcə limiti (CI/CD üçün vacib)

```bash
redwake -t https://target.com --non-interactive --max-budget-usd 2.00
```

LLM cost bu həddə çatanda scan graceful dayanır, exit code 0 (uğurlu) və ya 1 (tapıntı tapılıbsa) olur.

---

## Resume

Scan abort olubsa (Ctrl+C, timeout, crash), `redwake_runs/<run>_<timestamp>/` qovluğu qalır. Davam et:

```bash
redwake --resume target-com_a4f2
```

Agent bütün konteksti bərpa edir, sıfırdan başlamır.

---

## LLM model seçimi

```bash
# OpenAI bare name (default routing)
export REDWAKE_LLM='gpt-4o'

# Custom proxy prefix (recommended for stability)
export REDWAKE_LLM='asdsadasad/claude-opus-4-8'

# Multi-step reasoning
export REDWAKE_REASONING_EFFORT='xhigh'

# Quick + cheap
export REDWAKE_REASONING_EFFORT='low'
```

Tövsiyələr:
| Model | Pentest keyfiyyəti | Xərc | Tövsiyə |
|---|---|---|---|
| `asdsadasad/claude-opus-4-8` | ★★★★★ | yüksək | Real engagement üçün ən yaxşı |
| `nvidia/deepseek-ai/deepseek-v4-pro` | ★★★★ | orta | Balans |
| `gemini/gemini-3-pro-preview` | ★★★★ | orta | Recon üçün |
| `tokyo/claude-opus-4.8` | ★★★★★ | yüksək | Opus alternativ |
| `fable-5` | ★★★ | aşağı | Quick test / CI |

---

## Real workflow nümunəsi

```bash
# 1. Env qur (bir dəfə)
export REDWAKE_LICENSE_KEY='REDWAKE-LIC-...'
export REDWAKE_LLM='asdsadasad/claude-opus-4-8'
export REDWAKE_API_KEY='sk-...'
export REDWAKE_BASE_URL='<your-llm-endpoint>'

# 2. Recon-only scan
redwake -t https://target.com --non-interactive --scan-mode quick --max-budget-usd 0.50

# 3. Deep pentest (tapıntıları recon-dan istifadə edərək)
redwake -t https://target.com --non-interactive --scan-mode deep \
    --instruction "Focus on auth bypass and IDOR. Already mapped: /api/users, /api/orders" \
    --max-budget-usd 5.00

# 4. Resume if interrupted
redwake --resume target-com_a4f2

# 5. Nəticəni yoxla
ls -lh redwake_runs/target-com_*/
cat redwake_runs/target-com_*/penetration_test_report.md
```
