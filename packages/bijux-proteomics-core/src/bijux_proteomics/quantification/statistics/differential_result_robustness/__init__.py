# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned robustness scoring for quantitative differential-result rows."""

from __future__ import annotations

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
from bijux_proteomics.quantification.contracts.matrix_building import (
    _condition_lookup,
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.matrix_models import (
    LabelFreeQuantTable,
    QuantValue,
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
from bijux_proteomics.quantification.statistics.differential_result_robustness.scoring_policy import (
    note_for_reason_codes as _note_for_reason_codes,
    p_value_score as _p_value_score,
    pairwise_effect_size_score as _pairwise_effect_size_score,
    pairwise_replicate_consistency_score as _pairwise_replicate_consistency_score,
    peptide_support_score as _peptide_support_score,
    qc_status_components as _qc_status_components,
    reason_codes as _reason_codes,
    support_scores as _support_scores,
    time_course_effect_size_score as _time_course_effect_size_score,
    time_course_replicate_consistency_score as _time_course_replicate_consistency_score,
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
