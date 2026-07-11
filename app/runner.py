"""Retry orchestration for ZIP group LLM runs."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
from pydantic_ai import Agent

from app.agent import run_zip
from app.models import RunMetrics, ZipGroup, ZipResponse
from app.validator import validate_response

log = structlog.get_logger()


async def run_zip_with_retry(
    agent: Agent[Any, ZipResponse],
    zip_group: ZipGroup,
    timeout_seconds: int,
    max_retries: int,
    retry_delay_seconds: float = 1.0,
) -> tuple[ZipResponse, RunMetrics]:
    """Run the agent for one ZIP group, retrying on validation errors or transient failures.

    On validation failure the same prompt is retried — the failure count and retry
    count are recorded in the returned RunMetrics. If all attempts are exhausted by
    validation errors, the last response is returned as best-effort so the pipeline
    can continue. If all attempts raise exceptions, the last exception is re-raised.

    Token counts accumulate across all attempts so cost is correctly captured.

    Args:
        agent: A configured PydanticAI agent.
        zip_group: The ZIP group to research.
        timeout_seconds: Per-attempt timeout.
        max_retries: Maximum number of extra attempts beyond the first.
        retry_delay_seconds: Seconds to wait between attempts (0 in tests).

    Returns:
        A tuple of (ZipResponse, RunMetrics).

    Raises:
        Exception: Re-raises the last exception if every attempt raised.
    """
    last_response: ZipResponse | None = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_validation_errors: int = 0
    retry_count: int = 0
    last_latency_ms: float = 0.0

    for attempt in range(max_retries + 1):
        try:
            response, base_metrics = await run_zip(agent, zip_group, timeout_seconds)

            total_input_tokens += base_metrics.input_tokens
            total_output_tokens += base_metrics.output_tokens
            last_latency_ms = base_metrics.latency_ms
            last_response = response

            errors = validate_response(response, zip_group)

            if not errors:
                log.info(
                    "runner.zip_succeeded",
                    zip=zip_group.zip_code,
                    attempt=attempt,
                    retry_count=retry_count,
                )
                return response, RunMetrics(
                    latency_ms=last_latency_ms,
                    input_tokens=total_input_tokens,
                    output_tokens=total_output_tokens,
                    retry_count=retry_count,
                    validation_errors=total_validation_errors,
                )

            total_validation_errors += len(errors)

            if attempt < max_retries:
                retry_count += 1
                log.warning(
                    "runner.validation_failed_retrying",
                    zip=zip_group.zip_code,
                    errors=errors,
                    attempt=attempt,
                    retry_count=retry_count,
                )
                if retry_delay_seconds > 0:
                    await asyncio.sleep(retry_delay_seconds)
            else:
                log.error(
                    "runner.validation_failed_all_retries",
                    zip=zip_group.zip_code,
                    errors=errors,
                    total_validation_errors=total_validation_errors,
                )

        except Exception as exc:
            if attempt < max_retries:
                retry_count += 1
                delay = retry_delay_seconds * (2 ** attempt)
                log.warning(
                    "runner.exception_retrying",
                    zip=zip_group.zip_code,
                    error=str(exc),
                    attempt=attempt,
                    retry_count=retry_count,
                    delay=delay,
                )
                if delay > 0:
                    await asyncio.sleep(delay)
            else:
                log.error(
                    "runner.exception_all_retries_failed",
                    zip=zip_group.zip_code,
                    error=str(exc),
                )
                raise

    # All attempts exhausted by validation errors — return best-effort last response.
    if last_response is None:
        raise RuntimeError(f"No response captured for ZIP {zip_group.zip_code}")
    return last_response, RunMetrics(
        latency_ms=last_latency_ms,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
        retry_count=retry_count,
        validation_errors=total_validation_errors,
    )
