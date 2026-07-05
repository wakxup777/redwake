FROM docker.io/wakxup777/redwake-sandbox:1.0.0

LABEL org.opencontainers.image.title="redwake-sandbox"
LABEL org.opencontainers.image.description="RedWake - AI Penetration Testing Environment"
LABEL org.opencontainers.image.source="https://github.com/redwake/redwake"
LABEL org.opencontainers.image.vendor="RedWake Security Labs"
LABEL org.opencontainers.image.licenses="Apache-2.0"

# === Install Python dependencies via uv (image has uv pre-installed) ===
# The base image includes pentest tools but NOT the redwake agent runtime
# Python dependencies (openai-agents, httpx, litellm, jwt, pydantic-settings).
# Install them into /app/.venv using uv.

USER root

# Verify uv is available (base image should have it)
RUN which uv || (curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh)

# Install runtime deps into the existing /app/.venv using uv
RUN uv pip install --python /app/.venv/bin/python --quiet \
    "openai-agents[litellm]==0.14.6" \
    "pydantic>=2.11.3" \
    "pydantic-settings>=2.13.0" \
    "rich>=13.0.0" \
    "docker>=7.1.0" \
    "textual>=6.0.0" \
    "requests>=2.32.0" \
    "cvss>=3.2" \
    "caido-sdk-client>=0.2.0" \
    "PyJWT[crypto]>=2.9.0" \
    "cryptography>=43.0.0"

# === Add RedWake client package ===
COPY --chown=root:root redwake /app/redwake
ENV PYTHONPATH=/app:/app/redwake

USER pentester
WORKDIR /workspace

# Health check — verify all runtime deps and redwake package import
RUN /app/.venv/bin/python -c 'import openai_agents, httpx, litellm, jwt, pydantic_settings; import sys; sys.path.insert(0, "/app/redwake"); print("RedWake sandbox OK")'
