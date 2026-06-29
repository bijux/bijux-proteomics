# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Scoring policy for differential-result robustness."""

from __future__ import annotations

import numpy as np

from bijux_proteomics.quantification.contracts.differential import (
    DifferentialAbundanceEntry,
    DifferentialImputationSignificanceChangeReason,
    DifferentialResultRobustnessQcStatus,
    DifferentialResultRobustnessReasonCode,
    TimeCourseDifferentialEntry,
)
from bijux_proteomics.quantification.contracts.input_models import (
    MissingValueKind,
    QuantEntityLevel,
)
from bijux_proteomics.quantification.contracts.matrix_models import (
    LabelFreeQuantTable,
    QuantValue,
    QuantValueOrigin,
)
from bijux_proteomics.quantification.contracts.study_qc import (
    ReplicateAndBatchQcReport,
)


def pairwise_effect_size_score(entry: DifferentialAbundanceEntry) -> float:
    """Score one pairwise result by absolute effect magnitude."""

    magnitude = (
        abs(entry.effect_size_cohens_d)
        if entry.effect_size_cohens_d is not None
        else abs(entry.log2_fold_change)
    )
    return score_by_thresholds(
        magnitude,
        ((1.5, 1.0), (1.0, 0.85), (0.5, 0.65)),
        fallback=0.4,
    )


def time_course_effect_size_score(entry: TimeCourseDifferentialEntry) -> float:
    """Score one time-course result by slope or interaction magnitude."""

    magnitude = max(
        abs(entry.slope_per_timepoint),
        abs(entry.interaction_effect or 0.0),
    )
    return score_by_thresholds(
        magnitude,
        ((1.0, 1.0), (0.5, 0.8), (0.25, 0.6)),
        fallback=0.35,
    )


def p_value_score(value: float) -> float:
    """Convert one p-value-like quantity into a bounded robustness score."""

    bounded = min(max(float(value), 0.0), 1.0)
    return score_by_thresholds(
        1.0 - bounded,
        ((0.99, 1.0), (0.95, 0.85), (0.9, 0.6)),
        fallback=0.3,
    )


def support_scores(
    lookup: dict[tuple[str, str], QuantValue],
    entity_id: str,
    sample_ids: tuple[str, ...],
) -> tuple[float, float]:
    """Return missingness and imputation support scores for one entity."""

    if not sample_ids:
        return 1.0, 1.0
    support_weights: list[float] = []
    imputed_count = 0
    for sample_id in sample_ids:
        cell = lookup.get((entity_id, sample_id))
        if cell is None:
            support_weights.append(0.0)
            continue
        original_kind = (
            cell.imputation_provenance.original_missing_value_kind
            if cell.imputation_provenance is not None
            else cell.missing_value_kind
        )
        if original_kind is MissingValueKind.OBSERVED:
            support_weights.append(1.0)
        elif original_kind is MissingValueKind.ZERO:
            support_weights.append(0.7)
        else:
            support_weights.append(0.0)
        if cell.imputation_provenance is not None or (
            cell.value_provenance is not None
            and cell.value_provenance.value_origin is QuantValueOrigin.IMPUTED
        ):
            imputed_count += 1
    support_score = round(sum(support_weights) / len(sample_ids), 4)
    imputation_fraction = imputed_count / len(sample_ids)
    imputation_score = score_by_thresholds(
        1.0 - imputation_fraction,
        ((1.0, 1.0), (0.75, 0.8), (0.5, 0.55)),
        fallback=0.25,
    )
    return support_score, imputation_score


def peptide_support_score(
    table: LabelFreeQuantTable,
    lookup: dict[tuple[str, str], QuantValue],
    entity_id: str,
    sample_ids: tuple[str, ...],
) -> float:
    """Score protein support by distinct contributing peptides."""

    if table.entity_level is not QuantEntityLevel.PROTEIN:
        return 1.0
    peptides: set[str] = set()
    for sample_id in sample_ids:
        cell = lookup.get((entity_id, sample_id))
        if cell is None or cell.value_provenance is None:
            continue
        peptides.update(cell.value_provenance.source_peptides)
        for contributor in cell.value_provenance.selected_contributors:
            canonical_peptide = contributor.canonical_peptide
            if canonical_peptide is not None and canonical_peptide != "":
                peptides.add(canonical_peptide)
    if not peptides:
        peptides.update(table.entity_member_peptides.get(entity_id, ()))
    count = len(peptides)
    return score_by_thresholds(count, ((3, 1.0), (2, 0.8)), fallback=0.45)


def pairwise_replicate_consistency_score(
    lookup: dict[tuple[str, str], QuantValue],
    entity_id: str,
    sample_ids_a: tuple[str, ...],
    sample_ids_b: tuple[str, ...],
) -> float:
    """Score pairwise replicate agreement within each condition."""

    condition_scores: list[float] = []
    for sample_ids in (sample_ids_a, sample_ids_b):
        abundances = [
            float(cell.abundance)
            for sample_id in sample_ids
            if (cell := lookup.get((entity_id, sample_id))) is not None
            and cell.abundance is not None
        ]
        if len(abundances) < 2:
            condition_scores.append(0.5)
            continue
        mean_abundance = float(np.mean(abundances))
        if mean_abundance <= 0.0:
            condition_scores.append(0.3)
            continue
        cv = float(np.std(np.array(abundances, dtype=float), ddof=1) / mean_abundance)
        condition_scores.append(
            score_by_thresholds(
                1.0 - min(max(cv, 0.0), 1.0),
                ((0.8, 1.0), (0.65, 0.8), (0.5, 0.6)),
                fallback=0.3,
            )
        )
    return (
        round(sum(condition_scores) / len(condition_scores), 4)
        if condition_scores
        else 0.5
    )


def time_course_replicate_consistency_score(
    entry: TimeCourseDifferentialEntry,
    *,
    ordered_timepoint_count: int,
    expected_sample_count: int,
) -> float:
    """Score time-course support from coverage and uncertainty."""

    timepoint_coverage = min(
        max(entry.observed_timepoint_count / max(ordered_timepoint_count, 1), 0.0),
        1.0,
    )
    sample_coverage = min(
        max(entry.observed_sample_count / max(expected_sample_count, 1), 0.0),
        1.0,
    )
    coverage_score = round((timepoint_coverage + sample_coverage) / 2.0, 4)
    if entry.slope_standard_error is None:
        uncertainty_score = 0.75
    else:
        signal = max(
            abs(entry.slope_per_timepoint),
            abs(entry.interaction_effect or 0.0),
        )
        ratio = signal / max(entry.slope_standard_error, 1e-6)
        uncertainty_score = score_by_thresholds(
            ratio,
            ((4.0, 1.0), (2.0, 0.8), (1.0, 0.6)),
            fallback=0.35,
        )
    return round((coverage_score + uncertainty_score) / 2.0, 4)


def qc_status_components(
    qc_report: ReplicateAndBatchQcReport,
) -> tuple[
    DifferentialResultRobustnessQcStatus,
    float,
    tuple[DifferentialResultRobustnessReasonCode, ...],
]:
    """Return robustness-wide QC status, score, and inherited reasons."""

    if qc_report.batch_effect_report.batch_correction_blocked:
        return (
            DifferentialResultRobustnessQcStatus.FAIL,
            0.35,
            (DifferentialResultRobustnessReasonCode.FAILED_QC,),
        )
    caution = (
        qc_report.flagged_batch_count > 0
        or bool(qc_report.outlier_samples)
        or any(entry.flagged for entry in qc_report.replicate_cv_report.entries)
    )
    if caution:
        return (
            DifferentialResultRobustnessQcStatus.CAUTION,
            0.7,
            (DifferentialResultRobustnessReasonCode.CAUTION_QC,),
        )
    return DifferentialResultRobustnessQcStatus.PASSED, 1.0, ()


def reason_codes(
    *,
    effect_size_score: float,
    fdr_score: float,
    missingness_score: float,
    imputation_score: float,
    imputation_significance_change_reason: DifferentialImputationSignificanceChangeReason
    | None,
    peptide_support_score: float,
    replicate_consistency_score: float,
    qc_reasons: tuple[DifferentialResultRobustnessReasonCode, ...],
) -> tuple[DifferentialResultRobustnessReasonCode, ...]:
    """Summarize all policy triggers that weakened robustness."""

    reasons: list[DifferentialResultRobustnessReasonCode] = []
    if effect_size_score < 0.7:
        reasons.append(DifferentialResultRobustnessReasonCode.LOW_EFFECT_SIZE)
    if fdr_score < 0.85:
        reasons.append(DifferentialResultRobustnessReasonCode.ELEVATED_FDR)
    if missingness_score < 0.75:
        reasons.append(DifferentialResultRobustnessReasonCode.HIGH_MISSINGNESS)
    if imputation_score < 0.8:
        reasons.append(DifferentialResultRobustnessReasonCode.IMPUTATION_HEAVY)
    if (
        imputation_significance_change_reason
        is DifferentialImputationSignificanceChangeReason.SIGNIFICANT_ONLY_AFTER_IMPUTATION
    ):
        reasons.append(
            DifferentialResultRobustnessReasonCode.IMPUTATION_DEPENDENT_SIGNIFICANCE
        )
    if peptide_support_score < 0.8:
        reasons.append(DifferentialResultRobustnessReasonCode.LOW_PEPTIDE_SUPPORT)
    if replicate_consistency_score < 0.75:
        reasons.append(DifferentialResultRobustnessReasonCode.REPLICATE_INCONSISTENCY)
    reasons.extend(qc_reasons)
    return tuple(dict.fromkeys(reasons))


def note_for_reason_codes(
    reason_codes: tuple[DifferentialResultRobustnessReasonCode, ...],
) -> str:
    """Render one stable explanation string for one robustness reason set."""

    if not reason_codes:
        return (
            "result remains robust across effect, significance, support, and qc checks"
        )
    messages = {
        DifferentialResultRobustnessReasonCode.LOW_EFFECT_SIZE: "effect size is modest",
        DifferentialResultRobustnessReasonCode.ELEVATED_FDR: "adjusted significance is near the reporting threshold",
        DifferentialResultRobustnessReasonCode.HIGH_MISSINGNESS: "missing or zero-heavy support reduces confidence",
        DifferentialResultRobustnessReasonCode.IMPUTATION_HEAVY: "quantitative support depends strongly on imputed cells",
        DifferentialResultRobustnessReasonCode.IMPUTATION_DEPENDENT_SIGNIFICANCE: "result is significant only after imputation",
        DifferentialResultRobustnessReasonCode.LOW_PEPTIDE_SUPPORT: "protein-level support comes from few peptides",
        DifferentialResultRobustnessReasonCode.REPLICATE_INCONSISTENCY: "replicate spread is high relative to the signal",
        DifferentialResultRobustnessReasonCode.CAUTION_QC: "quant qc is cautionary for this result set",
        DifferentialResultRobustnessReasonCode.FAILED_QC: "quant qc failed for this result set",
    }
    return "; ".join(messages[reason] for reason in reason_codes)


def score_by_thresholds(
    value: float,
    thresholds: tuple[tuple[float, float], ...],
    *,
    fallback: float,
) -> float:
    """Apply one stable threshold ladder to a scalar score input."""

    for threshold, score in thresholds:
        if value >= threshold:
            return score
    return fallback


__all__ = [
    "note_for_reason_codes",
    "p_value_score",
    "pairwise_effect_size_score",
    "pairwise_replicate_consistency_score",
    "peptide_support_score",
    "qc_status_components",
    "reason_codes",
    "score_by_thresholds",
    "support_scores",
    "time_course_effect_size_score",
    "time_course_replicate_consistency_score",
]
