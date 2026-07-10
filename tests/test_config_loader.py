"""Tests for redwake.config.loader: JSON overrides, alias resolution, persistence."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from pydantic import AliasChoices, Field
from pydantic.fields import FieldInfo

from redwake.config import loader


if TYPE_CHECKING:
    from pathlib import Path


_LLM_ENV_KEYS = [
    # LlmSettings
    "REDWAKE_LLM",
    "REDWAKE_API_KEY",
    "REDWAKE_BASE_URL",
    "LLM_API_KEY",
    "OPENAI_API_KEY",
    "LLM_API_BASE",
    "OPENAI_API_BASE",
    "OPENAI_BASE_URL",
    "LITELLM_BASE_URL",
    "OLLAMA_API_BASE",
    "REDWAKE_REASONING_EFFORT",
    "LLM_TIMEOUT",
    # IntegrationSettings
    "PERPLEXITY_API_KEY",
    # RuntimeSettings
    "REDWAKE_IMAGE",
    "REDWAKE_RUNTIME_BACKEND",
    "REDWAKE_MAX_LOCAL_COPY_MB",
    # TelemetrySettings
    "REDWAKE_TELEMETRY",
    # NotifySettings
    "REDWAKE_WEBHOOK_URL",
    "REDWAKE_NOTIFY_ON_SCAN_END",
    "REDWAKE_NOTIFY_TIMEOUT",
]


@pytest.fixture(autouse=True)
def _reset_loader_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset module globals and clear known env vars for deterministic runs."""
    for key in _LLM_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(loader, "_cached", None)
    monkeypatch.setattr(loader, "_override", None)


# --------------------------------------------------------------------------- #
# _read_json_overrides
# --------------------------------------------------------------------------- #


def test_read_json_overrides_missing_file(tmp_path: Path) -> None:
    assert loader._read_json_overrides(tmp_path / "nope.json") == {}


def test_read_json_overrides_corrupt_json(tmp_path: Path) -> None:
    path = tmp_path / "cli-config.json"
    path.write_text("{not valid json", encoding="utf-8")
    assert loader._read_json_overrides(path) == {}


def test_read_json_overrides_non_dict_env(tmp_path: Path) -> None:
    path = tmp_path / "cli-config.json"
    path.write_text(json.dumps({"env": ["not", "a", "dict"]}), encoding="utf-8")
    assert loader._read_json_overrides(path) == {}


def test_read_json_overrides_maps_to_nested_settings(tmp_path: Path) -> None:
    path = tmp_path / "cli-config.json"
    path.write_text(
        json.dumps({"env": {"REDWAKE_LLM": "my-model", "PERPLEXITY_API_KEY": "pk"}}),
        encoding="utf-8",
    )
    assert loader._read_json_overrides(path) == {
        "llm": {"model": "my-model"},
        "integrations": {"perplexity_api_key": "pk"},
    }


def test_read_json_overrides_skips_keys_already_in_environ(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REDWAKE_LLM", "from-env")
    path = tmp_path / "cli-config.json"
    path.write_text(json.dumps({"env": {"REDWAKE_LLM": "from-file"}}), encoding="utf-8")
    # env wins -> the JSON value is not surfaced as an init kwarg.
    assert loader._read_json_overrides(path) == {}


# --------------------------------------------------------------------------- #
# _aliases_for
# --------------------------------------------------------------------------- #


def test_aliases_for_simple_alias() -> None:
    finfo = FieldInfo(alias="SIMPLE_ALIAS")
    assert loader._aliases_for(finfo) == ["SIMPLE_ALIAS"]


def test_aliases_for_alias_choices() -> None:
    finfo: FieldInfo = Field(  # type: ignore[assignment]
        default=None,
        validation_alias=AliasChoices("FIRST", "SECOND"),
    )
    assert loader._aliases_for(finfo) == ["FIRST", "SECOND"]


def test_aliases_for_string_validation_alias() -> None:
    finfo: FieldInfo = Field(default=None, validation_alias="STR_ALIAS")  # type: ignore[assignment]
    assert loader._aliases_for(finfo) == ["STR_ALIAS"]


def test_aliases_for_no_alias() -> None:
    assert loader._aliases_for(FieldInfo()) == []


# --------------------------------------------------------------------------- #
# apply_config_override + load_settings round-trip
# --------------------------------------------------------------------------- #


def test_apply_override_and_load_settings_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "cli-config.json"
    path.write_text(
        json.dumps({"env": {"REDWAKE_LLM": "round-trip-model", "PERPLEXITY_API_KEY": "pk"}}),
        encoding="utf-8",
    )

    loader.apply_config_override(path)
    settings = loader.load_settings()

    assert settings.llm.model == "round-trip-model"
    assert settings.integrations.perplexity_api_key == "pk"
    # Second call is memoized -> same object.
    assert loader.load_settings() is settings


def test_apply_config_override_invalidates_cache(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    first.write_text(json.dumps({"env": {"REDWAKE_LLM": "first-model"}}), encoding="utf-8")
    second = tmp_path / "second.json"
    second.write_text(json.dumps({"env": {"REDWAKE_LLM": "second-model"}}), encoding="utf-8")

    loader.apply_config_override(first)
    assert loader.load_settings().llm.model == "first-model"

    loader.apply_config_override(second)
    assert loader.load_settings().llm.model == "second-model"


# --------------------------------------------------------------------------- #
# persist_current
# --------------------------------------------------------------------------- #


def test_persist_current_writes_env_block(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDWAKE_LLM", "persisted-model")
    target = tmp_path / "sub" / "cli-config.json"
    loader.apply_config_override(target)

    loader.persist_current()

    assert target.exists()
    assert json.loads(target.read_text(encoding="utf-8")) == {
        "env": {"REDWAKE_LLM": "persisted-model"}
    }


def test_persist_current_sets_0600_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDWAKE_LLM", "persisted-model")
    target = tmp_path / "cli-config.json"
    loader.apply_config_override(target)

    loader.persist_current()

    assert target.stat().st_mode & 0o777 == 0o600


# --------------------------------------------------------------------------- #
# Regression: default config path + persist merge semantics
# --------------------------------------------------------------------------- #


def test_default_config_path_is_xdg_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """The default path must match the documented ~/.config/redwake location.

    Regression for a bug where _DEFAULT_PATH pointed at ~/.redwake, which was
    never documented and only ever held an empty {"env": {}} written by
    persist_current — the user's real config at ~/.config/redwake was silently
    ignored, so scans ran against the default model/endpoint and failed.
    """
    import re
    from pathlib import Path

    src = Path(loader.__file__).read_text(encoding="utf-8")
    match = re.search(
        r'_DEFAULT_PATH:\s*Path\s*=\s*Path\.home\(\)\s*/\s*"([^"]+)"\s*/\s*"([^"]+)"\s*/\s*"([^"]+)"',
        src,
    )
    assert match, "_DEFAULT_PATH must be defined as Path.home() / seg / seg / seg"
    assert (match.group(1), match.group(2), match.group(3)) == (
        ".config",
        "redwake",
        "cli-config.json",
    ), f"default path is {match.groups()}, expected ('.config','redwake','cli-config.json')"


def test_persist_current_preserves_file_only_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """persist_current must not erase keys that exist only in the file.

    Regression for a clobber bug: a user who keeps config in the file (no
    REDWAKE_* env vars exported) had persist_current overwrite the file with
    {"env": {}} on every run, destroying model/key/endpoint -> next scan fail.
    """
    target = tmp_path / "cli-config.json"
    target.write_text(
        json.dumps(
            {"env": {"REDWAKE_LLM": "file-only-model", "REDWAKE_BASE_URL": "http://file/v1"}}
        ),
        encoding="utf-8",
    )
    # No REDWAKE_* env set — config is file-only.
    monkeypatch.setattr(loader, "_cached", None)
    loader.apply_config_override(target)

    loader.persist_current()

    out = json.loads(target.read_text(encoding="utf-8"))
    assert out["env"]["REDWAKE_LLM"] == "file-only-model"
    assert out["env"]["REDWAKE_BASE_URL"] == "http://file/v1"


def test_persist_current_env_overrides_file_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Env-present keys still win over file keys on persist (merge, not blind keep)."""
    target = tmp_path / "cli-config.json"
    target.write_text(
        json.dumps({"env": {"REDWAKE_LLM": "old-model", "REDWAKE_BASE_URL": "http://file/v1"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("REDWAKE_LLM", "new-env-model")
    monkeypatch.setattr(loader, "_cached", None)
    loader.apply_config_override(target)

    loader.persist_current()

    out = json.loads(target.read_text(encoding="utf-8"))
    assert out["env"]["REDWAKE_LLM"] == "new-env-model"  # env won
    assert out["env"]["REDWAKE_BASE_URL"] == "http://file/v1"  # file-only survived
