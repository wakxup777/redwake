# Install — bütün OS-lər

RedWake-i hər yerdə quraşdırmaq üçün tam təlimat.

## Ən sürətli yol (Linux/macOS/WSL2)

```bash
git clone https://github.com/wakxup777/redwake.git
cd redwake && ./install.sh
```

`install.sh` hər şeyi edir:
- Docker yoxdursa quraşdırır
- `uv` (Python package manager) yoxdursa quraşdırır
- Binary-ni `~/.local/bin/redwake`-ə qoyur
- PATH-i `~/.bashrc`/`~/.zshrc`-ə əlavə edir

---

## Linux

### Debian/Ubuntu (apt)

```bash
sudo apt update
sudo apt install -y docker.io python3-pip
sudo usermod -aG docker $USER  # logout/login lazım
newgrp docker                  # və ya bu

# uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env

# RedWake
git clone https://github.com/wakxup777/redwake.git
cd redwake
uv sync
uv run pyinstaller --clean redwake.spec
cp dist/redwake ~/.local/bin/
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### RHEL/Fedora (dnf)

```bash
sudo dnf install -y docker python3-pip
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env

git clone https://github.com/wakxup777/redwake.git && cd redwake
uv sync && uv run pyinstaller --clean redwake.spec
cp dist/redwake ~/.local/bin/
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Arch (pacman)

```bash
sudo pacman -S docker python-pip
sudo systemctl start docker
sudo usermod -aG docker $USER

# uv (AUR-dan)
yay -S uv

git clone https://github.com/wakxup777/redwake.git && cd redwake
uv sync && uv run pyinstaller --clean redwake.spec
cp dist/redwake ~/.local/bin/
```

### Alpine (apk)

```bash
sudo apk add docker py3-pip
sudo rc-update add docker
sudo service docker start

curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env

git clone https://github.com/wakxup777/redwake.git && cd redwake
uv sync && uv run pyinstaller --clean redwake.spec
cp dist/redwake ~/.local/bin/
```

---

## macOS

### Homebrew

```bash
brew install docker  # Docker Desktop da lazımdır (brew cask install --cask docker)
brew install uv

git clone https://github.com/wakxup777/redwake.git && cd redwake
uv sync && uv run pyinstaller --clean redwake.spec
cp dist/redwake ~/.local/bin/   # və ya: cp dist/redwake /usr/local/bin/
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Apple Silicon** (M1/M2/M3): Docker Desktop ARM64 versiyasını yükləyin.

### Pre-built binary (sürətli)

GitHub Releases-dən yüklə:
```bash
# Intel Mac
curl -L https://github.com/wakxup777/redwake/releases/latest/download/redwake-darwin-x86_64 -o ~/.local/bin/redwake
chmod +x ~/.local/bin/redwake

# Apple Silicon
curl -L https://github.com/wakxup777/redwake/releases/latest/download/redwake-darwin-arm64 -o ~/.local/bin/redwake
chmod +x ~/.local/bin/redwake
```

---

## Windows

### WSL2 (tövsiyə)

Windows-da pentest üçün **WSL2** istifadə et:

```powershell
# PowerShell admin:
wsl --install
wsl --set-default-version 2
```

Sonra Ubuntu-ya daxil ol, [Debian/Ubuntu](#debianubuntu-apt) addımlarını izlə.

### Native Windows (preview)

Native Windows build işləyir, amma Docker Desktop Windows üçün WSL2 backend istifadə edir (hər halda WSL2 lazımdır):

1. **Docker Desktop Windows:** https://docker.com/products/docker-desktop/
2. **Python 3.12+:** https://python.org/downloads/windows/
3. **Git:** https://git-scm.com/download/win
4. **PowerShell:**
   ```powershell
   git clone https://github.com/wakxup777/redwake.git
   cd redwake
   uv sync
   uv run pyinstaller --clean redwake.spec
   .\dist\redwake.exe --help
   ```

---

## Docker (yalnız konteyner)

Pre-built image hələ publish olunmayıb. From-source Docker runtime:

```bash
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e REDWAKE_LLM='REDWAKE-LIC-...' \
  -e REDWAKE_LLM='gpt-4o' \
  -e REDWAKE_API_KEY='sk-...' \
  redwake/redwake:latest \
  -t https://target.com --non-interactive
```

(Docker image admin tərəfindən `ghcr.io/redwake/redwake:latest` ünvanında publish olunmalıdır.)

---

## From source (developer)

```bash
git clone https://github.com/wakxup777/redwake.git
cd redwake

# Dev asılılıqlar (pytest, mypy, ruff, pyinstaller)
uv sync

# Test
uv run pytest

# Lint + type check
uv run ruff check redwake
uv run mypy redwake

# Dev run (source-dan)
uv run redwake -t https://target.com --non-interactive

# Binary build
uv run pyinstaller --clean redwake.spec
ls -lh dist/redwake
```

---

## Pre-built binary (production)

CI/CD-nin yaratdığı binary-lər GitHub Releases-dədir:

| Platform | Fayl |
|---|---|
| Linux x86_64 | `redwake-linux-x86_64` |
| macOS Intel | `redwake-darwin-x86_64` |
| macOS ARM64 | `redwake-darwin-arm64` |
| Windows | `redwake.exe` |

**SHA256SUMS** hər release-də var. Yoxlama:
```bash
curl -L https://github.com/wakxup777/redwake/releases/latest/download/SHA256SUMS | sha256sum -c -
```

---

## Sandbox image

İlk scan-da `ghcr.io/redwake/redwake-sandbox:1.0.0` (~3GB) avtomatik çəkilir.

---

## Yoxlama

```bash
redwake --version
# Expected: redwake 1.0.4 (və ya daha yeni)

redwake --help
# Expected: usage info + "RedWake Multi-Agent Cybersecurity Penetration Testing Tool"

echo $REDWAKE_LLM | head -c 20
# Expected: REDWAKE-LIC-...
```

Problem olarsa: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
