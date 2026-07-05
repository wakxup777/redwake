# Security Policy

## Reporting a Vulnerability

RedWake açıq mənbə bir layihədir və təhlükəsizlik zəifliklərini ciddi qəbul edir. Hər hansı bir təhlükəsizlik məsələsi aşkar etsəniz:

**Email:** security@redwake.rf.gd
**PGP key:** (email ilə sorğu edin)
**Subject line:** `[SECURITY] <qısa təsvir>`

Zəhmət olmasa **public GitHub issue açmayın** təhlükəsizlik zəiflikləri üçün.

### Nə daxil edilməlidir

1. **Zəifliyin təsviri**
2. **Addım-addım reproduksiya** (kifayət qədər detallı)
3. **Təsirə məruz qalan versiyalar** (məs., v1.0.4-redwake.1)
4. **Impact** qiymətləndirməsi (RCE, info disclosure, və s.)
5. **Mühit** (OS, Python versiyası, quraşdırma üsulu)

### Cavab müddətləri

- **24 saat:** ilkin təsdiq
- **72 saat:** triage və ciddilik təsnifatı
- **7 gün:** yüksək/kritik üçün patch inkişafı
- **30 gün:** açıqlama (reporter ilə əlaqəli şəkildə)

### Əhatə dairəsi

Əhatə daxilində:
- Sandbox escape
- Container-dən kənar code execution (host-a)
- Təsadüfi və ya qəsdən data exfiltration
- RedWake agent-lərində və ya runtime-da zəifliklər

Əhatə xaricində:
- Dependency-lərdəki zəifliklər (müvafiq maintainer-lərə report edin)
- Sosial mühəndislik
- Fiziki hücumlar
- DoS (RedWake nüfuzetmə test alətidir — DoS testləri uyğun deyil)

### Bounty proqramı

RedWake hal-hazırda pullu bug bounty proqramı təklif etmir. Lakin:
- CHANGELOG.md-da açıq kredit (istək əsasında)
- Açıq mənbə layihəsi olaraq dərhal fix

## Məsuliyyətli İstifadə

RedWake güclü hücum təhlükəsizlik alətidir. Böyük güc böyük məsuliyyət deməkdir.

### ✅ Məqbul istifadə

- **Sahib olduğunuz** tətbiqlərin test edilməsi (şirkətiniz, layihəniz)
- **Yazılı səlahiyyətlə** səlahiyyətli penetration testləri (məs., bug bounty proqramı, red team işi)
- **Ayrılmış lab mühitlərində** təhlükəsizlik tədqiqatları (DVWA, HackTheBox, VulnHub, öz VM-ləriniz)
- CTF yarışları
- Akademik tədqiqat (müvafiq IRB təsdiqi ilə)

### ❌ Qadağan edilmiş istifadə

- **Açıq yazılı icazə olmadan** sistemləri skan etmək
- Kritik infrastruktura hücum (səhiyyə, enerji, nəqliyyat)
- DDoS / availability hücumları
- Şantaj (ransomware tipli təhdidlər)
- Lokal, milli və ya beynəlxalq qanunu pozan hər hansı fəaliyyət

### Hüquqi çərçivə

RedWake Apache 2.0 lisenziyası altında təqdim olunur. Lisenziyaya aşağıdakılar daxildir:

> SOFTWARE "AS IS" ƏSASINDA, HƏR HANSI BİR ZƏMANƏT OLMAQDAN TƏQDİM EDİLİR...

Siz RedWake-dən istifadənizin bütün tətbiq olunan qanun və qaydalara uyğun olmasını təmin etməkdə **tam məsuliyyət daşıyırsınız**.

## Threat Model

RedWake qoruyur:
- Default sandbox izolyasiyası
- Container sərhədləri (escape olmadıqda)
- Şəbəkə namespace izolyasiyası (NET_ADMIN cap ilə)

RedWake **QORUMUR**:
- Dövlət səviyyəli aktyorlardan
- Təcrübəli reverse engineer-lərdən
- İnsider təhdidlərdən (sizin VPS-ə admin girişi olan şəxsdən)
- Maşınınıza fiziki girişdən
- Maşınınızın rootlanmasından

## Kriptografiya

RedWake istifadə edir:
- **TLS** bütün xarici LLM endpoint iletişimi üçün
- **Docker content trust** sandbox image-ləri üçün (konfiqurasiya olduqda)

## Data emalı

RedWake LLM endpoint-ə göndərir:
- Sorğu konteksti (scan hədəfi, tapılmış zəifliklər, exploit cəhdləri)

RedWake LLM endpoint-ə **GÖNDƏRMİR**:
- Sizin API açarlarınız
- Şəxsi fayllarınız
- Autentifikasiya token-ləriniz

## Əlaqə

- **Ümumi:** hi@redwake.rf.gd
- **Təhlükəsizlik:** security@redwake.rf.gd
- **Veb sayt:** https://redwake.rf.gd
- **GitHub Issues:** https://github.com/wakxup777/redwake/issues
