# Getting Started — 5 dəqiqəyə RedWake

Bu guide sənə **license key** verildikdən sonra ilk scan-i 5 dəqiqə ərzində başlamağa kömək edəcək.

---

## 1. Tələblər (artıq quraşdırılmış ola bilər)

| Nə | Minimum | Yoxlamaq üçün |
|---|---|---|
| Docker | 20.10+ | `docker --version` |
| Python | 3.12+ | `python3 --version` |
| Git | 2.30+ | `git --version` |
| OS | Linux/macOS/WSL2 | `uname -a` |

## 2. Repo klonla

```bash
git clone https://github.com/redwake/redwake.git
cd redwake
```

## 3. Avtomatik quraşdırma

```bash
./install.sh
```

Bu skript:
- Docker yoxdursa quraşdırır
- `uv` (Python package manager) yoxdursa quraşdırır
- `redwake` binary-ni `~/.local/bin/`-ə qoyur
- `~/.bashrc` və ya `~/.zshrc`-ə PATH əlavə edir

## 4. License key-i aktivləşdir

Admin sənə `REDWAKE-LIC-...` formatında key verib. Hər scan-də bu lazımdır:

```bash
export REDWAKE_LICENSE_KEY='REDWAKE-LIC-...'
```

**Davamlı etmək üçün** `~/.bashrc` və ya `~/.zshrc`-ə əlavə et:

```bash
echo 'export REDWAKE_LICENSE_KEY="REDWAKE-LIC-..."' >> ~/.zshrc
source ~/.zshrc
```

## 5. LLM API tənzimləmələri

OpenAI-compatible endpoint üçün (OpenAI, Anthropic proxy, local LLM):

```bash
export REDWAKE_LLM='gpt-4o'                       # və ya 'asdsadasad/claude-opus-4-8'
export REDWAKE_API_KEY='sk-...'
export REDWAKE_BASE_URL='https://api.openai.com/v1'   # və ya proxy URL
```

OpenAI istifadə edirsənsə, `REDWAKE_BASE_URL` opsionaldır (default OpenAI-a gedir). Proxy və ya custom endpoint üçün mütləqdir.

## 6. İlk scan

Test üçün təhlükəsiz target:
```bash
redwake -t http://testphp.vulnweb.com --non-interactive --scan-mode quick
```

Real target üçün yalnız **öz sahibliyində və ya yazılı icazəli sistemləri** test et:
```bash
redwake -t https://your-target.com --non-interactive --scan-mode deep
```

## 7. Nəticə

Scan bitəndə:
- `penetration_test_report.md` — oxu
- `findings.sarif` — CI/CD üçün
- `redwake.log` — debug üçün
- `run.json` — machine-readable

Bu fayllar `redwake_runs/<target>_<timestamp>/` qovluğundadır.

---

## Sonrakı addımlar

- **İnteraktiv TUI:** `redwake -t https://target.com` (F1=Help, Esc=Stop)
- **Fokus ver:** `--instruction "Focus on IDOR and SSRF"`
- **Büdcə limiti:** `--max-budget-usd 5.00` (çox uzun scan-i dayandırmaq üçün)
- **Çoxlu target:** `redwake -t https://app.com -t https://api.app.com`
- **Resume:** scan abort olubsa, `redwake --resume <run_name>`

Tam CLI reference üçün: [USAGE.md](USAGE.md)
Problem olarsa: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
Sual olarsa: [FAQ.md](FAQ.md)
