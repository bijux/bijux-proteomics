# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Contracts and report state for protein-set scoring."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.quantification.contracts.input_models import (
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
)
from bijux_proteomics_foundation import JsonModel

ProteinSetScoreConfidenceStatus = ConfidenceTier


class ProteinSetColumnMapping(JsonModel):
    """Column mapping from one protein-set table into owned scoring fields."""

    model_config = ConfigDict(extra="forbid")

    set_id: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    set_name: str | None = None
    set_category: str | None = None
    source_name: str | None = None
    source_accession: str | None = None


class ProteinSetRecord(JsonModel):
    """One normalized protein-set membership row."""

    model_config = ConfigDict(extra="forbid")

    set_id: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    set_name: str | None = None
    set_category: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedProteinSetRow(JsonModel):
    """One rejected protein-set row with a stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class ProteinSetImportSummary(JsonModel):
    """Stable summary over one protein-set import pass."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_set_count: int = Field(..., ge=0)
    distinct_member_count: int = Field(..., ge=0)
    source_counts: dict[str, int] = Field(default_factory=dict)


class ProteinSetImportReport(JsonModel):
    """Governed protein-set import report."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[ProteinSetRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedProteinSetRow, ...] = Field(default_factory=tuple)
    column_mapping: ProteinSetColumnMapping
    summary: ProteinSetImportSummary
    note: str = Field(..., min_length=1)


class ProteinSetSampleScoreEntry(JsonModel):
    """One sample-level activity score for one protein set."""

    model_config = ConfigDict(extra="forbid")

    set_id: str = Field(..., min_length=1)
    set_name: str | None = None
    set_category: str | None = None
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
    confidence_status: ProteinSetScoreConfidenceStatus
    confidence_reason: str | None = None
    observed_member_ids: tuple[str, ...] = Field(default_factory=tuple)
    missing_member_ids: tuple[str, ...] = Field(default_factory=tuple)


class ProteinSetConditionScoreEntry(JsonModel):
    """One condition-level mean score over one protein set."""

    model_config = ConfigDict(extra="forbid")

    set_id: str = Field(..., min_length=1)
    set_name: str | None = None
    set_category: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    condition: str = Field(..., min_length=1)
    sample_count: int = Field(..., ge=0)
    scored_sample_count: int = Field(..., ge=0)
    high_confidence_sample_count: int = Field(..., ge=0)
    low_confidence_sample_count: int = Field(..., ge=0)
    confidence_status: ProteinSetScoreConfidenceStatus
    mean_activity_score: float | None = None


class ProteinSetConditionComparisonEntry(JsonModel):
    """One pairwise condition comparison over one protein set."""

    model_config = ConfigDict(extra="forbid")

    set_id: str = Field(..., min_length=1)
    set_name: str | None = None
    set_category: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    condition_a_confidence_status: ProteinSetScoreConfidenceStatus
    condition_b_confidence_status: ProteinSetScoreConfidenceStatus
    comparison_confidence_status: ProteinSetScoreConfidenceStatus
    mean_activity_score_a: float | None = None
    mean_activity_score_b: float | None = None
    activity_score_delta: float | None = None


class UnresolvedProteinSetMemberEntry(JsonModel):
    """One set member that could not be mapped onto the study protein table."""

    model_config = ConfigDict(extra="forbid")

    set_id: str = Field(..., min_length=1)
    set_name: str | None = None
    set_category: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    protein_ref: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class ProteinSetScoringSummary(JsonModel):
    """Compact summary over one protein-set scoring run."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    normalization_method: NormalizationMethod
    set_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    feature_protein_count: int = Field(..., ge=0)
    sample_score_count: int = Field(..., ge=0)
    scored_sample_count: int = Field(..., ge=0)
    high_confidence_sample_score_count: int = Field(..., ge=0)
    low_confidence_sample_score_count: int = Field(..., ge=0)
    sample_entries_with_missing_members: int = Field(..., ge=0)
    unresolved_member_count: int = Field(..., ge=0)
    condition_count: int = Field(..., ge=0)
    condition_comparison_count: int = Field(..., ge=0)


class ProteinSetScoringPolicy(JsonModel):
    """Confidence policy for protein-set activity scoring."""

    model_config = ConfigDict(extra="forbid")

    minimum_observed_member_count: int = Field(default=2, ge=1)


class ProteinSetScoringReport(JsonModel):
    """Owned protein-set scoring report over a normalized protein matrix."""

    model_config = ConfigDict(extra="forbid")

    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    sample_scores: tuple[ProteinSetSampleScoreEntry, ...] = Field(default_factory=tuple)
    condition_scores: tuple[ProteinSetConditionScoreEntry, ...] = Field(
        default_factory=tuple
    )
    condition_comparisons: tuple[ProteinSetConditionComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    unresolved_members: tuple[UnresolvedProteinSetMemberEntry, ...] = Field(
        default_factory=tuple
    )
    summary: ProteinSetScoringSummary
    note: str = Field(..., min_length=1)


__all__ = [
    "ProteinSetColumnMapping",
    "ProteinSetConditionComparisonEntry",
    "ProteinSetConditionScoreEntry",
    "ProteinSetScoreConfidenceStatus",
    "ProteinSetImportReport",
    "ProteinSetImportSummary",
    "ProteinSetRecord",
    "ProteinSetSampleScoreEntry",
    "ProteinSetScoringPolicy",
    "ProteinSetScoringReport",
    "ProteinSetScoringSummary",
    "RejectedProteinSetRow",
    "UnresolvedProteinSetMemberEntry",
]
