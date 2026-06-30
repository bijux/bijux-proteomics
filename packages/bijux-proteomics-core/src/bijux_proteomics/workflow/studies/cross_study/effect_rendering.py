# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""TSV rendering for cross-study protein effect comparison reports."""

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
    from bijux_proteomics.workflow.studies.cross_study.effect_comparison import (
        CrossStudyProteinEffectComparisonReport,
    )


def render_cross_study_effect_comparison_tsv(
    report: CrossStudyProteinEffectComparisonReport,
) -> str:
    """Render one cross-study protein effect comparison report as TSV."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "harmonized_id",
            "representative_protein_refs",
            "study_ids",
            "study_kinds",
            "tested_study_count",
            "significant_study_count",
            "significant_study_ids",
            "non_significant_study_ids",
            "contrast_alignment_status",
            "anchor_condition_a",
            "anchor_condition_b",
            "comparison_status",
            "replicated_hit",
            "study_specific_hit",
            "conflicting_hit",
            "conflicting_study_ids",
            "normalized_significant_directions",
            "min_log2_fold_change",
            "max_log2_fold_change",
            "median_absolute_log2_fold_change",
            "min_adjusted_p_value",
            "median_robustness_score",
            "low_robustness_study_ids",
            "note",
        ]
    )
    for entry in report.comparisons:
        writer.writerow(
            [
                entry.harmonized_id,
                ";".join(entry.representative_protein_refs),
                ";".join(entry.study_ids),
                ";".join(kind.value for kind in entry.study_kinds),
                entry.tested_study_count,
                entry.significant_study_count,
                ";".join(entry.significant_study_ids),
                ";".join(entry.non_significant_study_ids),
                entry.contrast_alignment_status.value,
                "" if entry.anchor_condition_a is None else entry.anchor_condition_a,
                "" if entry.anchor_condition_b is None else entry.anchor_condition_b,
                entry.comparison_status.value,
                str(entry.replicated_hit).lower(),
                str(entry.study_specific_hit).lower(),
                str(entry.conflicting_hit).lower(),
                ";".join(entry.conflicting_study_ids),
                ";".join(
                    direction.value
                    for direction in entry.normalized_significant_directions
                ),
                format_optional_float(entry.min_log2_fold_change),
                format_optional_float(entry.max_log2_fold_change),
                format_optional_float(entry.median_absolute_log2_fold_change),
                format_optional_float(entry.min_adjusted_p_value),
                format_optional_float(entry.median_robustness_score),
                ";".join(entry.low_robustness_study_ids),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_cross_study_effect_detail_tsv(
    report: CrossStudyProteinEffectComparisonReport,
) -> str:
    """Render one per-study detail table for cross-study effect comparison."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "harmonized_id",
            "observation_id",
            "study_id",
            "study_label",
            "study_kind",
            "species",
            "source_kind",
            "source_surface",
            "source_entity_id",
            "representative_protein_ref",
            "protein_refs",
            "accession_aliases",
            "gene_symbol",
            "contrast_label",
            "condition_a",
            "condition_b",
            "log2_fold_change",
            "direction",
            "normalized_log2_fold_change",
            "normalized_direction",
            "p_value",
            "adjusted_p_value",
            "standard_error",
            "confidence_interval_low",
            "confidence_interval_high",
            "robustness_score",
            "robustness_qc_status",
            "significant",
            "note",
        ]
    )
    for entry in report.study_entries:
        writer.writerow(
            [
                entry.harmonized_id,
                entry.observation_id,
                entry.study_id,
                "" if entry.study_label is None else entry.study_label,
                entry.study_kind.value,
                "" if entry.species is None else entry.species,
                entry.source_kind.value,
                entry.source_surface,
                entry.source_entity_id,
                entry.representative_protein_ref,
                ";".join(entry.protein_refs),
                ";".join(entry.accession_aliases),
                "" if entry.gene_symbol is None else entry.gene_symbol,
                "" if entry.contrast_label is None else entry.contrast_label,
                entry.condition_a,
                entry.condition_b,
                format_optional_float(entry.log2_fold_change),
                entry.direction.value,
                format_optional_float(entry.normalized_log2_fold_change),
                ""
                if entry.normalized_direction is None
                else entry.normalized_direction.value,
                format_optional_float(entry.p_value),
                format_optional_float(entry.adjusted_p_value),
                format_optional_float(entry.standard_error),
                format_optional_float(entry.confidence_interval_low),
                format_optional_float(entry.confidence_interval_high),
                format_optional_float(entry.robustness_score),
                (
                    ""
                    if entry.robustness_qc_status is None
                    else entry.robustness_qc_status.value
                ),
                str(entry.significant).lower(),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_cross_study_replicated_hit_tsv(
    report: CrossStudyProteinEffectComparisonReport,
) -> str:
    """Render only replicated cross-study protein hits as TSV."""
    return _render_filtered_effect_tsv(report, "replicated_hit")


def render_cross_study_study_specific_hit_tsv(
    report: CrossStudyProteinEffectComparisonReport,
) -> str:
    """Render only study-specific cross-study protein hits as TSV."""
    return _render_filtered_effect_tsv(report, "study_specific_hit")


def render_cross_study_conflicting_hit_tsv(
    report: CrossStudyProteinEffectComparisonReport,
) -> str:
    """Render only conflicting cross-study protein hits as TSV."""
    return _render_filtered_effect_tsv(report, "conflicting_hit")


def export_cross_study_effect_comparison_tsv(
    report: CrossStudyProteinEffectComparisonReport,
    path: Path,
) -> None:
    """Write cross-study effect comparison summaries to TSV."""
    export_tsv_table(path, render_cross_study_effect_comparison_tsv(report))


def export_cross_study_effect_detail_tsv(
    report: CrossStudyProteinEffectComparisonReport,
    path: Path,
) -> None:
    """Write per-study cross-study effect details to TSV."""
    export_tsv_table(path, render_cross_study_effect_detail_tsv(report))


def export_cross_study_replicated_hit_tsv(
    report: CrossStudyProteinEffectComparisonReport,
    path: Path,
) -> None:
    """Write replicated cross-study hits to TSV."""
    export_tsv_table(path, render_cross_study_replicated_hit_tsv(report))


def export_cross_study_study_specific_hit_tsv(
    report: CrossStudyProteinEffectComparisonReport,
    path: Path,
) -> None:
    """Write study-specific cross-study hits to TSV."""
    export_tsv_table(path, render_cross_study_study_specific_hit_tsv(report))


def export_cross_study_conflicting_hit_tsv(
    report: CrossStudyProteinEffectComparisonReport,
    path: Path,
) -> None:
    """Write conflicting cross-study hits to TSV."""
    export_tsv_table(path, render_cross_study_conflicting_hit_tsv(report))


def _render_filtered_effect_tsv(
    report: CrossStudyProteinEffectComparisonReport,
    status_value: str,
) -> str:
    filtered_report = report.model_copy(
        update={
            "comparisons": tuple(
                entry
                for entry in report.comparisons
                if entry.comparison_status.value == status_value
            )
        }
    )
    return render_cross_study_effect_comparison_tsv(filtered_report)


__all__ = [
    "export_cross_study_conflicting_hit_tsv",
    "export_cross_study_effect_comparison_tsv",
    "export_cross_study_effect_detail_tsv",
    "export_cross_study_replicated_hit_tsv",
    "export_cross_study_study_specific_hit_tsv",
    "render_cross_study_conflicting_hit_tsv",
    "render_cross_study_effect_comparison_tsv",
    "render_cross_study_effect_detail_tsv",
    "render_cross_study_replicated_hit_tsv",
    "render_cross_study_study_specific_hit_tsv",
]
