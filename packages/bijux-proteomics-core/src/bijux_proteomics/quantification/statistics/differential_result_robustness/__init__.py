# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned robustness scoring for quantitative differential-result rows."""

from __future__ import annotations

import numpy as np

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts.differential import (
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    DifferentialImputationSignificanceChangeReason,
    DifferentialResultRobustnessQcStatus,
    DifferentialResultRobustnessReasonCode,
    TimeCourseDifferentialEntry,
    TimeCourseDifferentialReport,
)
from bijux_proteomics.quantification.contracts.input_models import (
    MissingValueKind,
    QuantEntityLevel,
)
from bijux_proteomics.quantification.contracts.matrix_building import (
    _condition_lookup,
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.matrix_models import (
    LabelFreeQuantTable,
    QuantValue,
    QuantValueOrigin,
)
from bijux_proteomics.quantification.contracts.study_qc import (
    ReplicateAndBatchQcReport,
)
from bijux_proteomics.quantification.statistics.differential_result_robustness.bootstrap import (
    bootstrap_effect_stability,
    render_bootstrap_effect_stability_tsv,
)
from bijux_proteomics.quantification.statistics.differential_result_robustness.models import (
    BootstrapEffectRobustnessTier,
    BootstrapEffectStabilityEntry,
    BootstrapEffectStabilityReport,
    DifferentialResultRobustnessAnalysisKind,
    DifferentialResultRobustnessEntry,
    DifferentialResultRobustnessReport,
)
from bijux_proteomics.quantification.provenance.replicate_qc import (
    build_replicate_and_batch_qc_report,
)
 

def build_differential_abundance_robustness_report(
    report: DifferentialAbundanceReport,
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    replicate_qc_report: ReplicateAndBatchQcReport | None = None,
) -> DifferentialResultRobustnessReport:
    """Score each pairwise differential result beyond p-value ranking alone."""

    active_qc = replicate_qc_report or build_replicate_and_batch_qc_report(
        table,
        design_entries=design_entries,
    )
    condition_by_sample = _condition_lookup(design_entries)
    sample_ids_by_condition: dict[str, tuple[str, ...]] = {}
    for condition in sorted(
        {condition for condition in condition_by_sample.values() if condition}
    ):
        sample_ids_by_condition[condition] = tuple(
            sample_id
            for sample_id in table.sample_ids
            if condition_by_sample.get(sample_id) == condition
        )
    lookup = _matrix_value_index(table)
    qc_status, qc_score, qc_reasons = _qc_status_components(active_qc)
    entries = tuple(
        sorted(
            (
                _build_pairwise_robustness_entry(
                    entry=entry,
                    table=table,
                    lookup=lookup,
                    sample_ids_a=sample_ids_by_condition.get(entry.condition_a, ()),
                    sample_ids_b=sample_ids_by_condition.get(entry.condition_b, ()),
                    qc_status=qc_status,
                    qc_score=qc_score,
                    qc_reasons=qc_reasons,
                )
                for entry in report.entries
            ),
            key=lambda entry: (
                entry.entity_id,
                entry.primary_condition,
                entry.comparison_condition or "",
            ),
        )
    )
    return _build_robustness_report(
        analysis_kind=DifferentialResultRobustnessAnalysisKind.TWO_CONDITION,
        entries=entries,
    )


def annotate_differential_abundance_report_robustness(
    report: DifferentialAbundanceReport,
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    replicate_qc_report: ReplicateAndBatchQcReport | None = None,
) -> DifferentialAbundanceReport:
    """Attach owned robustness fields to pairwise differential-result rows."""

    robustness_report = build_differential_abundance_robustness_report(
        report,
        table,
        design_entries,
        replicate_qc_report=replicate_qc_report,
    )
    robustness_by_key = {
        (entry.entity_id, entry.primary_condition, entry.comparison_condition): entry
        for entry in robustness_report.entries
    }
    entries = tuple(
        result_entry.model_copy(
            update={
                "robustness_score": robustness_entry.robustness_score,
                "robustness_qc_status": robustness_entry.qc_status,
                "robustness_reason_codes": robustness_entry.reason_codes,
                "robustness_note": robustness_entry.note,
            }
        )
        for result_entry in report.entries
        if (
            robustness_entry := robustness_by_key[
                (
                    result_entry.entity_id,
                    result_entry.condition_a,
                    result_entry.condition_b,
                )
            ]
        )
    )
    return report.model_copy(update={"entries": entries})


def build_time_course_differential_robustness_report(
    report: TimeCourseDifferentialReport,
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    replicate_qc_report: ReplicateAndBatchQcReport | None = None,
) -> DifferentialResultRobustnessReport:
    """Score each ordered-timepoint differential result beyond significance alone."""

    active_qc = replicate_qc_report or build_replicate_and_batch_qc_report(
        table,
        design_entries=design_entries,
    )
    condition_by_sample = _condition_lookup(design_entries)
    sample_ids_by_condition: dict[str, tuple[str, ...]] = {}
    for condition in sorted(
        {condition for condition in condition_by_sample.values() if condition}
    ):
        sample_ids_by_condition[condition] = tuple(
            sample_id
            for sample_id in table.sample_ids
            if condition_by_sample.get(sample_id) == condition
        )
    lookup = _matrix_value_index(table)
    qc_status, qc_score, qc_reasons = _qc_status_components(active_qc)
    entries = tuple(
        sorted(
            (
                _build_time_course_robustness_entry(
                    entry=entry,
                    ordered_timepoint_count=max(len(report.ordered_timepoints), 1),
                    table=table,
                    lookup=lookup,
                    primary_sample_ids=sample_ids_by_condition.get(entry.condition, ()),
                    comparison_sample_ids=sample_ids_by_condition.get(
                        entry.reference_condition, ()
                    ),
                    qc_status=qc_status,
                    qc_score=qc_score,
                    qc_reasons=qc_reasons,
                )
                for entry in report.entries
            ),
            key=lambda entry: (
                entry.entity_id,
                entry.primary_condition,
                entry.comparison_condition or "",
            ),
        )
    )
    return _build_robustness_report(
        analysis_kind=DifferentialResultRobustnessAnalysisKind.TIME_COURSE,
        entries=entries,
    )


def annotate_time_course_differential_report_robustness(
    report: TimeCourseDifferentialReport,
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    replicate_qc_report: ReplicateAndBatchQcReport | None = None,
) -> TimeCourseDifferentialReport:
    """Attach owned robustness fields to ordered-timepoint differential rows."""

    robustness_report = build_time_course_differential_robustness_report(
        report,
        table,
        design_entries,
        replicate_qc_report=replicate_qc_report,
    )
    robustness_by_key = {
        (entry.entity_id, entry.primary_condition, entry.comparison_condition): entry
        for entry in robustness_report.entries
    }
    entries = tuple(
        result_entry.model_copy(
            update={
                "robustness_score": robustness_entry.robustness_score,
                "robustness_qc_status": robustness_entry.qc_status,
                "robustness_reason_codes": robustness_entry.reason_codes,
                "robustness_note": robustness_entry.note,
            }
        )
        for result_entry in report.entries
        if (
            robustness_entry := robustness_by_key[
                (
                    result_entry.entity_id,
                    result_entry.condition,
                    result_entry.reference_condition,
                )
            ]
        )
    )
    return report.model_copy(update={"entries": entries})


def _build_pairwise_robustness_entry(
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
    effect_size_score = _pairwise_effect_size_score(entry)
    fdr_score = _p_value_score(entry.adjusted_p_value or entry.p_value)
    missingness_score, imputation_score = _support_scores(
        lookup,
        entry.entity_id,
        sample_ids_a + sample_ids_b,
    )
    if (
        entry.imputation_significance_change_reason
        is DifferentialImputationSignificanceChangeReason.SIGNIFICANT_ONLY_AFTER_IMPUTATION
    ):
        imputation_score = min(imputation_score, 0.2)
    peptide_support_score = _peptide_support_score(
        table,
        lookup,
        entry.entity_id,
        sample_ids_a + sample_ids_b,
    )
    replicate_consistency_score = _pairwise_replicate_consistency_score(
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
            + peptide_support_score * 0.1
            + replicate_consistency_score * 0.1
            + qc_score * 0.1
        ),
        4,
    )
    reason_codes = _reason_codes(
        effect_size_score=effect_size_score,
        fdr_score=fdr_score,
        missingness_score=missingness_score,
        imputation_score=imputation_score,
        imputation_significance_change_reason=(
            entry.imputation_significance_change_reason
        ),
        peptide_support_score=peptide_support_score,
        replicate_consistency_score=replicate_consistency_score,
        qc_reasons=qc_reasons,
    )
    return DifferentialResultRobustnessEntry(
        analysis_kind=DifferentialResultRobustnessAnalysisKind.TWO_CONDITION,
        entity_id=entry.entity_id,
        primary_condition=entry.condition_a,
        comparison_condition=entry.condition_b,
        robustness_score=robustness_score,
        qc_status=qc_status,
        reason_codes=reason_codes,
        effect_size_score=effect_size_score,
        fdr_score=fdr_score,
        missingness_score=missingness_score,
        imputation_dependence_score=imputation_score,
        peptide_support_score=peptide_support_score,
        replicate_consistency_score=replicate_consistency_score,
        qc_score=qc_score,
        note=_note_for_reason_codes(reason_codes),
    )


def _build_time_course_robustness_entry(
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
    effect_size_score = _time_course_effect_size_score(entry)
    fdr_candidates = [entry.time_effect_adjusted_p_value or entry.time_effect_p_value]
    if (
        entry.interaction_adjusted_p_value is not None
        or entry.interaction_p_value is not None
    ):
        fdr_candidates.append(
            entry.interaction_adjusted_p_value or entry.interaction_p_value or 1.0
        )
    fdr_score = _p_value_score(min(fdr_candidates))
    missingness_score, imputation_score = _support_scores(
        lookup,
        entry.entity_id,
        primary_sample_ids + comparison_sample_ids,
    )
    peptide_support_score = _peptide_support_score(
        table,
        lookup,
        entry.entity_id,
        primary_sample_ids + comparison_sample_ids,
    )
    replicate_consistency_score = _time_course_replicate_consistency_score(
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
            + peptide_support_score * 0.1
            + replicate_consistency_score * 0.1
            + qc_score * 0.1
        ),
        4,
    )
    reason_codes = _reason_codes(
        effect_size_score=effect_size_score,
        fdr_score=fdr_score,
        missingness_score=missingness_score,
        imputation_score=imputation_score,
        imputation_significance_change_reason=(
            entry.imputation_significance_change_reason
        ),
        peptide_support_score=peptide_support_score,
        replicate_consistency_score=replicate_consistency_score,
        qc_reasons=qc_reasons,
    )
    return DifferentialResultRobustnessEntry(
        analysis_kind=DifferentialResultRobustnessAnalysisKind.TIME_COURSE,
        entity_id=entry.entity_id,
        primary_condition=entry.condition,
        comparison_condition=entry.reference_condition,
        robustness_score=robustness_score,
        qc_status=qc_status,
        reason_codes=reason_codes,
        effect_size_score=effect_size_score,
        fdr_score=fdr_score,
        missingness_score=missingness_score,
        imputation_dependence_score=imputation_score,
        peptide_support_score=peptide_support_score,
        replicate_consistency_score=replicate_consistency_score,
        qc_score=qc_score,
        note=_note_for_reason_codes(reason_codes),
    )


def _build_robustness_report(
    *,
    analysis_kind: DifferentialResultRobustnessAnalysisKind,
    entries: tuple[DifferentialResultRobustnessEntry, ...],
) -> DifferentialResultRobustnessReport:
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


def _pairwise_effect_size_score(entry: DifferentialAbundanceEntry) -> float:
    magnitude = (
        abs(entry.effect_size_cohens_d)
        if entry.effect_size_cohens_d is not None
        else abs(entry.log2_fold_change)
    )
    return _score_by_thresholds(
        magnitude,
        ((1.5, 1.0), (1.0, 0.85), (0.5, 0.65)),
        fallback=0.4,
    )


def _time_course_effect_size_score(entry: TimeCourseDifferentialEntry) -> float:
    magnitude = max(
        abs(entry.slope_per_timepoint),
        abs(entry.interaction_effect or 0.0),
    )
    return _score_by_thresholds(
        magnitude,
        ((1.0, 1.0), (0.5, 0.8), (0.25, 0.6)),
        fallback=0.35,
    )


def _p_value_score(value: float) -> float:
    bounded = min(max(float(value), 0.0), 1.0)
    return _score_by_thresholds(
        1.0 - bounded,
        ((0.99, 1.0), (0.95, 0.85), (0.9, 0.6)),
        fallback=0.3,
    )


def _support_scores(
    lookup: dict[tuple[str, str], QuantValue],
    entity_id: str,
    sample_ids: tuple[str, ...],
) -> tuple[float, float]:
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
    imputation_score = _score_by_thresholds(
        1.0 - imputation_fraction,
        ((1.0, 1.0), (0.75, 0.8), (0.5, 0.55)),
        fallback=0.25,
    )
    return support_score, imputation_score


def _peptide_support_score(
    table: LabelFreeQuantTable,
    lookup: dict[tuple[str, str], QuantValue],
    entity_id: str,
    sample_ids: tuple[str, ...],
) -> float:
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
    return _score_by_thresholds(count, ((3, 1.0), (2, 0.8)), fallback=0.45)


def _pairwise_replicate_consistency_score(
    lookup: dict[tuple[str, str], QuantValue],
    entity_id: str,
    sample_ids_a: tuple[str, ...],
    sample_ids_b: tuple[str, ...],
) -> float:
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
            _score_by_thresholds(
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


def _time_course_replicate_consistency_score(
    entry: TimeCourseDifferentialEntry,
    *,
    ordered_timepoint_count: int,
    expected_sample_count: int,
) -> float:
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
        uncertainty_score = _score_by_thresholds(
            ratio,
            ((4.0, 1.0), (2.0, 0.8), (1.0, 0.6)),
            fallback=0.35,
        )
    return round((coverage_score + uncertainty_score) / 2.0, 4)


def _qc_status_components(
    qc_report: ReplicateAndBatchQcReport,
) -> tuple[
    DifferentialResultRobustnessQcStatus,
    float,
    tuple[DifferentialResultRobustnessReasonCode, ...],
]:
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


def _reason_codes(
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


def _note_for_reason_codes(
    reason_codes: tuple[DifferentialResultRobustnessReasonCode, ...],
) -> str:
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


def _score_by_thresholds(
    value: float,
    thresholds: tuple[tuple[float, float], ...],
    *,
    fallback: float,
) -> float:
    for threshold, score in thresholds:
        if value >= threshold:
            return score
    return fallback


__all__ = [
    "BootstrapEffectRobustnessTier",
    "BootstrapEffectStabilityEntry",
    "BootstrapEffectStabilityReport",
    "DifferentialResultRobustnessAnalysisKind",
    "DifferentialResultRobustnessEntry",
    "DifferentialResultRobustnessReport",
    "annotate_differential_abundance_report_robustness",
    "bootstrap_effect_stability",
    "annotate_time_course_differential_report_robustness",
    "build_differential_abundance_robustness_report",
    "build_time_course_differential_robustness_report",
    "render_bootstrap_effect_stability_tsv",
]
