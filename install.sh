#!/usr/bin/env bash
# RedWake installer — Linux/macOS/WSL2
# Detects OS, ensures Docker + uv, builds binary, adds to PATH

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

    mkdir -p "${INSTALL_DIR}"
    install -m 0755 "${REPO_DIR}/dist/redwake" "${INSTALL_DIR}/redwake"
    log "Installed: ${INSTALL_DIR}/redwake"
}

# ── PATH ──
ensure_path() {
    case ":${PATH}:" in
        *":${INSTALL_DIR}:"*) log "PATH already includes ${INSTALL_DIR}" ;;
        *)
            warn "${INSTALL_DIR} not in PATH — adding to shell rc"
            for rc in "${HOME}/.bashrc" "${HOME}/.zshrc"; do
                if [[ -f "${rc}" ]]; then
                    if ! grep -q "${INSTALL_DIR}" "${rc}" 2>/dev/null; then
                        echo "" >> "${rc}"
                        echo "# Added by RedWake installer" >> "${rc}"
                        echo "export PATH=\"\${HOME}/.local/bin:\${PATH}\"" >> "${rc}"
                        log "Updated: ${rc}"
                    fi
                fi
            done
            export PATH="${INSTALL_DIR}:${PATH}"
            warn "Restart your shell or run: export PATH=\"${INSTALL_DIR}:\${PATH}\""
            ;;
    esac
}

# ── Verify ──
verify() {
    if ! command -v redwake >/dev/null 2>&1; then
        err "redwake not in PATH. Try: export PATH=\"${INSTALL_DIR}:\${PATH}\""
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
    ensure_sandbox_image
    ensure_path
    verify

    echo ""
    log "Install complete!"
    echo ""
    echo "Next steps:"
    echo "  1. (İstəyə bağlı) Default LLM endpoint-ini override et:"
    echo "     export REDWAKE_LLM='redwake-cli'"
    echo "     export OPENAI_API_KEY='rw-segpp76kmgi4ipxo1k7em'"
    echo "     export REDWAKE_BASE_URL='https://redwakeai.vercel.app/api/v1'"
    echo ""
    echo "  2. First scan:"
    echo "     redwake -t http://testphp.vulnweb.com --non-interactive --scan-mode quick"
    echo ""
    echo "Docs: https://github.com/wakxup777/redwake/blob/main/GETTING_STARTED.md"
    echo ""
}

main "$@"
