# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Domain contracts for protein complex activity scoring."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.interpretation.complex_enrichment import ComplexMemberKind
from bijux_proteomics.quantification.contracts.input_models import (
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
)
from bijux_proteomics_foundation import JsonModel

ComplexActivityConfidenceStatus = ConfidenceTier


class ComplexSampleScoreEntry(JsonModel):
    """One sample-level activity score for one complex."""

    model_config = ConfigDict(extra="forbid")

    complex_id: str = Field(..., min_length=1)
    complex_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    batch: str | None = None
    activity_score: float | None = None
    total_member_count: int = Field(..., ge=0)
    observed_member_count: int = Field(..., ge=0)
    missing_member_count: int = Field(..., ge=0)
    observed_fraction: float = Field(..., ge=0.0, le=1.0)
    minimum_observed_member_count: int = Field(..., ge=1)
    confidence_status: ComplexActivityConfidenceStatus
    confidence_reason: str | None = None
    observed_member_ids: tuple[str, ...] = Field(default_factory=tuple)
    missing_member_ids: tuple[str, ...] = Field(default_factory=tuple)
    limiting_member_ids: tuple[str, ...] = Field(default_factory=tuple)


class ComplexConditionScoreEntry(JsonModel):
    """One condition-level mean activity score for one complex."""

    model_config = ConfigDict(extra="forbid")

    complex_id: str = Field(..., min_length=1)
    complex_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    condition: str = Field(..., min_length=1)
    sample_count: int = Field(..., ge=0)
    scored_sample_count: int = Field(..., ge=0)
    high_confidence_sample_count: int = Field(..., ge=0)
    low_confidence_sample_count: int = Field(..., ge=0)
    confidence_status: ComplexActivityConfidenceStatus
    mean_activity_score: float | None = None
    limiting_member_ids: tuple[str, ...] = Field(default_factory=tuple)


class ComplexConditionComparisonEntry(JsonModel):
    """One pairwise condition contrast over one complex activity profile."""

    model_config = ConfigDict(extra="forbid")

    complex_id: str = Field(..., min_length=1)
    complex_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    condition_a_confidence_status: ComplexActivityConfidenceStatus
    condition_b_confidence_status: ComplexActivityConfidenceStatus
    comparison_confidence_status: ComplexActivityConfidenceStatus
    mean_activity_score_a: float | None = None
    mean_activity_score_b: float | None = None
    activity_score_delta: float | None = None
    condition_a_limiting_member_ids: tuple[str, ...] = Field(default_factory=tuple)
    condition_b_limiting_member_ids: tuple[str, ...] = Field(default_factory=tuple)


class ComplexMemberContributionEntry(JsonModel):
    """One sample-level complex member contribution row."""

    model_config = ConfigDict(extra="forbid")

    complex_id: str = Field(..., min_length=1)
    complex_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    batch: str | None = None
    member_kind: ComplexMemberKind
    member_id: str = Field(..., min_length=1)
    resolved_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    observed_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    resolved_protein_count: int = Field(..., ge=0)
    observed_protein_count: int = Field(..., ge=0)
    missing_protein_count: int = Field(..., ge=0)
    member_activity_score: float | None = None
    observed: bool


class UnresolvedComplexActivityMemberEntry(JsonModel):
    """One complex member that could not be resolved onto the scored study matrix."""

    model_config = ConfigDict(extra="forbid")

    complex_id: str = Field(..., min_length=1)
    complex_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    member_kind: ComplexMemberKind
    member_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class ComplexActivitySummary(JsonModel):
    """Stable summary over one complex activity scoring run."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    normalization_method: NormalizationMethod
    complex_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    sample_score_count: int = Field(..., ge=0)
    scored_sample_count: int = Field(..., ge=0)
    high_confidence_sample_score_count: int = Field(..., ge=0)
    low_confidence_sample_score_count: int = Field(..., ge=0)
    sample_entries_with_missing_members: int = Field(..., ge=0)
    member_contribution_count: int = Field(..., ge=0)
    unresolved_member_count: int = Field(..., ge=0)
    condition_count: int = Field(..., ge=0)
    condition_comparison_count: int = Field(..., ge=0)


class ComplexActivityPolicy(JsonModel):
    """Confidence policy for complex activity scoring."""

    model_config = ConfigDict(extra="forbid")

    minimum_observed_member_count: int = Field(default=2, ge=1)


class ComplexActivityReport(JsonModel):
    """Owned complex activity report over a protein quantification matrix."""

    model_config = ConfigDict(extra="forbid")

    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    sample_scores: tuple[ComplexSampleScoreEntry, ...] = Field(default_factory=tuple)
    condition_scores: tuple[ComplexConditionScoreEntry, ...] = Field(
        default_factory=tuple
    )
    condition_comparisons: tuple[ComplexConditionComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    member_contributions: tuple[ComplexMemberContributionEntry, ...] = Field(
        default_factory=tuple
    )
    unresolved_members: tuple[UnresolvedComplexActivityMemberEntry, ...] = Field(
        default_factory=tuple
    )
    summary: ComplexActivitySummary
    note: str = Field(..., min_length=1)
