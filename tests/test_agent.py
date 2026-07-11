"""Tests for the PydanticAI agent module."""

from pathlib import Path

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.agent import build_user_message, load_prompt, run_zip
from app.models import Role, ZipGroup, ZipResponse

# --- load_prompt ---


def test_load_prompt_returns_content(tmp_path: Path) -> None:
    f = tmp_path / "prompt.md"
    f.write_text("# System Prompt\n\nDo stuff.")
    assert load_prompt(f) == "# System Prompt\n\nDo stuff."


def test_load_prompt_strips_whitespace(tmp_path: Path) -> None:
    f = tmp_path / "prompt.md"
    f.write_text("\n\n# Prompt\n\n")
    assert load_prompt(f) == "# Prompt"


def test_load_prompt_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt(tmp_path / "nonexistent.md")


# --- build_user_message ---


@pytest.fixture()
def single_role_group() -> ZipGroup:
    return ZipGroup(
        zip_code="10019",
        roles=[Role(name="Governor", gov_level="State (New York)", branch="Executive")],
        row_indices=[2],
    )


@pytest.fixture()
def multi_role_group() -> ZipGroup:
    return ZipGroup(
        zip_code="10019",
        roles=[
            Role(name="Governor", gov_level="State (New York)", branch="Executive"),
            Role(name="Mayor of NYC", gov_level="Local (NYC)", branch="Executive"),
            Role(name="US Senator", gov_level="Federal", branch="Legislature"),
        ],
        row_indices=[2, 3, 4],
    )


def test_user_message_contains_zip(single_role_group: ZipGroup) -> None:
    msg = build_user_message(single_role_group)
    assert "10019" in msg


def test_user_message_contains_role_name(single_role_group: ZipGroup) -> None:
    msg = build_user_message(single_role_group)
    assert "Governor" in msg


def test_user_message_contains_gov_level(single_role_group: ZipGroup) -> None:
    msg = build_user_message(single_role_group)
    assert "State (New York)" in msg


def test_user_message_contains_branch(single_role_group: ZipGroup) -> None:
    msg = build_user_message(single_role_group)
    assert "Executive" in msg


def test_user_message_contains_all_roles(multi_role_group: ZipGroup) -> None:
    msg = build_user_message(multi_role_group)
    assert "Governor" in msg
    assert "Mayor of NYC" in msg
    assert "US Senator" in msg


def test_user_message_is_numbered(multi_role_group: ZipGroup) -> None:
    msg = build_user_message(multi_role_group)
    assert "1." in msg
    assert "2." in msg
    assert "3." in msg


# --- run_zip with TestModel ---


def _make_test_response(zip_code: str, role_name: str) -> dict:
    return {
        "zip_code": zip_code,
        "results": [{
            "role": role_name,
            "official_name": "Kathy Hochul",
            "official_website": "https://www.ny.gov/governor",
            "confidence": 0.95,
            "sources": ["https://www.ny.gov"],
        }],
    }


@pytest.mark.asyncio
async def test_run_zip_returns_zip_response(single_role_group: ZipGroup) -> None:
    test_model = TestModel(
        custom_output_args=_make_test_response("10019", "Governor"),
    )
    agent = Agent(test_model, output_type=ZipResponse, system_prompt="test")

    response, metrics = await run_zip(agent, single_role_group, timeout_seconds=30)

    assert isinstance(response, ZipResponse)
    assert response.zip_code == "10019"
    assert len(response.results) == 1
    assert response.results[0].official_name == "Kathy Hochul"


@pytest.mark.asyncio
async def test_run_zip_returns_metrics(single_role_group: ZipGroup) -> None:
    test_model = TestModel(
        custom_output_args=_make_test_response("10019", "Governor"),
    )
    agent = Agent(test_model, output_type=ZipResponse, system_prompt="test")

    _, metrics = await run_zip(agent, single_role_group, timeout_seconds=30)

    assert metrics.latency_ms >= 0
    assert metrics.input_tokens >= 0
    assert metrics.output_tokens >= 0
    assert metrics.retry_count >= 0


@pytest.mark.asyncio
async def test_run_zip_multiple_roles(multi_role_group: ZipGroup) -> None:
    test_model = TestModel(
        custom_output_args={
            "zip_code": "10019",
            "results": [
                {"role": "Governor", "official_name": "Kathy Hochul",
                 "official_website": "https://www.ny.gov/governor",
                 "confidence": 0.95, "sources": []},
                {"role": "Mayor of NYC", "official_name": "Eric Adams",
                 "official_website": "https://www.nyc.gov",
                 "confidence": 0.90, "sources": []},
                {"role": "US Senator", "official_name": "Chuck Schumer",
                 "official_website": "https://www.schumer.senate.gov",
                 "confidence": 0.99, "sources": []},
            ],
        }
    )
    agent = Agent(test_model, output_type=ZipResponse, system_prompt="test")

    response, _ = await run_zip(agent, multi_role_group, timeout_seconds=30)

    assert len(response.results) == 3
