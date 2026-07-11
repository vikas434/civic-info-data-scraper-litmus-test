"""Tests for domain models."""

import pytest
from pydantic import ValidationError

from app.models import (
    BenchmarkRecord,
    MatchResult,
    Role,
    RoleResult,
    StructuralAnomaly,
    ZipGroup,
    ZipResponse,
)


def make_role_result(
    role: str = "Governor",
    name: str = "Kathy Hochul",
    website: str = "https://www.ny.gov/governor",
    confidence: float = 0.95,
) -> RoleResult:
    return RoleResult(
        role=role,
        official_name=name,
        official_website=website,
        confidence=confidence,
        sources=["https://www.ny.gov"],
    )


def make_match_result(
    role: str = "Governor",
    name_match: bool = True,
    website_match: bool = True,
) -> MatchResult:
    return MatchResult(
        role=role,
        expected_name="Kathy Hochul",
        expected_website="https://www.ny.gov/governor",
        actual_name="Kathy Hochul" if name_match else "Wrong Name",
        actual_website="https://www.ny.gov/governor",
        name_match=name_match,
        website_match=website_match,
    )


def make_benchmark_record(match_results: list[MatchResult]) -> BenchmarkRecord:
    return BenchmarkRecord(
        zip_code="10019",
        model_id="google/gemini-2.5-pro",
        latency_ms=1500.0,
        input_tokens=500,
        output_tokens=200,
        estimated_cost_usd=0.0025,
        validation_errors=0,
        retry_count=0,
        has_web_search=True,
        timestamp="2025-01-01T00:00:00Z",
        match_results=match_results,
    )


# --- Role ---


def test_role_creation() -> None:
    role = Role(name="Governor", gov_level="State (New York)", branch="Executive")
    assert role.name == "Governor"
    assert role.gov_level == "State (New York)"
    assert role.branch == "Executive"


# --- ZipGroup ---


def test_zip_group_creation() -> None:
    role = Role(name="Governor", gov_level="State (New York)", branch="Executive")
    group = ZipGroup(zip_code="10019", roles=[role], row_indices=[2])
    assert group.zip_code == "10019"
    assert len(group.roles) == 1
    assert group.row_indices == [2]


# --- RoleResult ---


def test_role_result_valid_confidence() -> None:
    result = make_role_result(confidence=0.95)
    assert result.confidence == 0.95


def test_role_result_confidence_zero() -> None:
    result = make_role_result(confidence=0.0)
    assert result.confidence == 0.0


def test_role_result_confidence_one() -> None:
    result = make_role_result(confidence=1.0)
    assert result.confidence == 1.0


def test_role_result_confidence_above_one_raises() -> None:
    with pytest.raises(ValidationError):
        make_role_result(confidence=1.1)


def test_role_result_confidence_negative_raises() -> None:
    with pytest.raises(ValidationError):
        make_role_result(confidence=-0.1)


# --- ZipResponse ---


def test_zip_response_creation() -> None:
    response = ZipResponse(zip_code="10019", results=[make_role_result()])
    assert response.zip_code == "10019"
    assert len(response.results) == 1


def test_zip_response_multiple_results() -> None:
    results = [make_role_result("Governor"), make_role_result("Mayor", name="Eric Adams")]
    response = ZipResponse(zip_code="10019", results=results)
    assert len(response.results) == 2


# --- MatchResult ---


def test_match_result_is_match_when_both_match() -> None:
    match = make_match_result(name_match=True, website_match=True)
    assert match.is_match is True


def test_match_result_not_match_when_name_differs() -> None:
    match = make_match_result(name_match=False, website_match=True)
    assert match.is_match is False


def test_match_result_not_match_when_website_differs() -> None:
    match = make_match_result(name_match=True, website_match=False)
    assert match.is_match is False


def test_match_result_not_match_when_both_differ() -> None:
    match = make_match_result(name_match=False, website_match=False)
    assert match.is_match is False


# --- BenchmarkRecord.accuracy ---


def test_benchmark_record_accuracy_all_match() -> None:
    record = make_benchmark_record([
        make_match_result("Governor", name_match=True, website_match=True),
        make_match_result("Mayor", name_match=True, website_match=True),
    ])
    assert record.accuracy == 1.0


def test_benchmark_record_accuracy_half_match() -> None:
    record = make_benchmark_record([
        make_match_result("Governor", name_match=True, website_match=True),
        make_match_result("Mayor", name_match=False, website_match=True),
    ])
    assert record.accuracy == 0.5


def test_benchmark_record_accuracy_none_match() -> None:
    record = make_benchmark_record([
        make_match_result("Governor", name_match=False, website_match=False),
    ])
    assert record.accuracy == 0.0


def test_benchmark_record_accuracy_empty_results() -> None:
    record = make_benchmark_record([])
    assert record.accuracy == 0.0


# --- StructuralAnomaly ---


def test_structural_anomaly_creation() -> None:
    anomaly = StructuralAnomaly(
        zip_code="10019",
        actual_role_count=5,
        notes="Fewer roles than expected for an NYC ZIP",
    )
    assert anomaly.zip_code == "10019"
    assert anomaly.actual_role_count == 5
