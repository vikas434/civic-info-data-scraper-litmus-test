"""Configuration loader for the civic info benchmark system."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


class ModelPricing(BaseModel):
    """Per-token pricing for a model in USD."""

    input_per_1k_tokens: float
    output_per_1k_tokens: float


class ModelConfig(BaseModel):
    """Configuration and pricing for a single LLM."""

    id: str  # OpenRouter model ID, e.g. "google/gemini-2.5-pro"
    display_name: str
    column_prefix: str  # prefix used to find this model's columns in the workbook
    has_web_search: bool
    pricing: ModelPricing

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate the USD cost for a request given token counts."""
        input_cost = (input_tokens / 1000) * self.pricing.input_per_1k_tokens
        output_cost = (output_tokens / 1000) * self.pricing.output_per_1k_tokens
        return round(input_cost + output_cost, 6)


class Settings(BaseModel):
    """Full application settings combining secrets and config file values."""

    openrouter_api_key: str
    active_model: str
    max_retries: int
    timeout_seconds: int
    max_workers: int
    input_dir: Path
    output_dir: Path
    reports_dir: Path
    prompt_file: Path
    models: list[ModelConfig]

    def get_model_config(self, model_id: str) -> ModelConfig:
        """Return the ModelConfig for the given OpenRouter model ID.

        Raises:
            ValueError: If the model ID is not found in config.
        """
        for model in self.models:
            if model.id == model_id:
                return model
        available = [m.id for m in self.models]
        raise ValueError(f"Model {model_id!r} not found. Available: {available}")


def load_settings(
    config_path: Path = Path("config/settings.toml"),
    env_file: Path = Path(".env"),
) -> Settings:
    """Load settings from a TOML config file and a .env file.

    Args:
        config_path: Path to the TOML settings file.
        env_file: Path to the .env file containing secrets.

    Returns:
        A fully validated Settings instance.

    Raises:
        RuntimeError: If OPENROUTER_API_KEY is missing.
        FileNotFoundError: If config_path does not exist.
    """
    load_dotenv(env_file)

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Add it to your .env file."
        )

    return Settings(openrouter_api_key=api_key, **raw)
