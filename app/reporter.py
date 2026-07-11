"""Benchmark report generation — CSV, XLSX, and Markdown summary."""

from __future__ import annotations

import csv
import datetime
from pathlib import Path

import pandas as pd
import structlog

from app.config import ModelConfig
from app.models import BenchmarkRecord, MatchResult, RunMetrics

log = structlog.get_logger()

_CSV_FIELDS = [
    "zip_code",
    "model_id",
    "has_web_search",
    "timestamp",
    "latency_ms",
    "input_tokens",
    "output_tokens",
    "estimated_cost_usd",
    "validation_errors",
    "retry_count",
    "total_roles",
    "matched_roles",
    "accuracy_pct",
]


def build_benchmark_record(
    zip_code: str,
    model_config: ModelConfig,
    metrics: RunMetrics,
    match_results: list[MatchResult],
) -> BenchmarkRecord:
    """Build a BenchmarkRecord from the results of one ZIP group LLM run.

    Args:
        zip_code: The ZIP code that was processed.
        model_config: The model that was used, for pricing and metadata.
        metrics: Token usage and timing from the run.
        match_results: Per-role comparison against MyCivX ground truth.

    Returns:
        A fully populated BenchmarkRecord with estimated cost.
    """
    return BenchmarkRecord(
        zip_code=zip_code,
        model_id=model_config.id,
        latency_ms=metrics.latency_ms,
        input_tokens=metrics.input_tokens,
        output_tokens=metrics.output_tokens,
        estimated_cost_usd=model_config.estimate_cost(metrics.input_tokens, metrics.output_tokens),
        validation_errors=metrics.validation_errors,
        retry_count=metrics.retry_count,
        has_web_search=model_config.has_web_search,
        timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
        match_results=match_results,
    )


def _record_to_row(record: BenchmarkRecord) -> dict[str, object]:
    """Flatten a BenchmarkRecord into a CSV-safe dict."""
    matched = sum(1 for m in record.match_results if m.is_match)
    total = len(record.match_results)
    return {
        "zip_code": record.zip_code,
        "model_id": record.model_id,
        "has_web_search": record.has_web_search,
        "timestamp": record.timestamp,
        "latency_ms": record.latency_ms,
        "input_tokens": record.input_tokens,
        "output_tokens": record.output_tokens,
        "estimated_cost_usd": record.estimated_cost_usd,
        "validation_errors": record.validation_errors,
        "retry_count": record.retry_count,
        "total_roles": total,
        "matched_roles": matched,
        "accuracy_pct": round(record.accuracy * 100, 1),
    }


def append_to_csv(records: list[BenchmarkRecord], path: Path) -> None:
    """Append benchmark records to a CSV file, creating it if it does not exist.

    The header is written only on file creation so successive runs accumulate
    without duplicating the header row.

    Args:
        records: Records to append.
        path: Path to the CSV file.
    """
    if not records:
        return

    rows = [_record_to_row(r) for r in records]
    file_exists = path.exists()

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

    log.info("reporter.csv_appended", path=str(path), rows=len(rows))


def write_benchmark_xlsx(csv_path: Path, output_path: Path) -> None:
    """Write a formatted Excel report from the accumulated benchmark CSV.

    Args:
        csv_path: Path to the benchmark CSV (must exist).
        output_path: Destination .xlsx path.
    """
    df = pd.read_csv(csv_path)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Benchmark")
    log.info("reporter.xlsx_written", path=str(output_path), rows=len(df))


def write_summary_md(csv_path: Path, output_path: Path) -> None:
    """Generate a Markdown scorecard from all benchmark records in the CSV.

    Groups by model_id and computes accuracy %, average latency, and total cost.

    Args:
        csv_path: Path to the benchmark CSV (must exist).
        output_path: Destination .md path.
    """
    df = pd.read_csv(csv_path)

    summary = (
        df.groupby("model_id")
        .agg(
            zips_processed=("zip_code", "count"),
            avg_accuracy_pct=("accuracy_pct", "mean"),
            avg_latency_ms=("latency_ms", "mean"),
            total_cost_usd=("estimated_cost_usd", "sum"),
            total_input_tokens=("input_tokens", "sum"),
            total_output_tokens=("output_tokens", "sum"),
            total_retries=("retry_count", "sum"),
            total_validation_errors=("validation_errors", "sum"),
            web_search=("has_web_search", "first"),
        )
        .reset_index()
        .sort_values("avg_accuracy_pct", ascending=False)
    )

    generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = [
        "# Civic Info Benchmark — Summary",
        "",
        f"Generated: {generated}",
        f"Total ZIP runs: {len(df)}",
        "",
        "## Scorecard",
        "",
        "| Model | ZIPs | Accuracy | Avg Latency | Total Cost | Web Search |",
        "| --- | ---: | ---: | ---: | ---: | :---: |",
    ]

    for _, row in summary.iterrows():
        web = "Yes" if row["web_search"] else "No"
        lines.append(
            f"| {row['model_id']} "
            f"| {int(row['zips_processed'])} "
            f"| {row['avg_accuracy_pct']:.1f}% "
            f"| {row['avg_latency_ms']:.0f}ms "
            f"| ${row['total_cost_usd']:.4f} "
            f"| {web} |"
        )

    lines += [
        "",
        "## Token Usage",
        "",
        "| Model | Input Tokens | Output Tokens | Retries | Validation Errors |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for _, row in summary.iterrows():
        lines.append(
            f"| {row['model_id']} "
            f"| {int(row['total_input_tokens']):,} "
            f"| {int(row['total_output_tokens']):,} "
            f"| {int(row['total_retries'])} "
            f"| {int(row['total_validation_errors'])} |"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("reporter.summary_written", path=str(output_path), models=len(summary))
