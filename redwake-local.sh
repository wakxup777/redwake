#!/usr/bin/env bash
# RedWake local runner — bind-mount local source into rebranded sandbox image
# This avoids needing to rebuild the sandbox image with Python deps baked in.
#
# Usage:
#   ./redwake-local.sh -t https://target.com --non-interactive --scan-mode quick
#
# Requirements:
#   - Local redwake-repo/ with `uv sync` already done
#   - Docker Hub image docker.io/wakxup777/redwake-sandbox:1.0.0 (has pentest tools)
#   - SSH tunnel to license server: 127.0.0.1:18000 (or AWS SG port 8000 open)

set -euo pipefail

REDWAKE_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${REDWAKE_IMAGE:-docker.io/wakxup777/redwake-sandbox:1.0.0}"
LICENSE_SERVER="${REDWAKE_LICENSE_SERVER:-http://127.0.0.1:18000}"

if [[ ! -d "${REDWAKE_REPO}/.venv" ]]; then
    echo "ERROR: redwake-repo/.venv not found. Run 'uv sync' first." >&2
    exit 1
fi

# Collect all env vars to pass to container
ENV_ARGS=()
for var in REDWAKE_LICENSE_KEY REDWAKE_LICENSE_SERVER REDWAKE_LLM OPENAI_API_KEY OPENAI_BASE_URL REDWAKE_TELEMETRY REDWAKE_DEBUG; do
    if [[ -n "${!var:-}" ]]; then
        ENV_ARGS+=("-e" "${var}=${!var}")
    fi
done

# Run container with local source mounted
exec docker run --rm -i \
    --network host \
    -v "${REDWAKE_REPO}:/workspace/redwake" \
    -v "${REDWAKE_REPO}/.venv:/app/.venv" \
    -w /workspace/redwake \
    "${ENV_ARGS[@]}" \
    "${IMAGE}" \
    bash -c '
set -e
# Sync Python deps (idempotent, uses host .venv cache)
uv pip install --python /app/.venv/bin/python --quiet -e . 2>&1 | tail -3
# Run redwake with local source
exec /app/.venv/bin/python -m redwake.interface.main "$@"
' -- "$@"
