"""PydanticAI agent for civic representative lookup via OpenRouter."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

import structlog
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import ModelConfig
from app.models import RunMetrics, ZipGroup, ZipResponse

log = structlog.get_logger()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def load_prompt(path: Path) -> str:
    """Read a markdown prompt file and return its content.

    Args:
        path: Path to the markdown prompt file.

    Returns:
        The file content stripped of leading and trailing whitespace.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    return path.read_text(encoding="utf-8").strip()


def build_user_message(zip_group: ZipGroup) -> str:
    """Build the LLM user message for a ZIP group.

    Args:
        zip_group: The ZIP group containing the roles to look up.

    Returns:
        A formatted string listing the ZIP code and all roles to research.
    """
    lines: list[str] = [
        f"ZIP Code: {zip_group.zip_code}",
        "",
        "Find the current official holder and their official website for each role below.",
        "Use web search for every role. Never answer from memory.",
        "",
        "Roles to look up:",
        "",
    ]
    for i, role in enumerate(zip_group.roles, 1):
        lines.append(f"{i}. {role.name} ({role.gov_level}, {role.branch})")
    return "\n".join(lines)


def create_agent(
    model_config: ModelConfig,
    api_key: str,
    system_prompt: str,
    max_retries: int,
) -> Agent[Any, ZipResponse]:
    """Create a PydanticAI agent configured for OpenRouter.

    Args:
        model_config: The model to use, including its OpenRouter ID.
        api_key: OpenRouter API key.
        system_prompt: System prompt text (loaded from the prompt file).
        max_retries: Number of times to retry on validation failure.

    Returns:
        A configured PydanticAI Agent that returns ZipResponse.
    """
    provider = OpenAIProvider(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
    )
    model = OpenAIChatModel(model_config.id, provider=provider)
    return Agent(
        model=model,
        output_type=ZipResponse,
        system_prompt=system_prompt,
        retries=max_retries,
    )


async def run_zip(
    agent: Agent[Any, ZipResponse],
    zip_group: ZipGroup,
    timeout_seconds: int,
) -> tuple[ZipResponse, RunMetrics]:
    """Run the agent for one ZIP group and return the structured response with metrics.

    Args:
        agent: A configured PydanticAI agent.
        zip_group: The ZIP group to research.
        timeout_seconds: Maximum seconds to wait before raising TimeoutError.

    Returns:
        A tuple of (ZipResponse, RunMetrics).

    Raises:
        asyncio.TimeoutError: If the call exceeds timeout_seconds.
    """
    user_message = build_user_message(zip_group)
    log.info("agent.run_start", zip=zip_group.zip_code, role_count=len(zip_group.roles))

    start = time.monotonic()
    result = await asyncio.wait_for(agent.run(user_message), timeout=timeout_seconds)
    latency_ms = round((time.monotonic() - start) * 1000, 2)

    usage = result.usage
    metrics = RunMetrics(
        latency_ms=latency_ms,
        input_tokens=usage.input_tokens or 0,
        output_tokens=usage.output_tokens or 0,
        retry_count=max(0, (usage.requests or 1) - 1),
        validation_errors=0,
    )

    log.info(
        "agent.run_complete",
        zip=zip_group.zip_code,
        latency_ms=metrics.latency_ms,
        input_tokens=metrics.input_tokens,
        output_tokens=metrics.output_tokens,
        retries=metrics.retry_count,
    )

    return result.output, metrics
