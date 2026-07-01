# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein-set scoring surfaces for sample-level biological program review."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bijux_proteomics.interpretation.protein_set_scoring.models import (
    ProteinSetRecord,
    ProteinSetScoreConfidenceStatus,
    ProteinSetScoringPolicy,
    ProteinSetScoringReport,
    ProteinSetScoringSummary,
)
from bijux_proteomics.interpretation.protein_set_scoring.score_calculation import (
    build_condition_comparisons,
    build_condition_scores,
    build_sample_scores_and_unresolved_members,
)
from bijux_proteomics.quantification.contracts.input_models import QuantEntityLevel
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable

if TYPE_CHECKING:
    from bijux_proteomics.io.formats import ExperimentalDesignEntry


def build_protein_set_scoring_report(
    table: LabelFreeQuantTable,
    protein_set_records: tuple[ProteinSetRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
    policy: ProteinSetScoringPolicy | None = None,
) -> ProteinSetScoringReport:
    """Score protein sets per sample over one normalized protein quant table."""

    if table.entity_level is not QuantEntityLevel.PROTEIN:
        raise ValueError(
            "protein set scoring requires a protein-level quantification table"
        )

    active_policy = policy or ProteinSetScoringPolicy()
    sample_ids = table.sample_ids
    sample_scores, unresolved_members = build_sample_scores_and_unresolved_members(
        table,
        protein_set_records,
        design_entries=design_entries,
        minimum_observed_member_count=active_policy.minimum_observed_member_count,
    )
    condition_scores = build_condition_scores(sample_scores)
    condition_comparisons = build_condition_comparisons(condition_scores)
    return ProteinSetScoringReport(
        sample_ids=sample_ids,
        sample_scores=sample_scores,
        condition_scores=condition_scores,
        condition_comparisons=condition_comparisons,
        unresolved_members=unresolved_members,
        summary=ProteinSetScoringSummary(
            entity_level=table.entity_level,
            measure_kind=table.measure_kind,
            aggregation_method=table.aggregation_method,
            normalization_method=table.normalization_method,
            set_count=len({record.set_id for record in protein_set_records}),
            sample_count=len(sample_ids),
            feature_protein_count=len(table.entity_ids),
            sample_score_count=len(sample_scores),
            scored_sample_count=sum(
                1 for entry in sample_scores if entry.activity_score is not None
            ),
            high_confidence_sample_score_count=sum(
                1
                for entry in sample_scores
                if entry.confidence_status
                is ProteinSetScoreConfidenceStatus.HIGH_CONFIDENCE
            ),
            low_confidence_sample_score_count=sum(
                1
                for entry in sample_scores
                if entry.confidence_status
                is ProteinSetScoreConfidenceStatus.LOW_CONFIDENCE
            ),
            sample_entries_with_missing_members=sum(
                1 for entry in sample_scores if entry.missing_member_count > 0
            ),
            unresolved_member_count=len(unresolved_members),
            condition_count=len({entry.condition for entry in condition_scores}),
            condition_comparison_count=len(condition_comparisons),
        ),
        note=(
            "protein set scoring standardizes normalized protein abundances across samples, averages observed member signal per sample, preserves member coverage explicitly, and marks sparse member support as low confidence"
        ),
    )


__all__ = [
    "build_protein_set_scoring_report",
]
