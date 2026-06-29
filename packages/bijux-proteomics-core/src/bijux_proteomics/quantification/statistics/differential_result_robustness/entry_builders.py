# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Result-row builders for differential robustness reports."""

from __future__ import annotations

from bijux_proteomics.quantification.contracts.differential import (
    DifferentialAbundanceEntry,
    DifferentialImputationSignificanceChangeReason,
    DifferentialResultRobustnessQcStatus,
    DifferentialResultRobustnessReasonCode,
    TimeCourseDifferentialEntry,
)
from bijux_proteomics.quantification.contracts.matrix_models import (
    LabelFreeQuantTable,
    QuantValue,
)
from bijux_proteomics.quantification.statistics.differential_result_robustness.models import (
    DifferentialResultRobustnessAnalysisKind,
    DifferentialResultRobustnessEntry,
    DifferentialResultRobustnessReport,
)
from bijux_proteomics.quantification.statistics.differential_result_robustness.scoring_policy import (
    note_for_reason_codes,
    p_value_score,
    pairwise_effect_size_score,
    pairwise_replicate_consistency_score,
    peptide_support_score,
    reason_codes,
    support_scores,
    time_course_effect_size_score,
    time_course_replicate_consistency_score,
)


def build_pairwise_robustness_entry(
    *,
    entry: DifferentialAbundanceEntry,
    table: LabelFreeQuantTable,
    lookup: dict[tuple[str, str], QuantValue],
    sample_ids_a: tuple[str, ...],
    sample_ids_b: tuple[str, ...],
    qc_status: DifferentialResultRobustnessQcStatus,
    qc_score: float,
    qc_reasons: tuple[DifferentialResultRobustnessReasonCode, ...],
) -> DifferentialResultRobustnessEntry:
    """Build one robustness row for one pairwise differential result."""

    effect_size_score = pairwise_effect_size_score(entry)
    fdr_score = p_value_score(entry.adjusted_p_value or entry.p_value)
    missingness_score, imputation_score = support_scores(
        lookup,
        entry.entity_id,
        sample_ids_a + sample_ids_b,
    )
    if (
        entry.imputation_significance_change_reason
        is DifferentialImputationSignificanceChangeReason.SIGNIFICANT_ONLY_AFTER_IMPUTATION
    ):
        imputation_score = min(imputation_score, 0.2)
    peptide_score = peptide_support_score(
        table,
        lookup,
        entry.entity_id,
        sample_ids_a + sample_ids_b,
    )
    replicate_score = pairwise_replicate_consistency_score(
        lookup,
        entry.entity_id,
        sample_ids_a,
        sample_ids_b,
    )
    robustness_score = round(
        (
            effect_size_score * 0.2
            + fdr_score * 0.2
            + missingness_score * 0.15
            + imputation_score * 0.15
            + peptide_score * 0.1
            + replicate_score * 0.1
            + qc_score * 0.1
        ),
        4,
    )
    entry_reason_codes = reason_codes(
        effect_size_score=effect_size_score,
        fdr_score=fdr_score,
        missingness_score=missingness_score,
        imputation_score=imputation_score,
        imputation_significance_change_reason=(
            entry.imputation_significance_change_reason
        ),
        peptide_support_score=peptide_score,
        replicate_consistency_score=replicate_score,
        qc_reasons=qc_reasons,
    )
    return DifferentialResultRobustnessEntry(
        analysis_kind=DifferentialResultRobustnessAnalysisKind.TWO_CONDITION,
        entity_id=entry.entity_id,
        primary_condition=entry.condition_a,
        comparison_condition=entry.condition_b,
        robustness_score=robustness_score,
        qc_status=qc_status,
        reason_codes=entry_reason_codes,
        effect_size_score=effect_size_score,
        fdr_score=fdr_score,
        missingness_score=missingness_score,
        imputation_dependence_score=imputation_score,
        peptide_support_score=peptide_score,
        replicate_consistency_score=replicate_score,
        qc_score=qc_score,
        note=note_for_reason_codes(entry_reason_codes),
    )


def build_time_course_robustness_entry(
    *,
    entry: TimeCourseDifferentialEntry,
    ordered_timepoint_count: int,
    table: LabelFreeQuantTable,
    lookup: dict[tuple[str, str], QuantValue],
    primary_sample_ids: tuple[str, ...],
    comparison_sample_ids: tuple[str, ...],
    qc_status: DifferentialResultRobustnessQcStatus,
    qc_score: float,
    qc_reasons: tuple[DifferentialResultRobustnessReasonCode, ...],
) -> DifferentialResultRobustnessEntry:
    """Build one robustness row for one time-course differential result."""

    effect_size_score = time_course_effect_size_score(entry)
    fdr_candidates = [entry.time_effect_adjusted_p_value or entry.time_effect_p_value]
    if (
        entry.interaction_adjusted_p_value is not None
        or entry.interaction_p_value is not None
    ):
        fdr_candidates.append(
            entry.interaction_adjusted_p_value or entry.interaction_p_value or 1.0
        )
    fdr_score = p_value_score(min(fdr_candidates))
    missingness_score, imputation_score = support_scores(
        lookup,
        entry.entity_id,
        primary_sample_ids + comparison_sample_ids,
    )
    peptide_score = peptide_support_score(
        table,
        lookup,
        entry.entity_id,
        primary_sample_ids + comparison_sample_ids,
    )
    replicate_score = time_course_replicate_consistency_score(
        entry,
        ordered_timepoint_count=ordered_timepoint_count,
        expected_sample_count=max(len(primary_sample_ids), 1),
    )
    robustness_score = round(
        (
            effect_size_score * 0.2
            + fdr_score * 0.2
            + missingness_score * 0.15
            + imputation_score * 0.15
            + peptide_score * 0.1
            + replicate_score * 0.1
            + qc_score * 0.1
        ),
        4,
    )
    entry_reason_codes = reason_codes(
        effect_size_score=effect_size_score,
        fdr_score=fdr_score,
        missingness_score=missingness_score,
        imputation_score=imputation_score,
        imputation_significance_change_reason=(
            entry.imputation_significance_change_reason
        ),
        peptide_support_score=peptide_score,
        replicate_consistency_score=replicate_score,
        qc_reasons=qc_reasons,
    )
    return DifferentialResultRobustnessEntry(
        analysis_kind=DifferentialResultRobustnessAnalysisKind.TIME_COURSE,
        entity_id=entry.entity_id,
        primary_condition=entry.condition,
        comparison_condition=entry.reference_condition,
        robustness_score=robustness_score,
        qc_status=qc_status,
        reason_codes=entry_reason_codes,
        effect_size_score=effect_size_score,
        fdr_score=fdr_score,
        missingness_score=missingness_score,
        imputation_dependence_score=imputation_score,
        peptide_support_score=peptide_score,
        replicate_consistency_score=replicate_score,
        qc_score=qc_score,
        note=note_for_reason_codes(entry_reason_codes),
    )


def build_robustness_report(
    *,
    analysis_kind: DifferentialResultRobustnessAnalysisKind,
    entries: tuple[DifferentialResultRobustnessEntry, ...],
) -> DifferentialResultRobustnessReport:
    """Build one summary report over already-scored robustness rows."""

    return DifferentialResultRobustnessReport(
        analysis_kind=analysis_kind,
        entries=entries,
        low_robustness_entry_count=sum(
            entry.robustness_score < 0.6 for entry in entries
        ),
        caution_qc_entry_count=sum(
            entry.qc_status is DifferentialResultRobustnessQcStatus.CAUTION
            for entry in entries
        ),
        failed_qc_entry_count=sum(
            entry.qc_status is DifferentialResultRobustnessQcStatus.FAIL
            for entry in entries
        ),
        note=(
            "result robustness combines effect size, adjusted significance, missingness, imputation burden, peptide support, replicate consistency, and quant qc"
        ),
    )


__all__ = [
    "build_pairwise_robustness_entry",
    "build_robustness_report",
    "build_time_course_robustness_entry",
]
