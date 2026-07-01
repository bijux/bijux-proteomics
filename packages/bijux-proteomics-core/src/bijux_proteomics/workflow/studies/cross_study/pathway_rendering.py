# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""TSV rendering for cross-study pathway comparison reports."""

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
    from bijux_proteomics.workflow.studies.cross_study.pathway_comparison import (
        CrossStudyPathwayComparisonReport,
    )


def render_cross_study_pathway_comparison_tsv(
    report: CrossStudyPathwayComparisonReport,
) -> str:
    """Render cross-study pathway comparisons as TSV."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "comparison_id",
            "signal_kind",
            "pathway_id",
            "pathway_name",
            "source_name",
            "source_accession",
            "member_kind",
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
            "shared_signal",
            "opposite_signal",
            "study_specific_signal",
            "normalized_significant_directions",
            "minimum_coverage_fraction",
            "maximum_coverage_fraction",
            "coverage_fraction_range",
            "minimum_total_member_count",
            "maximum_total_member_count",
            "minimum_adjusted_p_value",
            "maximum_enrichment_ratio",
            "note",
        ]
    )
    for entry in report.comparisons:
        writer.writerow(
            [
                entry.comparison_id,
                entry.signal_kind.value,
                entry.pathway_id,
                entry.pathway_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                "" if entry.member_kind is None else entry.member_kind.value,
                ";".join(entry.study_ids),
                ";".join(kind.value for kind in entry.study_kinds),
                entry.tested_study_count,
                entry.significant_study_count,
                ";".join(entry.significant_study_ids),
                ";".join(entry.non_significant_study_ids),
                entry.contrast_alignment_status.value,
                entry.anchor_condition_a or "",
                entry.anchor_condition_b or "",
                entry.comparison_status.value,
                str(entry.shared_signal).lower(),
                str(entry.opposite_signal).lower(),
                str(entry.study_specific_signal).lower(),
                ";".join(
                    direction.value
                    for direction in entry.normalized_significant_directions
                ),
                format_optional_float(entry.minimum_coverage_fraction),
                format_optional_float(entry.maximum_coverage_fraction),
                format_optional_float(entry.coverage_fraction_range),
                ""
                if entry.minimum_total_member_count is None
                else entry.minimum_total_member_count,
                ""
                if entry.maximum_total_member_count is None
                else entry.maximum_total_member_count,
                format_optional_float(entry.minimum_adjusted_p_value),
                format_optional_float(entry.maximum_enrichment_ratio),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_cross_study_pathway_detail_tsv(
    report: CrossStudyPathwayComparisonReport,
) -> str:
    """Render per-study pathway comparison details as TSV."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "comparison_id",
            "observation_id",
            "study_id",
            "study_label",
            "study_kind",
            "signal_kind",
            "pathway_id",
            "pathway_name",
            "source_name",
            "source_accession",
            "member_kind",
            "condition_a",
            "condition_b",
            "direction",
            "normalized_direction",
            "activity_score_delta",
            "normalized_activity_score_delta",
            "activity_confidence_status",
            "p_value",
            "adjusted_p_value",
            "enrichment_ratio",
            "significant",
            "total_member_count",
            "foreground_overlap_count",
            "background_member_count",
            "condition_a_coverage_fraction",
            "condition_b_coverage_fraction",
            "coverage_fraction",
            "note",
        ]
    )
    for entry in report.study_entries:
        writer.writerow(
            [
                entry.comparison_id,
                entry.observation_id,
                entry.study_id,
                entry.study_label or "",
                entry.study_kind.value,
                entry.signal_kind.value,
                entry.pathway_id,
                entry.pathway_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                "" if entry.member_kind is None else entry.member_kind.value,
                entry.condition_a or "",
                entry.condition_b or "",
                "" if entry.direction is None else entry.direction.value,
                ""
                if entry.normalized_direction is None
                else entry.normalized_direction.value,
                format_optional_float(entry.activity_score_delta),
                format_optional_float(entry.normalized_activity_score_delta),
                (
                    ""
                    if entry.activity_confidence_status is None
                    else entry.activity_confidence_status.value
                ),
                format_optional_float(entry.p_value),
                format_optional_float(entry.adjusted_p_value),
                format_optional_float(entry.enrichment_ratio),
                str(entry.significant).lower(),
                "" if entry.total_member_count is None else entry.total_member_count,
                ""
                if entry.foreground_overlap_count is None
                else entry.foreground_overlap_count,
                ""
                if entry.background_member_count is None
                else entry.background_member_count,
                format_optional_float(entry.condition_a_coverage_fraction),
                format_optional_float(entry.condition_b_coverage_fraction),
                format_optional_float(entry.coverage_fraction),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_cross_study_shared_pathway_signal_tsv(
    report: CrossStudyPathwayComparisonReport,
) -> str:
    """Render shared pathway signals as TSV."""
    return _render_filtered_pathway_tsv(report, "shared_signal")


def render_cross_study_opposite_pathway_signal_tsv(
    report: CrossStudyPathwayComparisonReport,
) -> str:
    """Render opposite pathway signals as TSV."""
    return _render_filtered_pathway_tsv(report, "opposite_signal")


def render_cross_study_study_specific_pathway_tsv(
    report: CrossStudyPathwayComparisonReport,
) -> str:
    """Render study-specific pathway signals as TSV."""
    return _render_filtered_pathway_tsv(report, "study_specific_signal")


def export_cross_study_pathway_comparison_tsv(
    report: CrossStudyPathwayComparisonReport,
    path: Path,
) -> None:
    """Write pathway comparison summaries to TSV."""
    export_tsv_table(path, render_cross_study_pathway_comparison_tsv(report))


def export_cross_study_pathway_detail_tsv(
    report: CrossStudyPathwayComparisonReport,
    path: Path,
) -> None:
    """Write pathway comparison details to TSV."""
    export_tsv_table(path, render_cross_study_pathway_detail_tsv(report))


def export_cross_study_shared_pathway_signal_tsv(
    report: CrossStudyPathwayComparisonReport,
    path: Path,
) -> None:
    """Write shared pathway signals to TSV."""
    export_tsv_table(path, render_cross_study_shared_pathway_signal_tsv(report))


def export_cross_study_opposite_pathway_signal_tsv(
    report: CrossStudyPathwayComparisonReport,
    path: Path,
) -> None:
    """Write opposite pathway signals to TSV."""
    export_tsv_table(path, render_cross_study_opposite_pathway_signal_tsv(report))


def export_cross_study_study_specific_pathway_tsv(
    report: CrossStudyPathwayComparisonReport,
    path: Path,
) -> None:
    """Write study-specific pathway signals to TSV."""
    export_tsv_table(path, render_cross_study_study_specific_pathway_tsv(report))


def _render_filtered_pathway_tsv(
    report: CrossStudyPathwayComparisonReport,
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
    return render_cross_study_pathway_comparison_tsv(filtered_report)


__all__ = [
    "export_cross_study_opposite_pathway_signal_tsv",
    "export_cross_study_pathway_comparison_tsv",
    "export_cross_study_pathway_detail_tsv",
    "export_cross_study_shared_pathway_signal_tsv",
    "export_cross_study_study_specific_pathway_tsv",
    "render_cross_study_opposite_pathway_signal_tsv",
    "render_cross_study_pathway_comparison_tsv",
    "render_cross_study_pathway_detail_tsv",
    "render_cross_study_shared_pathway_signal_tsv",
    "render_cross_study_study_specific_pathway_tsv",
]
