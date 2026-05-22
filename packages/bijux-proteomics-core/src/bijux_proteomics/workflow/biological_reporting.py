# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned biological result bundles over governed label-free protein quantification."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    HeatmapMissingValuePolicy,
    HeatmapPreparationPolicy,
    HeatmapPreparationReport,
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    SampleExplorationReport,
    build_differential_abundance_report,
    build_heatmap_preparation_report,
    build_label_free_intensity_table,
    build_sample_exploration_report,
    normalize_label_free_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.quantification.contracts import DifferentialAbundanceReport
from bijux_proteomics.quantification.differential_abundance import (
    apply_benjamini_hochberg,
)
from bijux_proteomics.review import (
    VolcanoReviewPolicy,
    VolcanoReviewReport,
    build_quantification_volcano_review,
)
from bijux_proteomics_foundation import JsonModel


class BiologicalResultSelectionPolicy(JsonModel):
    """Selection policy for interpretation-focused biological result bundles."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(default=1.0, ge=0.0)
    heatmap_max_entity_count: int = Field(default=50, ge=1)
    heatmap_min_observed_fraction: float = Field(default=0.5, ge=0.0, le=1.0)


class BiologicalResultReportSummary(JsonModel):
    """Compact summary over one biological result bundle."""

    model_config = ConfigDict(extra="forbid")

    protein_count: int = Field(..., ge=0)
    significant_protein_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    heatmap_entity_count: int = Field(..., ge=0)
    pca_outlier_sample_count: int = Field(..., ge=0)


class BiologicalResultReportBundle(JsonModel):
    """Owned workflow bundle over differential proteins and review-ready plots."""

    model_config = ConfigDict(extra="forbid")

    differential_report: DifferentialAbundanceReport
    volcano_review: VolcanoReviewReport
    heatmap_report: HeatmapPreparationReport
    sample_exploration_report: SampleExplorationReport
    selection_policy: BiologicalResultSelectionPolicy
    summary: BiologicalResultReportSummary
    note: str = Field(..., min_length=1)


def build_biological_result_report_bundle(
    input_tsv_path: Path,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    mapping: Ms1FeatureColumnMapping | None = None,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    top_n: int = 3,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    selection_policy: BiologicalResultSelectionPolicy | None = None,
    volcano_policy: VolcanoReviewPolicy | None = None,
) -> BiologicalResultReportBundle:
    """Build a biological result bundle over one governed protein LFQ workflow."""

    active_mapping = mapping or Ms1FeatureColumnMapping(
        sample_id="sample_id",
        feature_id="feature_id",
        peptide="peptide",
        intensity="intensity",
        protein_refs="proteins",
        charge="charge",
        mz="mz",
        retention_time_seconds="retention_time_seconds",
        missing_reason="missing_reason",
        protein_separator=";",
    )
    active_selection_policy = selection_policy or BiologicalResultSelectionPolicy()
    parse_report = parse_ms1_feature_table(input_tsv_path, mapping=active_mapping)
    normalized_table = normalize_label_free_table(
        build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=aggregation_method,
            top_n=top_n,
        ),
        method=normalization_method,
    )
    resolved_condition_a, resolved_condition_b = _resolve_contrast(
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            normalized_table,
            design_entries,
            condition_a=resolved_condition_a,
            condition_b=resolved_condition_b,
        )
    )
    volcano_review = build_quantification_volcano_review(
        differential_report,
        protein_refs_by_entity=normalized_table.entity_protein_refs,
        policy=volcano_policy,
    )
    selected_entity_ids = _select_heatmap_entity_ids(
        differential_report,
        policy=active_selection_policy,
    )
    heatmap_report = build_heatmap_preparation_report(
        normalized_table,
        design_entries=design_entries,
        policy=HeatmapPreparationPolicy(
            entity_ids=selected_entity_ids,
            min_observed_fraction=active_selection_policy.heatmap_min_observed_fraction,
            max_entity_count=active_selection_policy.heatmap_max_entity_count,
            z_score_rows=True,
            missing_value_policy=HeatmapMissingValuePolicy.FILL_ROW_MEDIAN,
        ),
    )
    sample_exploration_report = build_sample_exploration_report(
        normalized_table,
        design_entries,
    )
    significant_protein_count = len(
        _select_significant_entity_ids(differential_report, policy=active_selection_policy)
    )
    return BiologicalResultReportBundle(
        differential_report=differential_report,
        volcano_review=volcano_review,
        heatmap_report=heatmap_report,
        sample_exploration_report=sample_exploration_report,
        selection_policy=active_selection_policy,
        summary=BiologicalResultReportSummary(
            protein_count=len(normalized_table.entity_ids),
            significant_protein_count=significant_protein_count,
            sample_count=len(normalized_table.sample_ids),
            heatmap_entity_count=len(heatmap_report.rows),
            pca_outlier_sample_count=sum(
                1 for entry in sample_exploration_report.sample_pca_report.entries if entry.outlier
            ),
        ),
        note=(
            "biological reporting assembles governed protein differential analysis, volcano review, heatmap preparation, and sample exploration into one owned workflow bundle"
        ),
    )


def _resolve_contrast(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None,
    condition_b: str | None,
) -> tuple[str, str]:
    if bool(condition_a) ^ bool(condition_b):
        raise ValueError("both condition_a and condition_b are required together")
    if condition_a is not None and condition_b is not None:
        return condition_a, condition_b
    conditions = tuple(
        sorted({entry.condition for entry in design_entries if entry.condition})
    )
    if len(conditions) != 2:
        raise ValueError(
            "biological result reporting requires exactly two conditions or an explicit contrast"
        )
    return conditions[0], conditions[1]


def _select_significant_entity_ids(
    report: DifferentialAbundanceReport,
    *,
    policy: BiologicalResultSelectionPolicy,
) -> tuple[str, ...]:
    return tuple(
        entry.entity_id
        for entry in report.entries
        if entry.adjusted_p_value is not None
        and entry.adjusted_p_value <= policy.max_adjusted_p_value
        and abs(entry.log2_fold_change) >= policy.min_absolute_log2_fold_change
    )


def _select_heatmap_entity_ids(
    report: DifferentialAbundanceReport,
    *,
    policy: BiologicalResultSelectionPolicy,
) -> tuple[str, ...]:
    significant_entity_ids = _select_significant_entity_ids(report, policy=policy)
    if significant_entity_ids:
        return significant_entity_ids
    ranked_entries = sorted(
        report.entries,
        key=lambda entry: (
            -(abs(entry.log2_fold_change)),
            entry.adjusted_p_value if entry.adjusted_p_value is not None else 1.0,
            entry.entity_id,
        ),
    )
    return tuple(
        entry.entity_id for entry in ranked_entries[: policy.heatmap_max_entity_count]
    )


__all__ = [
    "BiologicalResultReportBundle",
    "BiologicalResultReportSummary",
    "BiologicalResultSelectionPolicy",
    "build_biological_result_report_bundle",
]
