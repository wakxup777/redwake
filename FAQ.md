# FAQ — tez-tez verilən suallar

## Lisenziya

### Bir neçə maşında istifadə edə bilərəmmi?

Xeyr. Hər RedWake key **bir maşına bağlıdır** (machine fingerprint). Başqa maşında istifadə etmək istəyirsənsə:

- Server "fingerprint mismatch" xətası verəcək
- Admin ilə əlaqə saxla — yeni fingerprint üçün yeni key istə
- Birdən çox maşın üçün birdən çox key istə

Buna səbəb: license sharing detection. Server eyni key-i >1 fingerprint/24h görəndə avtomatik revoke edir.

### Key nə qədər müddətə keçərlidir?

Sənə verilən `--days` parametrindən asılıdır (default 365). Müddəti yoxlamaq:
```bash
echo "REDWAKE-LIC-..." | tr '-' '\n' | sed -n '2p' | base32 -d | python3 -c "import sys, time; print(time.ctime(int(sys.stdin.read().decode())))"
```

Müddət bitəndə server "expired" qaytarır. Yeni key lazımdır.

### Key müddəti bitibsə nə olur?

Cache 1 saat saxlanılır. 1 saatdan sonra server-ə sorğu gedəndə "expired" alırsan. Yeni key üçün admin-ə yaz.

### Server admin tərəfindən revoke olunubsa?

```bash
License verification failed: License key has been revoked. Reason: <admin_revoke>
```

Yeni key üçün admin ilə əlaqə. Cache təmizlə:
```bash
rm -f ~/.redwake/.license_cache
```

### Offline işləyə bilərəmmi?

Yalnız qısa müddətə (1 saat cache). Sonra server-ə sorğu lazımdır. Davamlı offline istifadə üçün müştəri + server hər ikisi off-grid olmalıdır.

### Key harada saxlanılır?

Yalnız env var (`REDWAKE_LICENSE_KEY`) və ya shell rc (`~/.zshrc`). Disk-də heç bir yerdə plaintext saxlanılmır.

## Lisenziya qiyməti və alınması

### Pulsuz sınaq versionu varmı?

Xeyr. Hər scan üçün admin-dən key almalısan.

### Refund mümkündürmü?

Admin ilə əlaqə. Out-of-scope (support@redwake.rf.gd).

### Toplu license almaq mümkündürmü?

Bəli, admin-ə `komanda@example.com --count 10` tipli sorğu göndər.

## Texniki

### Source code auditable-dırmı?

Bəli. Apache 2.0 lisenziyası. Repo açıqdır: https://github.com/redwake/redwake

### Open source tərəfindən fork edilə bilərmi?

Bəli, Apache 2.0 icazə verir, amma:
- Fork üçün də license key lazımdır (server-side check)
- Fork-umuza yeni endpoint obfuscation lazımdır
- Anti-tamper qorunmalı saxlanılmalıdır

### RedWake nədir?

RedWake **RedWake Security Labs** tərəfindən hazırlanmış çox-agentli AI penetration testing platformasıdır. Avtonom agentlər real hacker kimi davranır, kodu dinamik olaraq işlədir, zəiflikləri tapır və real proof-of-concept-lərlər təqdim edir.

### Sandbox image nədir?

Docker container RedWake hər scan üçün yaradır. İçində:
- Python tool-lar (sqlmap, nuclei, httpx, katana, ...)
- Caido proxy (trafik interception)
- Ssenari üçün təmiz environment

Default image: `ghcr.io/redwake/redwake-sandbox:1.0.0`.

### Niyə Docker istifadə edir?

Təhlükəsizlik:
- Host sistemindən izolyasiya
- Tool-ları hər scan üçün təmiz install
- Şəbəkə NET_ADMIN cap ilə isolated

Asanlıq:
- Bütün dependency-lər bir image-də
- Reproducible scan-lər

## Performance

### Scan nə qədər çəkir?

| Mode | Vaxt |
|---|---|
| `quick` | 5-10 dəq |
| `standard` | 15-30 dəq |
| `deep` | 30-90 dəq |

Vaxt dəyişir: target ölçüsü, LLM sürəti, network latency.

### Çoxlu target paralel edə bilərəmmi?

Bəli:
```bash
redwake -t https://app.com -t https://api.com -t https://admin.com --non-interactive
```

### Büdcə limiti necə işləyir?

`--max-budget-usd N` qoyduqda, LLM cost bu həddə çatanda scan graceful dayanır. Hər request-in cost-u izlənir.

### Daha sürətli model istifadə edə bilərəmmi?

Bəli:
```bash
export REDWAKE_LLM='fable-5'        # sürətli, ucuz
export REDWAKE_LLM='gpt-5-mini'    # sürətli, keyfiyyətli
export REDWAKE_REASONING_EFFORT='low'
```

Keyfiyyət aşağı düşə bilər — model seçimi sənin LLM endpoint-in və balansına bağlıdır.

## Hüquqi

### İcazəsiz target-ə scan edə bilərəmmi?

**XEYR.** Yalnız öz sahibliyində və ya yazılı icazəniz olan sistemlərə qarşı istifadə edin. İcazəsiz giriş qanunsuzdur (CFAA, GDPR, lokal qanunlar).

### RedWake qanunidirmi?

Bəli, alət kimi. İstifadə qaydası istifadəçidən asılıdır.

### Sorumluluk kimdədir?

Yalnız səndə. RedWake Security Labs aləti "AS IS" təqdim edir, sui-istifadəyə görə məsuliyyət daşımır.

## Daha çox yardım

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — texniki problemlər
- [INSTALL.md](INSTALL.md) — quraşdırma
- [USAGE.md](USAGE.md) — CLI reference
- GitHub Issues: https://github.com/redwake/redwake/issues
- Təhlükəsizlik: security@redwake.rf.gd
