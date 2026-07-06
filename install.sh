#!/usr/bin/env bash
# RedWake installer — Linux/macOS/WSL2
# Detects OS, ensures Docker + uv, builds binary, adds to PATH
mkdir -p ~/.local/bin
wget -O ~/.local/bin/redwake https://github.com/wakxup777/redwake/releases/download/v1.0.0/redwake-1.0.0-linux-x86_64
chmod +x ~/.local/bin/redwake

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

INSTALL_DIR="${HOME}/.local/bin"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() { echo -e "${GREEN}[+]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err() { echo -e "${RED}[x]${NC} $*" >&2; exit 1; }

# ── Detect OS ──
detect_os() {
    case "$(uname -s)" in
        Linux*)
            if [[ -f /etc/os-release ]]; then
                . /etc/os-release
                case "${ID:-}" in
                    debian|ubuntu|pop|linuxmint|elementary) echo "debian" ;;
                    fedora|rhel|centos|rocky|almalinux|ol) echo "fedora" ;;
                    arch|manjaro|endeavouros) echo "arch" ;;
                    alpine) echo "alpine" ;;
                    *) echo "linux-other" ;;
                esac
            else
                echo "linux-other"
            fi
            ;;
        Darwin*) echo "macos" ;;
        MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
        *) err "Unsupported OS: $(uname -s)" ;;
    esac
}

OS=$(detect_os)
log "Detected OS: ${OS}"

# ── Check Docker ──
ensure_docker() {
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            log "Docker OK: $(docker --version)"
            return 0
        fi
        warn "Docker installed but daemon not running"
    fi
    warn "Docker not available — installing..."
    case "${OS}" in
        debian)
            sudo apt update -qq && sudo apt install -y -qq docker.io
            sudo systemctl start docker 2>/dev/null || true
            sudo systemctl enable docker 2>/dev/null || true
            sudo usermod -aG docker "${USER}"
            warn "Logout/login may be required for docker group membership"
            ;;
        fedora)
            sudo dnf install -y docker
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker "${USER}"
            ;;
        arch)
            sudo pacman -S --noconfirm docker
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker "${USER}"
            ;;
        alpine)
            sudo apk add docker
            sudo rc-update add docker boot
            sudo service docker start
            sudo addgroup "${USER}" docker
            ;;
        macos)
            warn "Please install Docker Desktop manually: https://docker.com/products/docker-desktop/"
            err "After installing, re-run ./install.sh"
            ;;
        linux-other)
            err "Please install Docker manually, then re-run ./install.sh"
            ;;
    esac
    if ! docker info >/dev/null 2>&1; then
        err "Docker still not working. Visit: https://docs.docker.com/engine/install/"
    fi
}

# ── Sandbox image (pull rebranded image from Docker Hub) ──
ensure_sandbox_image() {
    local REDWAKE_IMAGE="${REDWAKE_IMAGE:-docker.io/wakxup777/redwake-sandbox:1.0.0}"

    # If image already exists locally, skip
    if docker image inspect "${REDWAKE_IMAGE}" >/dev/null 2>&1; then
        log "Sandbox image present: ${REDWAKE_IMAGE}"
        return 0
    fi

    # Pull from Docker Hub (3 min first time, ~3 GB)
    log "Pulling sandbox image (one-time, ~3GB)..."
    if docker pull "${REDWAKE_IMAGE}" 2>&1 | tail -3; then
        log "Pulled: ${REDWAKE_IMAGE}"
    else
        err "Failed to pull ${REDWAKE_IMAGE}. Check your network or set REDWAKE_IMAGE manually."
    fi
}

# ── Check uv ──
ensure_uv() {
    if command -v uv >/dev/null 2>&1; then
        log "uv OK: $(uv --version)"
        return 0
    fi
    warn "uv not found — installing..."
    if ! command -v curl >/dev/null 2>&1; then
        err "curl not found. Install curl and re-run."
    fi
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="${HOME}/.local/bin:${PATH}"
    if ! command -v uv >/dev/null 2>&1; then
        err "uv install failed. Visit: https://docs.astral.sh/uv/getting-started/installation/"
    fi
    log "uv installed: $(uv --version)"
}

# ── Build RedWake ──
build_redwake() {
    log "Syncing dependencies..."
    (cd "${REPO_DIR}" && uv sync --quiet)

    log "Building RedWake binary..."
    (cd "${REPO_DIR}" && uv run pyinstaller --clean redwake.spec)

    if [[ ! -f "${REPO_DIR}/dist/redwake" ]]; then
        err "Build failed — dist/redwake not found"
    fi

    log "Built: ${REPO_DIR}/dist/redwake"
}

# Install the built binary into one of several target locations.
# Tries /usr/local/bin first (no PATH config needed), then ~/.local/bin,
# then ~/bin. The first one that succeeds is used.
install_binary() {
    local binary="${REPO_DIR}/dist/redwake"
    local target=""

    # 1. /usr/local/bin (system-wide, no PATH config)
    if [[ -w /usr/local/bin ]] || sudo -n true 2>/dev/null; then
        if sudo -n install -m 0755 "${binary}" /usr/local/bin/redwake 2>/dev/null \
            || install -m 0755 "${binary}" /usr/local/bin/redwake 2>/dev/null; then
            target="/usr/local/bin"
        fi
    fi

    # 2. ~/.local/bin (user-local, needs PATH config)
    if [[ -z "${target}" ]]; then
        mkdir -p "${HOME}/.local/bin"
        if install -m 0755 "${binary}" "${HOME}/.local/bin/redwake" 2>/dev/null; then
            target="${HOME}/.local/bin"
        fi
    fi

    # 3. ~/bin (legacy fallback)
    if [[ -z "${target}" ]]; then
        mkdir -p "${HOME}/bin"
        if install -m 0755 "${binary}" "${HOME}/bin/redwake" 2>/dev/null; then
            target="${HOME}/bin"
        fi
    fi

    if [[ -z "${target}" ]]; then
        err "Could not install binary to /usr/local/bin, ~/.local/bin, or ~/bin. Check permissions."
    fi

    log "Installed: ${target}/redwake"
    INSTALL_DIR="${target}"
}

# ── PATH ──
ensure_path() {
    # If the install target is already on PATH (true for /usr/local/bin),
    # we don't need to touch rc files at all.
    if command -v redwake >/dev/null 2>&1; then
        log "redwake on PATH: $(command -v redwake)"
        return 0
    fi

    # Otherwise, append to ~/.bashrc and ~/.zshrc so future shells see it.
    for rc in "${HOME}/.bashrc" "${HOME}/.zshrc"; do
        [[ -f "${rc}" ]] || continue
        if ! grep -qF "${INSTALL_DIR}" "${rc}" 2>/dev/null; then
            echo "" >> "${rc}"
            echo "# Added by RedWake installer" >> "${rc}"
            echo "export PATH=\"\${PATH}:${INSTALL_DIR}\"" >> "${rc}"
            log "Updated: ${rc}"
        fi
    done

    # Also export in the current shell so this session works immediately.
    export PATH="${PATH}:${INSTALL_DIR}"
    if command -v redwake >/dev/null 2>&1; then
        log "redwake on PATH (current shell): $(command -v redwake)"
    else
        warn "PATH updated, but restart your shell or run: export PATH=\"\${PATH}:${INSTALL_DIR}\""
    fi
}

# ── Verify ──
verify() {
    if ! command -v redwake >/dev/null 2>&1; then
        err "redwake not in PATH. Try: export PATH=\"\${PATH}:${INSTALL_DIR}\""
    fi
    local version
    version=$(redwake --version 2>&1 | head -1)
    log "Verify: ${version}"
}

main() {
    echo ""
    echo "RedWake installer"
    echo "================="
    echo ""

    ensure_docker
    ensure_uv
    build_redwake
    install_binary
    ensure_sandbox_image
    ensure_path
    verify

    echo ""
    log "Install complete!"
    echo ""
    echo "Next steps:"
    echo "  1. (İstəyə bağlı) Default LLM endpoint-ini override et:"
    echo "     export REDWAKE_LLM='redwake-cli'"
    echo "     export REDWAKE_API_KEY='rw-segpp76kmgi4ipxo1k7em'"
    echo "     export REDWAKE_BASE_URL='https://redwakeai.vercel.app/api/v1'"
    echo ""
    echo "  2. First scan:"
    echo "     redwake -t http://testphp.vulnweb.com --non-interactive --scan-mode quick"
    echo ""
    echo "Docs: https://github.com/wakxup777/redwake/blob/main/GETTING_STARTED.md"
    echo ""
}

main "$@"
