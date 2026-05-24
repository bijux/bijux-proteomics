# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned robustness scoring for quantitative differential-result rows."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    DifferentialImputationSignificanceChangeReason,
    DifferentialResultRobustnessQcStatus,
    DifferentialResultRobustnessReasonCode,
    LabelFreeQuantTable,
    MissingValueKind,
    QuantEntityLevel,
    QuantValue,
    QuantValueOrigin,
    ReplicateAndBatchQcReport,
    TimeCourseDifferentialEntry,
    TimeCourseDifferentialReport,
    _condition_lookup,
    _matrix_value_index,
)
from bijux_proteomics.quantification.replicate_qc import (
    build_replicate_and_batch_qc_report,
)
from bijux_proteomics.study import (
    SampleRunAnalysisPolicy,
    resolve_sample_run_analysis_entries,
)
from bijux_proteomics_foundation import JsonModel


class DifferentialResultRobustnessAnalysisKind(StrEnum):
    """Stable analysis-family labels for robustness ledgers."""

    TWO_CONDITION = "two_condition"
    TIME_COURSE = "time_course"


class DifferentialResultRobustnessEntry(JsonModel):
    """One robustness decomposition row for one differential result."""

    model_config = ConfigDict(extra="forbid")

    analysis_kind: DifferentialResultRobustnessAnalysisKind
    entity_id: str = Field(..., min_length=1)
    primary_condition: str = Field(..., min_length=1)
    comparison_condition: str | None = None
    robustness_score: float = Field(..., ge=0.0, le=1.0)
    qc_status: DifferentialResultRobustnessQcStatus
    reason_codes: tuple[DifferentialResultRobustnessReasonCode, ...] = Field(
        default_factory=tuple
    )
    effect_size_score: float = Field(..., ge=0.0, le=1.0)
    fdr_score: float = Field(..., ge=0.0, le=1.0)
    missingness_score: float = Field(..., ge=0.0, le=1.0)
    imputation_dependence_score: float = Field(..., ge=0.0, le=1.0)
    peptide_support_score: float = Field(..., ge=0.0, le=1.0)
    replicate_consistency_score: float = Field(..., ge=0.0, le=1.0)
    qc_score: float = Field(..., ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class DifferentialResultRobustnessReport(JsonModel):
    """Owned robustness report over one differential result collection."""

    model_config = ConfigDict(extra="forbid")

    analysis_kind: DifferentialResultRobustnessAnalysisKind
    entries: tuple[DifferentialResultRobustnessEntry, ...] = Field(
        default_factory=tuple
    )
    low_robustness_entry_count: int = Field(..., ge=0)
    caution_qc_entry_count: int = Field(..., ge=0)
    failed_qc_entry_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class BootstrapEffectRobustnessTier(StrEnum):
    """Stable resampling tiers for entity-level effect robustness."""

    STABLE = "stable"
    CAUTION = "caution"
    UNSTABLE = "unstable"


class BootstrapEffectStabilityEntry(JsonModel):
    """One entity-level effect stability summary over bootstrap resamples."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    median_log2fc: float
    sign_consistency: float = Field(..., ge=0.0, le=1.0)
    q_value_stability: float = Field(..., ge=0.0, le=1.0)
    robustness_tier: BootstrapEffectRobustnessTier


class BootstrapEffectStabilityReport(JsonModel):
    """Owned bootstrap effect-stability report over one two-condition contrast."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    n_resamples: int = Field(..., ge=10)
    significance_threshold: float = Field(..., gt=0.0, lt=1.0)
    entries: tuple[BootstrapEffectStabilityEntry, ...] = Field(default_factory=tuple)
    stable_entry_count: int = Field(..., ge=0)
    caution_entry_count: int = Field(..., ge=0)
    unstable_entry_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


def bootstrap_effect_stability(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None = None,
    condition_b: str | None = None,
    n_resamples: int = 200,
    significance_threshold: float = 0.05,
    random_seed: int = 0,
    sample_run_policy: SampleRunAnalysisPolicy = (
        SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS
    ),
) -> BootstrapEffectStabilityReport:
    """Bootstrap one two-condition effect report over resampled biological observations."""

    from bijux_proteomics.quantification.differential_abundance import (
        build_differential_abundance_report,
    )

    base_report = build_differential_abundance_report(
        table,
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
        sample_run_policy=sample_run_policy,
    )
    active_design_entries = resolve_sample_run_analysis_entries(
        design_entries,
        policy=sample_run_policy,
    )
    _require_table_sample_ids(
        table,
        design_entries=active_design_entries,
        sample_run_policy=sample_run_policy,
    )
    design_by_sample = {
        entry.sample_id: entry for entry in active_design_entries
    }
    rng = np.random.default_rng(random_seed)
    condition_by_sample = _condition_lookup(active_design_entries)
    sample_ids_a = _sample_ids_for_condition(condition_by_sample, base_report.condition_a)
    sample_ids_b = _sample_ids_for_condition(condition_by_sample, base_report.condition_b)
    bootstrap_log2fc: dict[str, list[float]] = {
        entry.entity_id: [] for entry in base_report.entries
    }
    bootstrap_q_values: dict[str, list[float]] = {
        entry.entity_id: [] for entry in base_report.entries
    }

    for resample_index in range(n_resamples):
        resampled_sample_ids, resampled_design_entries = _bootstrap_resampled_design(
            rng=rng,
            sample_ids_a=sample_ids_a,
            sample_ids_b=sample_ids_b,
            condition_a=base_report.condition_a,
            condition_b=base_report.condition_b,
            design_by_sample=design_by_sample,
            resample_index=resample_index,
        )
        resampled_table = _bootstrap_resampled_table(
            table=table,
            resampled_sample_ids=resampled_sample_ids,
        )
        resampled_report = build_differential_abundance_report(
            resampled_table,
            resampled_design_entries,
            condition_a=base_report.condition_a,
            condition_b=base_report.condition_b,
            sample_run_policy=sample_run_policy,
        )
        adjusted_lookup = {
            entry.entity_id: float(entry.adjusted_p_value or entry.p_value)
            for entry in resampled_report.entries
        }
        for entry in resampled_report.entries:
            bootstrap_log2fc[entry.entity_id].append(float(entry.log2_fold_change))
            bootstrap_q_values[entry.entity_id].append(adjusted_lookup[entry.entity_id])

    entries = tuple(
        _build_bootstrap_effect_stability_entry(
            entity_id=entry.entity_id,
            log2_fold_changes=tuple(bootstrap_log2fc[entry.entity_id]),
            q_values=tuple(bootstrap_q_values[entry.entity_id]),
            significance_threshold=significance_threshold,
        )
        for entry in base_report.entries
    )
    return BootstrapEffectStabilityReport(
        condition_a=base_report.condition_a,
        condition_b=base_report.condition_b,
        n_resamples=n_resamples,
        significance_threshold=significance_threshold,
        entries=entries,
        stable_entry_count=sum(
            entry.robustness_tier is BootstrapEffectRobustnessTier.STABLE
            for entry in entries
        ),
        caution_entry_count=sum(
            entry.robustness_tier is BootstrapEffectRobustnessTier.CAUTION
            for entry in entries
        ),
        unstable_entry_count=sum(
            entry.robustness_tier is BootstrapEffectRobustnessTier.UNSTABLE
            for entry in entries
        ),
        note=(
            "bootstrap effect stability resamples biological observations within each "
            "condition and tracks fold-change direction plus adjusted-significance stability"
        ),
    )


def render_bootstrap_effect_stability_tsv(
    report: BootstrapEffectStabilityReport,
) -> str:
    """Render one bootstrap effect-stability report as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "median_log2fc",
            "sign_consistency",
            "q_value_stability",
            "robustness_tier",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.entity_id,
                entry.median_log2fc,
                entry.sign_consistency,
                entry.q_value_stability,
                entry.robustness_tier.value,
            )
        )
    return buffer.getvalue()


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
    for condition in sorted({condition for condition in condition_by_sample.values() if condition}):
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
                (result_entry.entity_id, result_entry.condition_a, result_entry.condition_b)
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
    for condition in sorted({condition for condition in condition_by_sample.values() if condition}):
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
    if entry.interaction_adjusted_p_value is not None or entry.interaction_p_value is not None:
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
        low_robustness_entry_count=sum(entry.robustness_score < 0.6 for entry in entries),
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
        if (
            cell.imputation_provenance is not None
            or (
                cell.value_provenance is not None
                and cell.value_provenance.value_origin is QuantValueOrigin.IMPUTED
            )
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
        peptides.update(
            contributor.canonical_peptide
            for contributor in cell.value_provenance.selected_contributors
            if contributor.canonical_peptide not in (None, "")
        )
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
    return round(sum(condition_scores) / len(condition_scores), 4) if condition_scores else 0.5


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
    return DifferentialResultRobustnessQcStatus.PASS, 1.0, ()


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
        return "result remains robust across effect, significance, support, and qc checks"
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


def _build_bootstrap_effect_stability_entry(
    *,
    entity_id: str,
    log2_fold_changes: tuple[float, ...],
    q_values: tuple[float, ...],
    significance_threshold: float,
) -> BootstrapEffectStabilityEntry:
    fold_change_array = np.array(log2_fold_changes, dtype=float)
    q_value_array = np.array(q_values, dtype=float)
    median_log2fc = float(np.median(fold_change_array))
    sign_consistency = _sign_consistency(
        fold_change_array,
        median_log2fc=median_log2fc,
    )
    q_value_stability = _q_value_stability(
        q_value_array,
        significance_threshold=significance_threshold,
    )
    robustness_tier = _bootstrap_robustness_tier(
        sign_consistency=sign_consistency,
        q_value_stability=q_value_stability,
    )
    return BootstrapEffectStabilityEntry(
        entity_id=entity_id,
        median_log2fc=round(median_log2fc, 6),
        sign_consistency=round(sign_consistency, 4),
        q_value_stability=round(q_value_stability, 4),
        robustness_tier=robustness_tier,
    )


def _sign_consistency(
    fold_changes: np.ndarray,
    *,
    median_log2fc: float,
    zero_tolerance: float = 1e-9,
) -> float:
    if fold_changes.size == 0:
        return 0.0
    if median_log2fc > zero_tolerance:
        return float(np.mean(fold_changes > zero_tolerance))
    if median_log2fc < -zero_tolerance:
        return float(np.mean(fold_changes < -zero_tolerance))
    return float(np.mean(np.abs(fold_changes) <= zero_tolerance))


def _q_value_stability(
    q_values: np.ndarray,
    *,
    significance_threshold: float,
) -> float:
    if q_values.size == 0:
        return 0.0
    significant_fraction = float(np.mean(q_values <= significance_threshold))
    return max(significant_fraction, 1.0 - significant_fraction)


def _bootstrap_robustness_tier(
    *,
    sign_consistency: float,
    q_value_stability: float,
) -> BootstrapEffectRobustnessTier:
    if sign_consistency < 0.75:
        return BootstrapEffectRobustnessTier.UNSTABLE
    if sign_consistency < 0.9 or q_value_stability < 0.8:
        return BootstrapEffectRobustnessTier.CAUTION
    return BootstrapEffectRobustnessTier.STABLE


def _bootstrap_resampled_design(
    *,
    rng: np.random.Generator,
    sample_ids_a: tuple[str, ...],
    sample_ids_b: tuple[str, ...],
    condition_a: str,
    condition_b: str,
    design_by_sample: dict[str, ExperimentalDesignEntry],
    resample_index: int,
) -> tuple[tuple[tuple[str, str], ...], tuple[ExperimentalDesignEntry, ...]]:
    sampled_pairs: list[tuple[str, str]] = []
    sampled_entries: list[ExperimentalDesignEntry] = []
    for condition, source_sample_ids in (
        (condition_a, sample_ids_a),
        (condition_b, sample_ids_b),
    ):
        drawn_indices = rng.integers(
            0,
            len(source_sample_ids),
            size=len(source_sample_ids),
        )
        for draw_index, source_index in enumerate(drawn_indices, start=1):
            source_sample_id = source_sample_ids[int(source_index)]
            resampled_sample_id = (
                f"{condition}__bootstrap_{resample_index:04d}_{draw_index:02d}"
            )
            sampled_pairs.append((resampled_sample_id, source_sample_id))
            source_entry = design_by_sample[source_sample_id]
            sampled_entries.append(
                source_entry.model_copy(
                    update={
                        "sample_id": resampled_sample_id,
                        "replicate": draw_index,
                        "metadata": {
                            **source_entry.metadata,
                            "bootstrap_source_sample_id": source_sample_id,
                            "bootstrap_iteration": str(resample_index),
                        },
                    }
                )
            )
    return tuple(sampled_pairs), tuple(sampled_entries)


def _bootstrap_resampled_table(
    *,
    table: LabelFreeQuantTable,
    resampled_sample_ids: tuple[tuple[str, str], ...],
) -> LabelFreeQuantTable:
    lookup = _matrix_value_index(table)
    values: list[QuantValue] = []
    normalization_factors: dict[str, float] = {}
    for resampled_sample_id, source_sample_id in resampled_sample_ids:
        normalization_factors[resampled_sample_id] = table.normalization_factors.get(
            source_sample_id,
            1.0,
        )
        for entity_id in table.entity_ids:
            cell = lookup.get((entity_id, source_sample_id))
            if cell is None:
                values.append(
                    QuantValue(
                        sample_id=resampled_sample_id,
                        entity_id=entity_id,
                        abundance=None,
                        missing_value_kind=MissingValueKind.NOT_OBSERVED,
                        source_feature_count=0,
                    )
                )
                continue
            values.append(cell.model_copy(update={"sample_id": resampled_sample_id}))
    return LabelFreeQuantTable(
        entity_level=table.entity_level,
        measure_kind=table.measure_kind,
        aggregation_method=table.aggregation_method,
        normalization_method=table.normalization_method,
        imputation_method=table.imputation_method,
        sample_ids=tuple(resampled_sample_id for resampled_sample_id, _ in resampled_sample_ids),
        entity_ids=table.entity_ids,
        values=tuple(values),
        normalization_factors=normalization_factors,
        entity_protein_refs=table.entity_protein_refs,
        entity_member_peptides=table.entity_member_peptides,
    )


def _require_table_sample_ids(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    sample_run_policy: SampleRunAnalysisPolicy,
) -> None:
    missing_sample_ids = tuple(
        sorted(
            {
                entry.sample_id
                for entry in design_entries
                if entry.sample_id not in table.sample_ids
            }
        )
    )
    if not missing_sample_ids:
        return
    raise ValueError(
        "quantification table sample ids do not cover the resolved analysis design "
        f"for sample/run policy {sample_run_policy.value!r}; missing sample ids: "
        + ", ".join(missing_sample_ids)
    )


def _sample_ids_for_condition(
    condition_by_sample: dict[str, str],
    condition: str,
) -> tuple[str, ...]:
    return tuple(
        sample_id
        for sample_id, sample_condition in condition_by_sample.items()
        if sample_condition == condition
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
