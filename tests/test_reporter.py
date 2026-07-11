"""Tests for benchmark reporter."""

import csv
from pathlib import Path

import pytest

from app.config import ModelConfig, ModelPricing
from app.models import MatchResult, RunMetrics
from app.reporter import (
    append_to_csv,
    build_benchmark_record,
    write_benchmark_xlsx,
    write_summary_md,
)


@pytest.fixture()
def model() -> ModelConfig:
    return ModelConfig(
        id="google/gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        column_prefix="Gemini 2.5 Pro",
        has_web_search=True,
        pricing=ModelPricing(input_per_1k_tokens=0.00125, output_per_1k_tokens=0.010),
    )


@pytest.fixture()
def metrics() -> RunMetrics:
    return RunMetrics(
        latency_ms=1500.0,
        input_tokens=1000,
        output_tokens=500,
        retry_count=0,
        validation_errors=0,
    )


@pytest.fixture()
def match_results() -> list[MatchResult]:
    return [
        MatchResult(
            role="Governor",
            expected_name="Kathy Hochul",
            expected_website="https://www.ny.gov/governor",
            actual_name="Kathy Hochul",
            actual_website="https://www.ny.gov/governor",
            name_match=True,
            website_match=True,
        ),
        MatchResult(
            role="Mayor",
            expected_name="Eric Adams",
            expected_website="https://www.nyc.gov",
            actual_name="Wrong Person",
            actual_website="https://www.nyc.gov",
            name_match=False,
            website_match=True,
        ),
    ]


# --- build_benchmark_record ---


def test_build_record_zip_code(model: ModelConfig, metrics: RunMetrics) -> None:
    record = build_benchmark_record("10019", model, metrics, [])
    assert record.zip_code == "10019"


def test_build_record_model_id(model: ModelConfig, metrics: RunMetrics) -> None:
    record = build_benchmark_record("10019", model, metrics, [])
    assert record.model_id == "google/gemini-2.5-pro"


def test_build_record_has_web_search(model: ModelConfig, metrics: RunMetrics) -> None:
    record = build_benchmark_record("10019", model, metrics, [])
    assert record.has_web_search is True


def test_build_record_latency(model: ModelConfig, metrics: RunMetrics) -> None:
    record = build_benchmark_record("10019", model, metrics, [])
    assert record.latency_ms == 1500.0


def test_build_record_tokens(model: ModelConfig, metrics: RunMetrics) -> None:
    record = build_benchmark_record("10019", model, metrics, [])
    assert record.input_tokens == 1000
    assert record.output_tokens == 500


def test_build_record_cost_calculated(model: ModelConfig, metrics: RunMetrics) -> None:
    record = build_benchmark_record("10019", model, metrics, [])
    expected = model.estimate_cost(1000, 500)
    assert record.estimated_cost_usd == expected


def test_build_record_has_timestamp(model: ModelConfig, metrics: RunMetrics) -> None:
    record = build_benchmark_record("10019", model, metrics, [])
    assert record.timestamp  # non-empty ISO string


def test_build_record_match_results_stored(
    model: ModelConfig, metrics: RunMetrics, match_results: list[MatchResult]
) -> None:
    record = build_benchmark_record("10019", model, metrics, match_results)
    assert len(record.match_results) == 2


def test_build_record_accuracy(
    model: ModelConfig, metrics: RunMetrics, match_results: list[MatchResult]
) -> None:
    record = build_benchmark_record("10019", model, metrics, match_results)
    assert record.accuracy == 0.5  # 1 of 2 match


# --- append_to_csv ---


def test_append_creates_file(
    tmp_path: Path, model: ModelConfig, metrics: RunMetrics
) -> None:
    record = build_benchmark_record("10019", model, metrics, [])
    path = tmp_path / "benchmark.csv"
    append_to_csv([record], path)
    assert path.exists()


def test_append_writes_header(
    tmp_path: Path, model: ModelConfig, metrics: RunMetrics
) -> None:
    record = build_benchmark_record("10019", model, metrics, [])
    path = tmp_path / "benchmark.csv"
    append_to_csv([record], path)
    with open(path) as f:
        reader = csv.DictReader(f)
        assert "zip_code" in (reader.fieldnames or [])
        assert "model_id" in (reader.fieldnames or [])
        assert "accuracy_pct" in (reader.fieldnames or [])


def test_append_writes_data_row(
    tmp_path: Path, model: ModelConfig, metrics: RunMetrics
) -> None:
    record = build_benchmark_record("10019", model, metrics, [])
    path = tmp_path / "benchmark.csv"
    append_to_csv([record], path)
    with open(path) as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["zip_code"] == "10019"


def test_append_does_not_duplicate_header(
    tmp_path: Path, model: ModelConfig, metrics: RunMetrics
) -> None:
    path = tmp_path / "benchmark.csv"
    r1 = build_benchmark_record("10019", model, metrics, [])
    r2 = build_benchmark_record("10012", model, metrics, [])
    append_to_csv([r1], path)
    append_to_csv([r2], path)
    with open(path) as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2


def test_append_multiple_records(
    tmp_path: Path, model: ModelConfig, metrics: RunMetrics
) -> None:
    records = [
        build_benchmark_record("10019", model, metrics, []),
        build_benchmark_record("10012", model, metrics, []),
    ]
    path = tmp_path / "benchmark.csv"
    append_to_csv(records, path)
    with open(path) as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2


# --- write_benchmark_xlsx ---


def test_xlsx_creates_file(
    tmp_path: Path, model: ModelConfig, metrics: RunMetrics
) -> None:
    csv_path = tmp_path / "benchmark.csv"
    xlsx_path = tmp_path / "benchmark.xlsx"
    record = build_benchmark_record("10019", model, metrics, [])
    append_to_csv([record], csv_path)
    write_benchmark_xlsx(csv_path, xlsx_path)
    assert xlsx_path.exists()


def test_xlsx_contains_data(
    tmp_path: Path, model: ModelConfig, metrics: RunMetrics
) -> None:
    import openpyxl

    csv_path = tmp_path / "benchmark.csv"
    xlsx_path = tmp_path / "benchmark.xlsx"
    record = build_benchmark_record("10019", model, metrics, [])
    append_to_csv([record], csv_path)
    write_benchmark_xlsx(csv_path, xlsx_path)

    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active
    assert ws.max_row == 2  # header + 1 data row


# --- write_summary_md ---


def test_summary_md_creates_file(
    tmp_path: Path, model: ModelConfig, metrics: RunMetrics
) -> None:
    csv_path = tmp_path / "benchmark.csv"
    md_path = tmp_path / "summary.md"
    record = build_benchmark_record("10019", model, metrics, [])
    append_to_csv([record], csv_path)
    write_summary_md(csv_path, md_path)
    assert md_path.exists()


def test_summary_md_contains_model_id(
    tmp_path: Path, model: ModelConfig, metrics: RunMetrics
) -> None:
    csv_path = tmp_path / "benchmark.csv"
    md_path = tmp_path / "summary.md"
    record = build_benchmark_record("10019", model, metrics, [])
    append_to_csv([record], csv_path)
    write_summary_md(csv_path, md_path)
    content = md_path.read_text()
    assert "google/gemini-2.5-pro" in content


def test_summary_md_shows_multiple_models(
    tmp_path: Path, metrics: RunMetrics
) -> None:
    model_a = ModelConfig(
        id="google/gemini-2.5-pro", display_name="Gemini", column_prefix="Gemini",
        has_web_search=True,
        pricing=ModelPricing(input_per_1k_tokens=0.00125, output_per_1k_tokens=0.010),
    )
    model_b = ModelConfig(
        id="anthropic/claude-sonnet-4", display_name="Claude", column_prefix="Claude",
        has_web_search=False,
        pricing=ModelPricing(input_per_1k_tokens=0.003, output_per_1k_tokens=0.015),
    )
    csv_path = tmp_path / "benchmark.csv"
    md_path = tmp_path / "summary.md"
    append_to_csv([build_benchmark_record("10019", model_a, metrics, [])], csv_path)
    append_to_csv([build_benchmark_record("10019", model_b, metrics, [])], csv_path)
    write_summary_md(csv_path, md_path)
    content = md_path.read_text()
    assert "google/gemini-2.5-pro" in content
    assert "anthropic/claude-sonnet-4" in content


def test_summary_md_shows_accuracy(
    tmp_path: Path, model: ModelConfig, metrics: RunMetrics,
    match_results: list[MatchResult],
) -> None:
    csv_path = tmp_path / "benchmark.csv"
    md_path = tmp_path / "summary.md"
    record = build_benchmark_record("10019", model, metrics, match_results)
    append_to_csv([record], csv_path)
    write_summary_md(csv_path, md_path)
    content = md_path.read_text()
    assert "50.0%" in content
