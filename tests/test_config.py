"""Tests for configuration loader."""

from pathlib import Path

import pytest

from app.config import load_settings

SAMPLE_TOML = """\
active_model = "google/gemini-2.5-pro"
max_retries = 3
timeout_seconds = 120
max_workers = 1
input_dir = "input"
output_dir = "output"
reports_dir = "reports"
prompt_file = "config/prompts/civic_lookup.md"

[[models]]
id = "google/gemini-2.5-pro"
display_name = "Gemini 2.5 Pro"
column_prefix = "Gemini 2.5 Pro"
has_web_search = true
[models.pricing]
input_per_1k_tokens = 0.00125
output_per_1k_tokens = 0.010

[[models]]
id = "anthropic/claude-sonnet-4"
display_name = "Claude Sonnet 4"
column_prefix = "Claude Sonnet 4"
has_web_search = false
[models.pricing]
input_per_1k_tokens = 0.003
output_per_1k_tokens = 0.015
"""


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    f = tmp_path / "settings.toml"
    f.write_text(SAMPLE_TOML)
    return f


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("OPENROUTER_API_KEY=test-key-123\n")
    return f


def test_load_settings_basic(config_file: Path, env_file: Path) -> None:
    settings = load_settings(config_path=config_file, env_file=env_file)
    assert settings.openrouter_api_key == "test-key-123"
    assert settings.active_model == "google/gemini-2.5-pro"
    assert settings.max_retries == 3
    assert settings.max_workers == 1
    assert len(settings.models) == 2


def test_settings_paths_are_path_objects(config_file: Path, env_file: Path) -> None:
    settings = load_settings(config_path=config_file, env_file=env_file)
    assert isinstance(settings.input_dir, Path)
    assert isinstance(settings.output_dir, Path)
    assert isinstance(settings.reports_dir, Path)
    assert isinstance(settings.prompt_file, Path)


def test_get_model_config_found(config_file: Path, env_file: Path) -> None:
    settings = load_settings(config_path=config_file, env_file=env_file)
    model = settings.get_model_config("google/gemini-2.5-pro")
    assert model.display_name == "Gemini 2.5 Pro"
    assert model.has_web_search is True


def test_get_model_config_not_found(config_file: Path, env_file: Path) -> None:
    settings = load_settings(config_path=config_file, env_file=env_file)
    with pytest.raises(ValueError, match="not found"):
        settings.get_model_config("nonexistent/model")


def test_model_without_web_search(config_file: Path, env_file: Path) -> None:
    settings = load_settings(config_path=config_file, env_file=env_file)
    model = settings.get_model_config("anthropic/claude-sonnet-4")
    assert model.has_web_search is False


def test_model_estimate_cost(config_file: Path, env_file: Path) -> None:
    settings = load_settings(config_path=config_file, env_file=env_file)
    model = settings.get_model_config("google/gemini-2.5-pro")
    cost = model.estimate_cost(input_tokens=1000, output_tokens=500)
    expected = (1000 / 1000 * 0.00125) + (500 / 1000 * 0.010)
    assert abs(cost - expected) < 1e-9


def test_estimate_cost_zero_tokens(config_file: Path, env_file: Path) -> None:
    settings = load_settings(config_path=config_file, env_file=env_file)
    model = settings.get_model_config("google/gemini-2.5-pro")
    assert model.estimate_cost(input_tokens=0, output_tokens=0) == 0.0


def test_missing_api_key_raises(
    config_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty_env = tmp_path / ".env"
    empty_env.write_text("")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        load_settings(config_path=config_file, env_file=empty_env)
