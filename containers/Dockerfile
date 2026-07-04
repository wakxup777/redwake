FROM ghcr.io/usestrix/strix-sandbox:1.0.0

# Rebrand: replace all upstream references with RedWake
LABEL org.opencontainers.image.title="redwake-sandbox"
LABEL org.opencontainers.image.description="RedWake — AI Penetration Testing Environment"
LABEL org.opencontainers.image.source="https://github.com/redwake/redwake"
LABEL org.opencontainers.image.vendor="RedWake Security Labs"
LABEL org.opencontainers.image.licenses="Apache-2.0"

# Rebrand PATH entries — overlay our rebranded Python package on top of the
# upstream image's preinstalled tooling.
USER root
COPY --chown=pentester:pentester redwake/tools/proxy/caido_api.py /opt/redwake-python/caido_api.py
ENV PYTHONPATH=/opt/redwake-python

# Rebrand environment variables (upstream image still works because we only
# *add* a layer; existing tools at /usr/bin/, /home/pentester/go/bin/ are kept
# as-is since they're path-based, not name-based).
ENV REDWAKE_HOME=/home/pentester

USER pentester
WORKDIR /workspace

# Health check — confirm key tools are reachable.
RUN command -v sqlmap >/dev/null && \
    command -v nuclei >/dev/null && \
    command -v httpx >/dev/null && \
    command -v katana >/dev/null && \
    command -v caido-cli >/dev/null && \
    command -v python3 >/dev/null && \
    echo "RedWake sandbox ready"
