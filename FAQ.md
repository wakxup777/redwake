# FAQ — tez-tez verilən suallar

## Ümumi

### RedWake nədir?

RedWake çox-agentli AI penetration testing platformasıdır. Avtonom agentlər real hacker kimi davranır, kodu dinamik olaraq işlədir, zəiflikləri tapır və real proof-of-concept-lərlər təqdim edir. Tamamilə open source-dur (Apache 2.0).

### Source code auditable-dırmı?

Bəli. Apache 2.0 lisenziyası. Repo açıqdır: https://github.com/wakxup777/redwake

### Open source tərəfindən fork edilə bilərmi?

Bəli, Apache 2.0 bunu açıq şəkildə icazə verir. Heç bir license server, anti-tamper, və ya endpoint obfuscation tələbi yoxdur — fork etdikdən sonra dərhal istifadə edə bilərsiniz.

### Sandbox image nədir?

Docker container RedWake hər scan üçün yaradır. İçində:
- Python tool-lar (sqlmap, nuclei, httpx, katana, ...)
- Caido proxy (trafik interception)
- Ssenari üçün təmiz environment

Default image: `docker.io/wakxup777/redwake-sandbox:1.0.0`.

### Niyə Docker istifadə edir?

Təhlükəsizlik:
- Host sistemindən izolyasiya
- Tool-ları hər scan üçün təmiz install
- Şəbəkə NET_ADMIN cap ilə isolated

Asanlıq:
- Bütün dependency-lər bir image-də
- Reproducible scan-lər

### LLM istifadə etməliyəmmi?

Bəli — RedWake AI agentlər işlədir və onlar LLM-dən istifadə edir. Default olaraq `https://redwakeai.vercel.app/api/v1` endpoint-inə bağlanır. İstəsəniz öz LLM provider-inizi istifadə edə bilərsiniz (OpenAI, Anthropic, local LLM, və s.).

## Texniki

### LLM endpoint-ini dəyişə bilərəmmi?

Bəli — `redwake/config/settings.py` faylındakı default-ları `REDWAKE_LLM`, `REDWAKE_API_KEY`, `REDWAKE_BASE_URL` environment variable-ları ilə override edin. `~/.config/redwake/cli-config.json` faylı da dəstəklənir.

### LLM-i necə seçirəm?

Keyfiyyət və sürət arasında balans:
```bash
export REDWAKE_LLM='gpt-4o'           # keyfiyyətli
export REDWAKE_LLM='gpt-4o-mini'      # sürətli, ucuz
export REDWAKE_LLM='gpt-5'            # ən keyfiyyətli (OpenAI)
export REDWAKE_REASONING_EFFORT='low'
```

### Çoxlu target paralel edə bilərəmmi?

Bəli:
```bash
redwake -t https://app.com -t https://api.com -t https://admin.com --non-interactive
```

### Büdcə limiti necə işləyir?

`--max-budget-usd N` qoyduqda, LLM cost bu həddə çatanda scan graceful dayanır. Hər request-in cost-u izlənir.

## Performance

### Scan nə qədər çəkir?

| Mode | Vaxt |
|---|---|
| `quick` | 5-10 dəq |
| `standard` | 15-30 dəq |
| `deep` | 30-90 dəq |

Vaxt dəyişir: target ölçüsü, LLM sürəti, network latency.

### Daha sürətli model istifadə edə bilərəmmi?

Bəli:
```bash
export REDWAKE_LLM='gpt-4o-mini'    # sürətli, keyfiyyətli
export REDWAKE_LLM='gpt-5-mini'    # ən sürətli
export REDWAKE_REASONING_EFFORT='low'
```

Keyfiyyət aşağı düşə bilər — model seçimi sənin LLM endpoint-in və balansına bağlıdır.

## Hüquqi

### İcazəsiz target-ə scan edə bilərəmmi?

**XEYR.** Yalnız öz sahibliyində və ya yazılı icazəniz olan sistemlərə qarşı istifadə edin. İcazəsiz giriş qanunsuzdur (CFAA, GDPR, lokal qanunlar).

### RedWake qanunidirmi?

Bəli, alət kimi. İstifadə qaydası istifadəçidən asılıdır.

### Sorumluluk kimdədir?

Yalnız səndə. RedWake aləti "AS IS" təqdim edir, sui-istifadəyə görə məsuliyyət daşımır.

## Daha çox yardım

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — texniki problemlər
- [INSTALL.md](INSTALL.md) — quraşdırma
- [USAGE.md](USAGE.md) — CLI reference
- GitHub Issues: https://github.com/wakxup777/redwake/issues
- Təhlükəsizlik: security@redwake.rf.gd
