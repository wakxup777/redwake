"""RedWake application settings — pydantic-settings powered."""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"]

_BASE_CONFIG = SettingsConfigDict(
    case_sensitive=False,
    populate_by_name=True,
    extra="ignore",
)


class LlmSettings(BaseSettings):
    model_config = _BASE_CONFIG

    model: str = Field(default="redwake-cli", alias="REDWAKE_LLM")
    api_key: str = Field(
        default="rw-v62xfhvlv7dw61ocw0odj",
        alias="REDWAKE_API_KEY",
    )
    api_base: str = Field(
        default="https://redwakeai.vercel.app/api/v1",
        alias="REDWAKE_BASE_URL",
    )
    reasoning_effort: ReasoningEffort = Field(default="high", alias="REDWAKE_REASONING_EFFORT")
    timeout: int = Field(default=300, alias="LLM_TIMEOUT")


class RuntimeSettings(BaseSettings):
    model_config = _BASE_CONFIG

    image: str = Field(
        # Default is the upstream RedWake sandbox image (identical content).
        # The rebranded `ghcr.io/redwake/redwake-sandbox` is published when the
        # admin builds and pushes a custom image (see ADMIN_GUIDE.md).
        default="docker.io/wakxup777/redwake-sandbox:1.0.0",
        alias="REDWAKE_IMAGE",
    )
    backend: str = Field(default="docker", alias="REDWAKE_RUNTIME_BACKEND")
    # Hard cap on a local target's size before we refuse to stream it into the
    # sandbox file-by-file (the SDK copies every file individually, which stalls
    # on large repos). Above this, the user must bind-mount via ``--mount``.
    # Set to 0 (or less) to disable the pre-flight check entirely.
    max_local_copy_mb: int = Field(default=1024, alias="REDWAKE_MAX_LOCAL_COPY_MB")


class TelemetrySettings(BaseSettings):
    model_config = _BASE_CONFIG

    enabled: bool = Field(default=True, alias="REDWAKE_TELEMETRY")


class IntegrationSettings(BaseSettings):
    model_config = _BASE_CONFIG

    perplexity_api_key: str | None = Field(default=None, alias="PERPLEXITY_API_KEY")


class NotifySettings(BaseSettings):
    """Webhook notifications for scan completion.

    Slack-compatible JSON POST format. To enable:
        export REDWAKE_WEBHOOK_URL="https://hooks.slack.com/services/..."
    The webhook is fired automatically when scan completes (success, fail,
    or interrupt). Failed POSTs are logged but never abort the scan.
    """

    model_config = _BASE_CONFIG

    webhook_url: str | None = Field(default=None, alias="REDWAKE_WEBHOOK_URL")
    notify_on_scan_end: bool = Field(default=True, alias="REDWAKE_NOTIFY_ON_SCAN_END")
    timeout: int = Field(default=10, alias="REDWAKE_NOTIFY_TIMEOUT")


class Settings(BaseSettings):
    model_config = _BASE_CONFIG

    llm: LlmSettings = Field(default_factory=LlmSettings)
    runtime: RuntimeSettings = Field(default_factory=RuntimeSettings)
    telemetry: TelemetrySettings = Field(default_factory=TelemetrySettings)
    integrations: IntegrationSettings = Field(default_factory=IntegrationSettings)
    notify: NotifySettings = Field(default_factory=NotifySettings)
