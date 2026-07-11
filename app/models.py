"""Domain models for the civic info benchmark system."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

Confidence = Annotated[float, Field(ge=0.0, le=1.0)]


class Role(BaseModel):
    """A single government role to be looked up for a ZIP code."""

    name: str
    gov_level: str
    branch: str
    mycivx_name: str | None = None      # pre-filled ground truth from workbook
    mycivx_website: str | None = None   # pre-filled ground truth from workbook


class ZipGroup(BaseModel):
    """All roles for a single ZIP code with their workbook row positions."""

    zip_code: str
    roles: list[Role]
    row_indices: list[int]  # 1-based openpyxl row numbers, one per role


class RoleResult(BaseModel):
    """LLM-produced result for a single government role."""

    role: str
    official_name: str
    official_website: str
    confidence: Confidence
    sources: list[str]


class ZipResponse(BaseModel):
    """Structured LLM response covering all roles for a single ZIP code."""

    zip_code: str
    results: list[RoleResult]


class MatchResult(BaseModel):
    """Comparison of one LLM role result against MyCivX ground truth."""

    role: str
    expected_name: str
    expected_website: str
    actual_name: str
    actual_website: str
    name_match: bool
    website_match: bool

    @property
    def is_match(self) -> bool:
        """True only when both name and website match."""
        return self.name_match and self.website_match


class BenchmarkRecord(BaseModel):
    """All metrics captured for a single ZIP + model LLM call."""

    zip_code: str
    model_id: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    validation_errors: int
    retry_count: int
    has_web_search: bool
    timestamp: str  # ISO 8601
    match_results: list[MatchResult]

    @property
    def accuracy(self) -> float:
        """Fraction of roles where is_match is True. Returns 0.0 for empty results."""
        if not self.match_results:
            return 0.0
        return sum(1 for r in self.match_results if r.is_match) / len(self.match_results)


class StructuralAnomaly(BaseModel):
    """Records a ZIP group whose role list is unexpected, for human review."""

    zip_code: str
    actual_role_count: int
    notes: str
