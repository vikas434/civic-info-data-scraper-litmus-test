"""Tests for retry orchestration in runner.py."""

from unittest.mock import AsyncMock, patch

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.models import Role, RoleResult, RunMetrics, ZipGroup, ZipResponse
from app.runner import run_zip_with_retry


@pytest.fixture()
def zip_group() -> ZipGroup:
    return ZipGroup(
        zip_code="10019",
        roles=[Role(name="Governor", gov_level="State", branch="Executive")],
        row_indices=[2],
    )


@pytest.fixture()
def valid_response() -> ZipResponse:
    return ZipResponse(
        zip_code="10019",
        results=[RoleResult(
            role="Governor",
            official_name="Kathy Hochul",
            official_website="https://www.ny.gov/governor",
            confidence=0.95,
            sources=["https://www.ny.gov"],
        )],
    )


@pytest.fixture()
def invalid_response() -> ZipResponse:
    """Response where Governor role is missing."""
    return ZipResponse(zip_code="10019", results=[])


@pytest.fixture()
def base_metrics() -> RunMetrics:
    return RunMetrics(
        latency_ms=500.0,
        input_tokens=100,
        output_tokens=50,
        retry_count=0,
        validation_errors=0,
    )


@pytest.fixture()
def agent() -> Agent:
    return Agent(TestModel(), output_type=ZipResponse, system_prompt="test")


# --- success on first attempt ---


@pytest.mark.asyncio
async def test_succeeds_first_attempt(
    agent: Agent, zip_group: ZipGroup, valid_response: ZipResponse, base_metrics: RunMetrics
) -> None:
    with patch("app.runner.run_zip", new_callable=AsyncMock) as mock:
        mock.return_value = (valid_response, base_metrics)
        response, metrics = await run_zip_with_retry(
            agent, zip_group, timeout_seconds=30, max_retries=2, retry_delay_seconds=0.0
        )

    assert mock.call_count == 1
    assert metrics.retry_count == 0
    assert metrics.validation_errors == 0
    assert response.zip_code == "10019"


# --- retry on validation failure ---


@pytest.mark.asyncio
async def test_retries_once_on_validation_error(
    agent: Agent, zip_group: ZipGroup,
    valid_response: ZipResponse, invalid_response: ZipResponse, base_metrics: RunMetrics,
) -> None:
    with patch("app.runner.run_zip", new_callable=AsyncMock) as mock:
        mock.side_effect = [
            (invalid_response, base_metrics),
            (valid_response, base_metrics),
        ]
        response, metrics = await run_zip_with_retry(
            agent, zip_group, timeout_seconds=30, max_retries=2, retry_delay_seconds=0.0
        )

    assert mock.call_count == 2
    assert metrics.retry_count == 1
    assert metrics.validation_errors > 0
    assert response.zip_code == "10019"
    assert len(response.results) == 1


@pytest.mark.asyncio
async def test_token_counts_accumulate_across_retries(
    agent: Agent, zip_group: ZipGroup,
    valid_response: ZipResponse, invalid_response: ZipResponse, base_metrics: RunMetrics,
) -> None:
    with patch("app.runner.run_zip", new_callable=AsyncMock) as mock:
        mock.side_effect = [
            (invalid_response, base_metrics),   # 100 input, 50 output
            (valid_response, base_metrics),     # 100 input, 50 output
        ]
        _, metrics = await run_zip_with_retry(
            agent, zip_group, timeout_seconds=30, max_retries=2, retry_delay_seconds=0.0
        )

    assert metrics.input_tokens == 200
    assert metrics.output_tokens == 100


# --- all retries exhausted on validation ---


@pytest.mark.asyncio
async def test_returns_best_effort_when_all_retries_fail_validation(
    agent: Agent, zip_group: ZipGroup, invalid_response: ZipResponse, base_metrics: RunMetrics,
) -> None:
    with patch("app.runner.run_zip", new_callable=AsyncMock) as mock:
        mock.return_value = (invalid_response, base_metrics)
        response, metrics = await run_zip_with_retry(
            agent, zip_group, timeout_seconds=30, max_retries=1, retry_delay_seconds=0.0
        )

    assert mock.call_count == 2  # initial + 1 retry
    assert metrics.retry_count == 1
    assert metrics.validation_errors > 0
    assert response is invalid_response  # best effort: last response returned


# --- retry on transient exception ---


@pytest.mark.asyncio
async def test_retries_on_exception(
    agent: Agent, zip_group: ZipGroup, valid_response: ZipResponse, base_metrics: RunMetrics,
) -> None:
    with patch("app.runner.run_zip", new_callable=AsyncMock) as mock:
        mock.side_effect = [
            RuntimeError("connection error"),
            (valid_response, base_metrics),
        ]
        response, metrics = await run_zip_with_retry(
            agent, zip_group, timeout_seconds=30, max_retries=2, retry_delay_seconds=0.0
        )

    assert mock.call_count == 2
    assert metrics.retry_count == 1
    assert response.zip_code == "10019"


# --- all attempts raise exception ---


@pytest.mark.asyncio
async def test_raises_after_all_retries_fail_with_exception(
    agent: Agent, zip_group: ZipGroup,
) -> None:
    with patch("app.runner.run_zip", new_callable=AsyncMock) as mock:
        mock.side_effect = RuntimeError("network down")
        with pytest.raises(RuntimeError, match="network down"):
            await run_zip_with_retry(
                agent, zip_group, timeout_seconds=30, max_retries=1, retry_delay_seconds=0.0
            )

    assert mock.call_count == 2
