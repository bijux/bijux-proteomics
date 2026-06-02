# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Cross-study effect-size meta-analysis over owned study-result surfaces."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from enum import StrEnum
from io import StringIO
import math
from pathlib import Path
import re

from pydantic import ConfigDict, Field

from bijux_proteomics.workflow.cross_study_effect_comparison import (
    CrossStudyEffectContrastAlignmentStatus,
    CrossStudyEffectDirection,
    CrossStudyProteinEffectComparisonEntry,
    CrossStudyEffectUnsupportedStudy,
    CrossStudyProteinEffectComparisonReport,
    CrossStudyProteinEffectObservation,
    CrossStudyProteinEffectStudyEntry,
    build_cross_study_effect_comparison_report,
    build_cross_study_effect_comparison_report_from_observations,
)
from bijux_proteomics.workflow.cross_study_protein_harmonization import (
    CrossStudyProteinStudyInput,
)
from bijux_proteomics.workflow.study_result import ProteomicsStudyKind
from bijux_proteomics_foundation import JsonModel


class CrossStudyMetaAnalysisEffectModel(StrEnum):
    """Effect models preserved on one cross-study meta-analysis result."""

    FIXED_INVERSE_VARIANCE = "fixed_inverse_variance"
    RANDOM_EFFECTS = "random_effects"


class CrossStudyMetaAnalysisHeterogeneityTier(StrEnum):
    """Stable heterogeneity tiers over one meta-analysis group."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class CrossStudyMetaAnalysisRejectionReason(StrEnum):
    """Stable reasons why one harmonized group cannot be meta-analyzed."""

    HETEROGENEOUS_CONTRASTS = "heterogeneous_contrasts"
    INSUFFICIENT_STUDIES = "insufficient_studies"
    MISSING_STANDARD_ERROR = "missing_standard_error"
    NONPOSITIVE_STANDARD_ERROR = "nonpositive_standard_error"
    MIXED_SPECIES_GROUP = "mixed_species_group"


class CrossStudyMetaAnalysisPolicy(JsonModel):
    """Policy controlling cross-study effect-size aggregation."""

    model_config = ConfigDict(extra="forbid")

    minimum_study_count: int = Field(default=2, ge=2)
    allow_cross_species: bool = False
    prefer_random_effects_i_squared_threshold: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
    )


class CrossStudyMetaAnalysisStudyWeightEntry(JsonModel):
    """One study-specific weight contribution to one meta-analysis group."""

    model_config = ConfigDict(extra="forbid")

    harmonized_id: str = Field(..., min_length=1)
    study_id: str = Field(..., min_length=1)
    study_label: str | None = None
    study_kind: ProteomicsStudyKind
    species: str | None = None
    normalized_direction: CrossStudyEffectDirection
    normalized_log2_fold_change: float
    standard_error: float = Field(..., gt=0.0)
    variance: float = Field(..., gt=0.0)
    fixed_weight: float = Field(..., gt=0.0)
    fixed_weight_fraction: float = Field(..., ge=0.0, le=1.0)
    random_weight: float = Field(..., gt=0.0)
    random_weight_fraction: float = Field(..., ge=0.0, le=1.0)
    significant: bool = False
    note: str = Field(..., min_length=1)


class CrossStudyMetaAnalysisEntry(JsonModel):
    """One combined cross-study effect-size result over one harmonized protein."""

    model_config = ConfigDict(extra="forbid")

    meta_analysis_id: str = Field(..., min_length=1)
    harmonized_id: str = Field(..., min_length=1)
    representative_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    study_ids: tuple[str, ...] = Field(default_factory=tuple)
    study_kinds: tuple[ProteomicsStudyKind, ...] = Field(default_factory=tuple)
    species: tuple[str, ...] = Field(default_factory=tuple)
    anchor_condition_a: str = Field(..., min_length=1)
    anchor_condition_b: str = Field(..., min_length=1)
    included_study_count: int = Field(..., ge=0)
    effect_model: CrossStudyMetaAnalysisEffectModel
    combined_log2_fold_change: float
    combined_standard_error: float = Field(..., gt=0.0)
    combined_confidence_interval_low: float
    combined_confidence_interval_high: float
    combined_p_value: float = Field(..., ge=0.0, le=1.0)
    combined_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    fixed_effect_log2_fold_change: float
    fixed_effect_standard_error: float = Field(..., gt=0.0)
    fixed_effect_confidence_interval_low: float
    fixed_effect_confidence_interval_high: float
    fixed_effect_p_value: float = Field(..., ge=0.0, le=1.0)
    random_effect_log2_fold_change: float
    random_effect_standard_error: float = Field(..., gt=0.0)
    random_effect_confidence_interval_low: float
    random_effect_confidence_interval_high: float
    random_effect_p_value: float = Field(..., ge=0.0, le=1.0)
    heterogeneity_q: float = Field(..., ge=0.0)
    heterogeneity_degrees_of_freedom: int = Field(..., ge=0)
    heterogeneity_i_squared: float = Field(..., ge=0.0, le=1.0)
    between_study_variance_tau_squared: float = Field(..., ge=0.0)
    heterogeneity_tier: CrossStudyMetaAnalysisHeterogeneityTier
    direction_conflict: bool = False
    conflicting_study_ids: tuple[str, ...] = Field(default_factory=tuple)
    low_robustness_study_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class CrossStudyMetaAnalysisRejectedEntry(JsonModel):
    """One harmonized protein group rejected from meta-analysis."""

    model_config = ConfigDict(extra="forbid")

    rejection_id: str = Field(..., min_length=1)
    harmonized_id: str = Field(..., min_length=1)
    representative_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    study_ids: tuple[str, ...] = Field(default_factory=tuple)
    study_kinds: tuple[ProteomicsStudyKind, ...] = Field(default_factory=tuple)
    species: tuple[str, ...] = Field(default_factory=tuple)
    tested_study_count: int = Field(..., ge=0)
    rejection_reason: CrossStudyMetaAnalysisRejectionReason
    note: str = Field(..., min_length=1)


class CrossStudyMetaAnalysisSummary(JsonModel):
    """Summary over one cross-study meta-analysis pass."""

    model_config = ConfigDict(extra="forbid")

    input_study_count: int = Field(..., ge=0)
    supported_study_count: int = Field(..., ge=0)
    unsupported_study_count: int = Field(..., ge=0)
    effect_observation_count: int = Field(..., ge=0)
    harmonized_group_count: int = Field(..., ge=0)
    combined_entry_count: int = Field(..., ge=0)
    rejected_group_count: int = Field(..., ge=0)
    fixed_model_count: int = Field(..., ge=0)
    random_model_count: int = Field(..., ge=0)
    conflict_flag_count: int = Field(..., ge=0)
    high_heterogeneity_count: int = Field(..., ge=0)


class CrossStudyMetaAnalysisReport(JsonModel):
    """Owned report over cross-study inverse-variance meta-analysis."""

    model_config = ConfigDict(extra="forbid")

    comparison_report: CrossStudyProteinEffectComparisonReport
    combined_entries: tuple[CrossStudyMetaAnalysisEntry, ...] = Field(
        default_factory=tuple
    )
    study_weight_entries: tuple[CrossStudyMetaAnalysisStudyWeightEntry, ...] = Field(
        default_factory=tuple
    )
    rejected_entries: tuple[CrossStudyMetaAnalysisRejectedEntry, ...] = Field(
        default_factory=tuple
    )
    summary: CrossStudyMetaAnalysisSummary
    note: str = Field(..., min_length=1)


def build_cross_study_meta_analysis_report(
    studies: tuple[CrossStudyProteinStudyInput, ...],
    *,
    ortholog_records: tuple = (),
    significance_threshold: float = 0.05,
    low_robustness_threshold: float = 0.5,
    policy: CrossStudyMetaAnalysisPolicy | None = None,
) -> CrossStudyMetaAnalysisReport:
    """Combine compatible study effects by inverse-variance meta-analysis."""

    comparison_report = build_cross_study_effect_comparison_report(
        studies,
        ortholog_records=ortholog_records,
        significance_threshold=significance_threshold,
        low_robustness_threshold=low_robustness_threshold,
    )
    return build_cross_study_meta_analysis_report_from_comparison(
        comparison_report,
        policy=policy,
    )


def build_cross_study_meta_analysis_report_from_observations(
    observations: tuple[CrossStudyProteinEffectObservation, ...],
    *,
    unsupported_studies: tuple[CrossStudyEffectUnsupportedStudy, ...] = (),
    ortholog_records: tuple = (),
    input_study_count: int | None = None,
    significance_threshold: float = 0.05,
    low_robustness_threshold: float = 0.5,
    policy: CrossStudyMetaAnalysisPolicy | None = None,
) -> CrossStudyMetaAnalysisReport:
    """Combine compatible observed study effects by inverse-variance meta-analysis."""

    comparison_report = build_cross_study_effect_comparison_report_from_observations(
        observations,
        unsupported_studies=unsupported_studies,
        ortholog_records=ortholog_records,
        input_study_count=input_study_count,
        significance_threshold=significance_threshold,
        low_robustness_threshold=low_robustness_threshold,
    )
    return build_cross_study_meta_analysis_report_from_comparison(
        comparison_report,
        policy=policy,
    )


def build_cross_study_meta_analysis_report_from_comparison(
    comparison_report: CrossStudyProteinEffectComparisonReport,
    *,
    policy: CrossStudyMetaAnalysisPolicy | None = None,
) -> CrossStudyMetaAnalysisReport:
    """Combine compatible comparison groups from one cross-study effect comparison."""

    active_policy = policy or CrossStudyMetaAnalysisPolicy()
    entries_by_harmonized_id: dict[str, list[CrossStudyProteinEffectStudyEntry]] = {}
    for entry in comparison_report.study_entries:
        entries_by_harmonized_id.setdefault(entry.harmonized_id, []).append(entry)

    combined_entries: list[CrossStudyMetaAnalysisEntry] = []
    weight_entries: list[CrossStudyMetaAnalysisStudyWeightEntry] = []
    rejected_entries: list[CrossStudyMetaAnalysisRejectedEntry] = []
    for comparison in sorted(
        comparison_report.comparisons,
        key=lambda entry: entry.harmonized_id,
    ):
        raw_study_entries = tuple(
            sorted(
                entries_by_harmonized_id.get(comparison.harmonized_id, []),
                key=lambda entry: (entry.study_id, entry.observation_id),
            )
        )
        study_entries = _normalize_study_entries_to_comparison_anchor(
            raw_study_entries,
            comparison=comparison,
        )
        rejection = _meta_analysis_rejection(
            comparison=comparison,
            study_entries=study_entries,
            policy=active_policy,
        )
        if rejection is not None:
            rejected_entries.append(rejection)
            continue
        meta_entry, meta_weights = _build_meta_analysis_entry(
            comparison=comparison,
            study_entries=study_entries,
            policy=active_policy,
        )
        combined_entries.append(meta_entry)
        weight_entries.extend(meta_weights)

    adjusted_p_values = _apply_benjamini_hochberg(
        [entry.combined_p_value for entry in combined_entries]
    )
    combined_entries = [
        entry.model_copy(update={"combined_adjusted_p_value": adjusted_p_value})
        for entry, adjusted_p_value in zip(
            combined_entries,
            adjusted_p_values,
            strict=True,
        )
    ]
    ordered_combined_entries = tuple(
        sorted(
            combined_entries,
            key=lambda entry: (
                entry.combined_adjusted_p_value
                if entry.combined_adjusted_p_value is not None
                else 1.0,
                -abs(entry.combined_log2_fold_change),
                entry.harmonized_id,
            ),
        )
    )
    ordered_weight_entries = tuple(
        sorted(
            weight_entries,
            key=lambda entry: (
                entry.harmonized_id,
                -entry.fixed_weight_fraction,
                entry.study_id,
            ),
        )
    )
    ordered_rejections = tuple(
        sorted(
            rejected_entries,
            key=lambda entry: (
                entry.rejection_reason.value,
                entry.harmonized_id,
            ),
        )
    )
    summary = CrossStudyMetaAnalysisSummary(
        input_study_count=comparison_report.summary.input_study_count,
        supported_study_count=comparison_report.summary.supported_study_count,
        unsupported_study_count=comparison_report.summary.unsupported_study_count,
        effect_observation_count=comparison_report.summary.effect_observation_count,
        harmonized_group_count=comparison_report.summary.harmonized_group_count,
        combined_entry_count=len(ordered_combined_entries),
        rejected_group_count=len(ordered_rejections),
        fixed_model_count=sum(
            entry.effect_model is CrossStudyMetaAnalysisEffectModel.FIXED_INVERSE_VARIANCE
            for entry in ordered_combined_entries
        ),
        random_model_count=sum(
            entry.effect_model is CrossStudyMetaAnalysisEffectModel.RANDOM_EFFECTS
            for entry in ordered_combined_entries
        ),
        conflict_flag_count=sum(entry.direction_conflict for entry in ordered_combined_entries),
        high_heterogeneity_count=sum(
            entry.heterogeneity_tier is CrossStudyMetaAnalysisHeterogeneityTier.HIGH
            for entry in ordered_combined_entries
        ),
    )
    return CrossStudyMetaAnalysisReport(
        comparison_report=comparison_report,
        combined_entries=ordered_combined_entries,
        study_weight_entries=ordered_weight_entries,
        rejected_entries=ordered_rejections,
        summary=summary,
        note=(
            "cross-study meta-analysis combines normalized study effects by "
            "inverse-variance weighting, preserves per-study weights and heterogeneity, "
            "and rejects incompatible groups instead of averaging p-values"
        ),
    )


def render_cross_study_meta_analysis_tsv(report: CrossStudyMetaAnalysisReport) -> str:
    """Render one cross-study meta-analysis summary table as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "meta_analysis_id",
            "harmonized_id",
            "representative_protein_refs",
            "study_ids",
            "study_kinds",
            "species",
            "anchor_condition_a",
            "anchor_condition_b",
            "included_study_count",
            "effect_model",
            "combined_log2_fold_change",
            "combined_standard_error",
            "combined_confidence_interval_low",
            "combined_confidence_interval_high",
            "combined_p_value",
            "combined_adjusted_p_value",
            "fixed_effect_log2_fold_change",
            "fixed_effect_standard_error",
            "fixed_effect_p_value",
            "random_effect_log2_fold_change",
            "random_effect_standard_error",
            "random_effect_p_value",
            "heterogeneity_q",
            "heterogeneity_degrees_of_freedom",
            "heterogeneity_i_squared",
            "between_study_variance_tau_squared",
            "heterogeneity_tier",
            "direction_conflict",
            "conflicting_study_ids",
            "low_robustness_study_ids",
            "note",
        ]
    )
    for entry in report.combined_entries:
        writer.writerow(
            [
                entry.meta_analysis_id,
                entry.harmonized_id,
                ";".join(entry.representative_protein_refs),
                ";".join(entry.study_ids),
                ";".join(kind.value for kind in entry.study_kinds),
                ";".join(entry.species),
                entry.anchor_condition_a,
                entry.anchor_condition_b,
                entry.included_study_count,
                entry.effect_model.value,
                _format_float(entry.combined_log2_fold_change),
                _format_float(entry.combined_standard_error),
                _format_float(entry.combined_confidence_interval_low),
                _format_float(entry.combined_confidence_interval_high),
                _format_float(entry.combined_p_value),
                _format_float(entry.combined_adjusted_p_value),
                _format_float(entry.fixed_effect_log2_fold_change),
                _format_float(entry.fixed_effect_standard_error),
                _format_float(entry.fixed_effect_p_value),
                _format_float(entry.random_effect_log2_fold_change),
                _format_float(entry.random_effect_standard_error),
                _format_float(entry.random_effect_p_value),
                _format_float(entry.heterogeneity_q),
                entry.heterogeneity_degrees_of_freedom,
                _format_float(entry.heterogeneity_i_squared),
                _format_float(entry.between_study_variance_tau_squared),
                entry.heterogeneity_tier.value,
                str(entry.direction_conflict).lower(),
                ";".join(entry.conflicting_study_ids),
                ";".join(entry.low_robustness_study_ids),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_cross_study_meta_analysis_study_weight_tsv(
    report: CrossStudyMetaAnalysisReport,
) -> str:
    """Render per-study meta-analysis weights as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "harmonized_id",
            "study_id",
            "study_label",
            "study_kind",
            "species",
            "normalized_direction",
            "normalized_log2_fold_change",
            "standard_error",
            "variance",
            "fixed_weight",
            "fixed_weight_fraction",
            "random_weight",
            "random_weight_fraction",
            "significant",
            "note",
        ]
    )
    for entry in report.study_weight_entries:
        writer.writerow(
            [
                entry.harmonized_id,
                entry.study_id,
                "" if entry.study_label is None else entry.study_label,
                entry.study_kind.value,
                "" if entry.species is None else entry.species,
                entry.normalized_direction.value,
                _format_float(entry.normalized_log2_fold_change),
                _format_float(entry.standard_error),
                _format_float(entry.variance),
                _format_float(entry.fixed_weight),
                _format_float(entry.fixed_weight_fraction),
                _format_float(entry.random_weight),
                _format_float(entry.random_weight_fraction),
                str(entry.significant).lower(),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_cross_study_meta_analysis_rejected_tsv(
    report: CrossStudyMetaAnalysisReport,
) -> str:
    """Render rejected meta-analysis groups as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "rejection_id",
            "harmonized_id",
            "representative_protein_refs",
            "study_ids",
            "study_kinds",
            "species",
            "tested_study_count",
            "rejection_reason",
            "note",
        ]
    )
    for entry in report.rejected_entries:
        writer.writerow(
            [
                entry.rejection_id,
                entry.harmonized_id,
                ";".join(entry.representative_protein_refs),
                ";".join(entry.study_ids),
                ";".join(kind.value for kind in entry.study_kinds),
                ";".join(entry.species),
                entry.tested_study_count,
                entry.rejection_reason.value,
                entry.note,
            ]
        )
    return buffer.getvalue()


def export_cross_study_meta_analysis_tsv(
    report: CrossStudyMetaAnalysisReport,
    path: Path,
) -> None:
    """Write combined meta-analysis entries to TSV."""

    write_output_table_tsv(path, render_cross_study_meta_analysis_tsv(report))


def export_cross_study_meta_analysis_study_weight_tsv(
    report: CrossStudyMetaAnalysisReport,
    path: Path,
) -> None:
    """Write per-study meta-analysis weights to TSV."""

    write_output_table_tsv(path, render_cross_study_meta_analysis_study_weight_tsv(report))


def export_cross_study_meta_analysis_rejected_tsv(
    report: CrossStudyMetaAnalysisReport,
    path: Path,
) -> None:
    """Write rejected meta-analysis groups to TSV."""

    write_output_table_tsv(path, render_cross_study_meta_analysis_rejected_tsv(report))


def _meta_analysis_rejection(
    *,
    comparison: CrossStudyProteinEffectComparisonEntry,
    study_entries: tuple[CrossStudyProteinEffectStudyEntry, ...],
    policy: CrossStudyMetaAnalysisPolicy,
) -> CrossStudyMetaAnalysisRejectedEntry | None:
    species = tuple(
        sorted({entry.species for entry in study_entries if entry.species is not None})
    )
    if (
        comparison.contrast_alignment_status
        is CrossStudyEffectContrastAlignmentStatus.HETEROGENEOUS_CONTRASTS
    ):
        return _rejected_entry(
            comparison=comparison,
            study_entries=study_entries,
            reason=CrossStudyMetaAnalysisRejectionReason.HETEROGENEOUS_CONTRASTS,
            note=(
                "meta-analysis rejected this harmonized group because study contrasts "
                "could not be normalized onto one shared comparison direction"
            ),
            species=species,
        )
    if len(study_entries) < policy.minimum_study_count:
        return _rejected_entry(
            comparison=comparison,
            study_entries=study_entries,
            reason=CrossStudyMetaAnalysisRejectionReason.INSUFFICIENT_STUDIES,
            note=(
                "meta-analysis requires at least "
                f"{policy.minimum_study_count} compatible studies per harmonized group"
            ),
            species=species,
        )
    if not policy.allow_cross_species and len(species) > 1:
        return _rejected_entry(
            comparison=comparison,
            study_entries=study_entries,
            reason=CrossStudyMetaAnalysisRejectionReason.MIXED_SPECIES_GROUP,
            note=(
                "meta-analysis rejected this harmonized group because it spans more "
                "than one species without explicit cross-species allowance"
            ),
            species=species,
        )
    if any(entry.normalized_log2_fold_change is None for entry in study_entries):
        return _rejected_entry(
            comparison=comparison,
            study_entries=study_entries,
            reason=CrossStudyMetaAnalysisRejectionReason.HETEROGENEOUS_CONTRASTS,
            note=(
                "meta-analysis rejected this harmonized group because one or more "
                "study effects could not be normalized onto the anchor contrast"
            ),
            species=species,
        )
    if any(entry.standard_error is None for entry in study_entries):
        return _rejected_entry(
            comparison=comparison,
            study_entries=study_entries,
            reason=CrossStudyMetaAnalysisRejectionReason.MISSING_STANDARD_ERROR,
            note=(
                "meta-analysis rejected this harmonized group because one or more "
                "study effects do not preserve the uncertainty needed for inverse-variance weighting"
            ),
            species=species,
        )
    if any(
        entry.standard_error is not None and entry.standard_error <= 0.0
        for entry in study_entries
    ):
        return _rejected_entry(
            comparison=comparison,
            study_entries=study_entries,
            reason=CrossStudyMetaAnalysisRejectionReason.NONPOSITIVE_STANDARD_ERROR,
            note=(
                "meta-analysis rejected this harmonized group because at least one "
                "study effect carries a nonpositive standard error"
            ),
            species=species,
        )
    return None


def _normalize_study_entries_to_comparison_anchor(
    study_entries: tuple[CrossStudyProteinEffectStudyEntry, ...],
    *,
    comparison: CrossStudyProteinEffectComparisonEntry,
) -> tuple[CrossStudyProteinEffectStudyEntry, ...]:
    anchor_condition_a = comparison.anchor_condition_a
    anchor_condition_b = comparison.anchor_condition_b
    if anchor_condition_a is None or anchor_condition_b is None:
        return tuple(
            entry.model_copy(
                update={
                    "normalized_log2_fold_change": None,
                    "normalized_direction": None,
                }
            )
            for entry in study_entries
        )

    normalized_entries: list[CrossStudyProteinEffectStudyEntry] = []
    for entry in study_entries:
        if entry.condition_a == anchor_condition_a and entry.condition_b == anchor_condition_b:
            normalized_entries.append(
                entry.model_copy(
                    update={
                        "normalized_log2_fold_change": entry.log2_fold_change,
                        "normalized_direction": entry.direction,
                    }
                )
            )
            continue
        if entry.condition_a == anchor_condition_b and entry.condition_b == anchor_condition_a:
            normalized_log2_fold_change = -entry.log2_fold_change
            normalized_entries.append(
                entry.model_copy(
                    update={
                        "normalized_log2_fold_change": normalized_log2_fold_change,
                        "normalized_direction": _direction_from_log2_fold_change(
                            normalized_log2_fold_change
                        ),
                    }
                )
            )
            continue
        return tuple(
            entry.model_copy(
                update={
                    "normalized_log2_fold_change": None,
                    "normalized_direction": None,
                }
            )
            for entry in study_entries
        )
    return tuple(normalized_entries)


def _build_meta_analysis_entry(
    *,
    comparison: CrossStudyProteinEffectComparisonEntry,
    study_entries: tuple[CrossStudyProteinEffectStudyEntry, ...],
    policy: CrossStudyMetaAnalysisPolicy,
) -> tuple[CrossStudyMetaAnalysisEntry, list[CrossStudyMetaAnalysisStudyWeightEntry]]:
    normalized_effects = [entry.normalized_log2_fold_change for entry in study_entries]
    if any(value is None for value in normalized_effects):
        raise RuntimeError(
            "cross-study meta-analysis requires normalized effect sizes for every study entry"
        )
    effects = [float(value) for value in normalized_effects if value is not None]
    standard_errors = [
        float(entry.standard_error)
        for entry in study_entries
        if entry.standard_error is not None
    ]
    variances = [value * value for value in standard_errors]
    fixed_weights = [1.0 / variance for variance in variances]
    fixed_weight_total = sum(fixed_weights)
    fixed_effect = sum(
        weight * effect for weight, effect in zip(fixed_weights, effects, strict=True)
    ) / fixed_weight_total
    fixed_standard_error = math.sqrt(1.0 / fixed_weight_total)
    q_statistic = sum(
        weight * ((effect - fixed_effect) ** 2)
        for weight, effect in zip(fixed_weights, effects, strict=True)
    )
    degrees_of_freedom = max(len(study_entries) - 1, 0)
    fixed_weight_square_total = sum(weight * weight for weight in fixed_weights)
    c_value = fixed_weight_total - (fixed_weight_square_total / fixed_weight_total)
    tau_squared = (
        max(0.0, (q_statistic - degrees_of_freedom) / c_value)
        if c_value > 0.0 and degrees_of_freedom > 0
        else 0.0
    )
    random_weights = [1.0 / (variance + tau_squared) for variance in variances]
    random_weight_total = sum(random_weights)
    random_effect = sum(
        weight * effect for weight, effect in zip(random_weights, effects, strict=True)
    ) / random_weight_total
    random_standard_error = math.sqrt(1.0 / random_weight_total)
    i_squared = (
        max(0.0, (q_statistic - degrees_of_freedom) / q_statistic)
        if q_statistic > 0.0 and degrees_of_freedom > 0
        else 0.0
    )
    heterogeneity_tier = _heterogeneity_tier(i_squared)
    effect_model = (
        CrossStudyMetaAnalysisEffectModel.RANDOM_EFFECTS
        if i_squared >= policy.prefer_random_effects_i_squared_threshold
        else CrossStudyMetaAnalysisEffectModel.FIXED_INVERSE_VARIANCE
    )
    if effect_model is CrossStudyMetaAnalysisEffectModel.RANDOM_EFFECTS:
        combined_effect = random_effect
        combined_standard_error = random_standard_error
    else:
        combined_effect = fixed_effect
        combined_standard_error = fixed_standard_error
    combined_interval_low, combined_interval_high = _confidence_interval(
        combined_effect,
        combined_standard_error,
    )
    fixed_interval_low, fixed_interval_high = _confidence_interval(
        fixed_effect,
        fixed_standard_error,
    )
    random_interval_low, random_interval_high = _confidence_interval(
        random_effect,
        random_standard_error,
    )
    combined_p_value = _two_sided_normal_p_value(
        combined_effect,
        combined_standard_error,
    )
    fixed_p_value = _two_sided_normal_p_value(
        fixed_effect,
        fixed_standard_error,
    )
    random_p_value = _two_sided_normal_p_value(
        random_effect,
        random_standard_error,
    )
    fixed_weight_fractions = [weight / fixed_weight_total for weight in fixed_weights]
    random_weight_fractions = [weight / random_weight_total for weight in random_weights]
    weight_entries = [
        CrossStudyMetaAnalysisStudyWeightEntry(
            harmonized_id=comparison.harmonized_id,
            study_id=entry.study_id,
            study_label=entry.study_label,
            study_kind=entry.study_kind,
            species=entry.species,
            normalized_direction=(
                entry.normalized_direction or CrossStudyEffectDirection.FLAT
            ),
            normalized_log2_fold_change=entry.normalized_log2_fold_change or 0.0,
            standard_error=standard_error,
            variance=variance,
            fixed_weight=fixed_weight,
            fixed_weight_fraction=fixed_fraction,
            random_weight=random_weight,
            random_weight_fraction=random_fraction,
            significant=entry.significant,
            note="study contributes inverse-variance weights to the combined effect",
        )
        for (
            entry,
            standard_error,
            variance,
            fixed_weight,
            fixed_fraction,
            random_weight,
            random_fraction,
        ) in zip(
            study_entries,
            standard_errors,
            variances,
            fixed_weights,
            fixed_weight_fractions,
            random_weights,
            random_weight_fractions,
            strict=True,
        )
    ]
    species = tuple(
        sorted({entry.species for entry in study_entries if entry.species is not None})
    )
    conflict_study_ids = tuple(
        sorted(
            entry.study_id
            for entry in study_entries
            if entry.normalized_direction in {
                CrossStudyEffectDirection.UP,
                CrossStudyEffectDirection.DOWN,
            }
        )
    )
    direction_conflict = comparison.conflicting_hit or len(
        {
            entry.normalized_direction
            for entry in study_entries
            if entry.normalized_direction in {
                CrossStudyEffectDirection.UP,
                CrossStudyEffectDirection.DOWN,
            }
        }
    ) > 1
    entry = CrossStudyMetaAnalysisEntry(
        meta_analysis_id=_meta_analysis_id(comparison.harmonized_id),
        harmonized_id=comparison.harmonized_id,
        representative_protein_refs=comparison.representative_protein_refs,
        study_ids=comparison.study_ids,
        study_kinds=comparison.study_kinds,
        species=species,
        anchor_condition_a=comparison.anchor_condition_a or "",
        anchor_condition_b=comparison.anchor_condition_b or "",
        included_study_count=len(study_entries),
        effect_model=effect_model,
        combined_log2_fold_change=combined_effect,
        combined_standard_error=combined_standard_error,
        combined_confidence_interval_low=combined_interval_low,
        combined_confidence_interval_high=combined_interval_high,
        combined_p_value=combined_p_value,
        combined_adjusted_p_value=None,
        fixed_effect_log2_fold_change=fixed_effect,
        fixed_effect_standard_error=fixed_standard_error,
        fixed_effect_confidence_interval_low=fixed_interval_low,
        fixed_effect_confidence_interval_high=fixed_interval_high,
        fixed_effect_p_value=fixed_p_value,
        random_effect_log2_fold_change=random_effect,
        random_effect_standard_error=random_standard_error,
        random_effect_confidence_interval_low=random_interval_low,
        random_effect_confidence_interval_high=random_interval_high,
        random_effect_p_value=random_p_value,
        heterogeneity_q=q_statistic,
        heterogeneity_degrees_of_freedom=degrees_of_freedom,
        heterogeneity_i_squared=i_squared,
        between_study_variance_tau_squared=tau_squared,
        heterogeneity_tier=heterogeneity_tier,
        direction_conflict=direction_conflict,
        conflicting_study_ids=conflict_study_ids if direction_conflict else (),
        low_robustness_study_ids=comparison.low_robustness_study_ids,
        note=(
            "meta-analysis combined normalized study effects by inverse-variance "
            "weighting and preserved heterogeneity plus conflict flags explicitly"
        ),
    )
    return entry, weight_entries


def _rejected_entry(
    *,
    comparison: CrossStudyProteinEffectComparisonEntry,
    study_entries: tuple[CrossStudyProteinEffectStudyEntry, ...],
    reason: CrossStudyMetaAnalysisRejectionReason,
    note: str,
    species: tuple[str, ...],
) -> CrossStudyMetaAnalysisRejectedEntry:
    return CrossStudyMetaAnalysisRejectedEntry(
        rejection_id=_rejection_id(comparison.harmonized_id, reason),
        harmonized_id=comparison.harmonized_id,
        representative_protein_refs=comparison.representative_protein_refs,
        study_ids=comparison.study_ids,
        study_kinds=comparison.study_kinds,
        species=species,
        tested_study_count=len(study_entries),
        rejection_reason=reason,
        note=note,
    )


def _apply_benjamini_hochberg(p_values: list[float]) -> list[float]:
    total = len(p_values)
    if total == 0:
        return []
    order = sorted(range(total), key=lambda index: p_values[index])
    adjusted = [1.0] * total
    running_minimum = 1.0
    for reverse_rank, index in enumerate(reversed(order), start=1):
        rank = total - reverse_rank + 1
        candidate = p_values[index] * total / rank
        running_minimum = min(running_minimum, candidate)
        adjusted[index] = min(1.0, running_minimum)
    return adjusted


def _confidence_interval(effect: float, standard_error: float) -> tuple[float, float]:
    radius = 1.96 * standard_error
    return effect - radius, effect + radius


def _two_sided_normal_p_value(effect: float, standard_error: float) -> float:
    z_score = effect / standard_error
    return math.erfc(abs(z_score) / math.sqrt(2.0))


def _heterogeneity_tier(i_squared: float) -> CrossStudyMetaAnalysisHeterogeneityTier:
    if i_squared >= 0.5:
        return CrossStudyMetaAnalysisHeterogeneityTier.HIGH
    if i_squared >= 0.25:
        return CrossStudyMetaAnalysisHeterogeneityTier.MODERATE
    return CrossStudyMetaAnalysisHeterogeneityTier.LOW


def _direction_from_log2_fold_change(value: float) -> CrossStudyEffectDirection:
    if value > 0.0:
        return CrossStudyEffectDirection.UP
    if value < 0.0:
        return CrossStudyEffectDirection.DOWN
    return CrossStudyEffectDirection.FLAT


def _meta_analysis_id(harmonized_id: str) -> str:
    return f"meta_analysis_{_stable_token(harmonized_id)}"


def _rejection_id(
    harmonized_id: str,
    reason: CrossStudyMetaAnalysisRejectionReason,
) -> str:
    return f"meta_analysis_rejection_{_stable_token(harmonized_id)}_{reason.value}"


def _stable_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return token or "unspecified"


def _format_float(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


__all__ = [
    "CrossStudyMetaAnalysisEffectModel",
    "CrossStudyMetaAnalysisEntry",
    "CrossStudyMetaAnalysisHeterogeneityTier",
    "CrossStudyMetaAnalysisPolicy",
    "CrossStudyMetaAnalysisRejectedEntry",
    "CrossStudyMetaAnalysisRejectionReason",
    "CrossStudyMetaAnalysisReport",
    "CrossStudyMetaAnalysisStudyWeightEntry",
    "CrossStudyMetaAnalysisSummary",
    "build_cross_study_meta_analysis_report",
    "build_cross_study_meta_analysis_report_from_comparison",
    "build_cross_study_meta_analysis_report_from_observations",
    "export_cross_study_meta_analysis_rejected_tsv",
    "export_cross_study_meta_analysis_study_weight_tsv",
    "export_cross_study_meta_analysis_tsv",
    "render_cross_study_meta_analysis_rejected_tsv",
    "render_cross_study_meta_analysis_study_weight_tsv",
    "render_cross_study_meta_analysis_tsv",
]
