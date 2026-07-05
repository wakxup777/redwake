# Troubleshooting — ümumi xətalar və həllər

## Lisenziya xətaları

### "DOCKER NOT INSTALLED"

```bash
sudo apt install -y docker.io  # Debian/Ubuntu
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker
docker ps  # should work without sudo
```

### "Failed to pull docker image"

```bash
Failed to pull docker image ghcr.io/redwake/redwake-sandbox:1.0.0
```

**Həll:**
```bash
# Override (image hələ publish olunmayıbsa)
export REDWAKE_IMAGE='ghcr.io/redwake/redwake-sandbox:1.0.0'

# və ya image-i manual çək
docker pull ghcr.io/redwake/redwake-sandbox:1.0.0
```

### "Sandbox container creation failed"

Docker daemon işləmir:
```bash
sudo systemctl status docker
sudo systemctl restart docker
docker info | grep "Server Version"
```

## LLM xətaları

### "LLM CONNECTION FAILED"

```bash
openai.OpenAIError: Missing credentials. Please pass an `api_key`...
```

**Həll:** `REDWAKE_API_KEY` set et:
```bash
export REDWAKE_API_KEY='sk-...'
```

### "Unknown model name"

```bash
UNKNOWN MODEL NAME
'fable-5' is not a known OpenAI model.
```

**Həll:** Provider prefix istifadə et:
```bash
export REDWAKE_LLM='<provider>/<model>'  # proxy ilə işləyir
```

### "InternalServerError: Hosted_vllmException"

Upstream LLM server qırılıb. 60 saniyə gözlə, retry et. Davamlı problem olarsa, model dəyiş:
```bash
export REDWAKE_LLM='claude-opus-4.8'  # bare, fallback
```

## Scan xətaları

### "Scan failed" / "No exploitable vulnerabilities detected"

Bunlar həmişə xətalar deyil. Səbəbləri:

1. **Network əlçatmazlıq** — target-ə container-dən çıxış yoxdur (sandbox network policy)
2. **Target boş** — real application yoxdur (məs: example.com)
3. **Bütün vectors bloklanıb** — WAF / rate limit / auth
4. **Tool çatışmazlığı** — bax: "Tool X not found in /tmp/..."

**Debug:**
```bash
# Verbose logging
export REDWAKE_DEBUG=1

# Read redwake.log
tail -100 redwake_runs/target-com_*/redwake.log
```

### "Tool X not found in /tmp/..."

Subagent `/tmp/sqlmap/` axtarır, ancaq `/usr/bin/sqlmap` var. Workaround:

```bash
redwake -t https://target.com --non-interactive \
    --instruction "Tools are PRE-INSTALLED at:
- /usr/bin/sqlmap
- /usr/bin/nuclei  
- /home/pentester/go/bin/httpx
- /home/pentester/go/bin/katana
Never install tools to /tmp. Skip missing tools and continue with curl/jq/bash."
```

### "asyncio.CancelledError"

Normal Ctrl+C / timeout abort. Scan uğurla başlamışdı, ancaq abort olundu. Resume et:
```bash
redwake --resume <run_name>
```

## Performance

### Çox yavaş scan

- `--max-budget-usd` qoy ki, çox token istifadə etməsin
- `--scan-mode quick` istifadə et
- Daha sürətli model: `export REDWAKE_LLM='fable-5'`
- Sadə fokus: `--instruction "Test only top 3 vectors: SQLi, IDOR, XSS"`

### Yüksək LLM cost

- `--max-budget-usd 2.00` qoy
- `--scan-mode quick` istifadə et
- Reasoning effort azalt: `export REDWAKE_REASONING_EFFORT='low'`
- Cache TTL 1 saat — tez-tez restart etmə (hər dəfə yenidən verify edir)

## Debug mode

Verbose logging:
```bash
export REDWAKE_DEBUG=1
redwake -t https://target.com --non-interactive
```

Log fayl yeri:
- Stdout (real-time)
- `redwake_runs/<run>/redwake.log` (persistent)

## Reset state

Tamamilə sıfırla:
```bash
rm -rf ~/.redwake redwake_runs/
docker system prune -f  # köhnə sandbox-lar
```

Yenidən başladıqda ilk run-da image təkrar çəkilir (~1-3 dəq).

## Yardım alma

1. **FAQ.md** — ümumi suallar
2. **GitHub Issues:** https://github.com/redwake/redwake/issues
3. **License support:** admin səninlə əlaqə
4. **Təhlükəsizlik problemi:** security@redwake.rf.gd
