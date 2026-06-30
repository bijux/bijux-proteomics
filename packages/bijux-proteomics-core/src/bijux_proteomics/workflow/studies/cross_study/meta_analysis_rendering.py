# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""TSV rendering for cross-study meta-analysis reports."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

from bijux_proteomics.workflow.studies.cross_study.tsv_support import (
    export_tsv_table,
    format_optional_float,
)

if TYPE_CHECKING:
    from bijux_proteomics.workflow.studies.cross_study.meta_analysis import (
        CrossStudyMetaAnalysisReport,
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
                format_optional_float(entry.combined_log2_fold_change),
                format_optional_float(entry.combined_standard_error),
                format_optional_float(entry.combined_confidence_interval_low),
                format_optional_float(entry.combined_confidence_interval_high),
                format_optional_float(entry.combined_p_value),
                format_optional_float(entry.combined_adjusted_p_value),
                format_optional_float(entry.fixed_effect_log2_fold_change),
                format_optional_float(entry.fixed_effect_standard_error),
                format_optional_float(entry.fixed_effect_p_value),
                format_optional_float(entry.random_effect_log2_fold_change),
                format_optional_float(entry.random_effect_standard_error),
                format_optional_float(entry.random_effect_p_value),
                format_optional_float(entry.heterogeneity_q),
                entry.heterogeneity_degrees_of_freedom,
                format_optional_float(entry.heterogeneity_i_squared),
                format_optional_float(entry.between_study_variance_tau_squared),
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
                format_optional_float(entry.normalized_log2_fold_change),
                format_optional_float(entry.standard_error),
                format_optional_float(entry.variance),
                format_optional_float(entry.fixed_weight),
                format_optional_float(entry.fixed_weight_fraction),
                format_optional_float(entry.random_weight),
                format_optional_float(entry.random_weight_fraction),
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
    export_tsv_table(path, render_cross_study_meta_analysis_tsv(report))


def export_cross_study_meta_analysis_study_weight_tsv(
    report: CrossStudyMetaAnalysisReport,
    path: Path,
) -> None:
    """Write per-study meta-analysis weights to TSV."""
    export_tsv_table(path, render_cross_study_meta_analysis_study_weight_tsv(report))


def export_cross_study_meta_analysis_rejected_tsv(
    report: CrossStudyMetaAnalysisReport,
    path: Path,
) -> None:
    """Write rejected meta-analysis groups to TSV."""
    export_tsv_table(path, render_cross_study_meta_analysis_rejected_tsv(report))


__all__ = [
    "export_cross_study_meta_analysis_rejected_tsv",
    "export_cross_study_meta_analysis_study_weight_tsv",
    "export_cross_study_meta_analysis_tsv",
    "render_cross_study_meta_analysis_rejected_tsv",
    "render_cross_study_meta_analysis_study_weight_tsv",
    "render_cross_study_meta_analysis_tsv",
]
