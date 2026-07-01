# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Tabular rendering and export for labeled differential workflow outputs."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.quantification.differential_abundance import (
    render_differential_abundance_tsv,
    render_multi_condition_differential_abundance_tsv,
)
from bijux_proteomics.workflow.pipelines.comparative.label_based_differential.models import (
    LabelBasedDifferentialAnalysisReport,
    LabelBasedDifferentialInputReport,
    LabelBasedDifferentialVolcanoPlot,
    LabelBasedNormalizationBalancePlot,
)


def render_label_based_differential_matrix_tsv(
    report: LabelBasedDifferentialInputReport,
) -> str:
    """Render one labeled differential matrix as a stable wide TSV table."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        ("entity_id", "protein_refs", "member_peptides", *report.sample_ids)
    )
    for row in report.rows:
        value_lookup = {value.sample_id: value for value in row.values}
        writer.writerow(
            (
                row.entity_id,
                ";".join(row.protein_refs),
                ";".join(row.member_peptides),
                *[
                    ""
                    if (value := value_lookup[sample_id]).abundance is None
                    else f"{value.abundance:g}"
                    for sample_id in report.sample_ids
                ],
            )
        )
    return handle.getvalue()


def render_label_based_differential_missingness_tsv(
    report: LabelBasedDifferentialInputReport,
) -> str:
    """Render one labeled differential missingness mask beside the wide matrix."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        ("entity_id", "protein_refs", "member_peptides", *report.sample_ids)
    )
    for row in report.rows:
        value_lookup = {value.sample_id: value for value in row.values}
        writer.writerow(
            (
                row.entity_id,
                ";".join(row.protein_refs),
                ";".join(row.member_peptides),
                *[
                    value_lookup[sample_id].missing_value_kind.value
                    for sample_id in report.sample_ids
                ],
            )
        )
    return handle.getvalue()


def render_label_based_differential_results_tsv(
    report: LabelBasedDifferentialAnalysisReport,
) -> str:
    """Render one labeled differential result surface as TSV."""

    if report.differential_abundance_report is not None:
        return render_differential_abundance_tsv(report.differential_abundance_report)
    if report.differential_abundance_multi_condition_report is not None:
        return render_multi_condition_differential_abundance_tsv(
            report.differential_abundance_multi_condition_report
        )
    raise ValueError(
        "labeled differential analysis report does not contain differential results"
    )


def render_label_based_normalization_balance_plot_tsv(
    plot: LabelBasedNormalizationBalancePlot,
) -> str:
    """Render one normalization-balance plot payload as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sample_id",
            "stage",
            "total_abundance",
            "median_abundance",
            "interquartile_range",
        )
    )
    for point in plot.points:
        writer.writerow(
            (
                point.sample_id,
                point.stage,
                f"{point.total_abundance:g}",
                f"{point.median_abundance:g}",
                f"{point.interquartile_range:g}",
            )
        )
    return handle.getvalue()


def render_label_based_differential_volcano_plot_tsv(
    plot: LabelBasedDifferentialVolcanoPlot,
) -> str:
    """Render one labeled volcano plot payload as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "protein_refs",
            "log2_fold_change",
            "raw_p_value",
            "adjusted_p_value",
            "negative_log10_adjusted_p_value",
            "highlighted",
        )
    )
    for point in plot.points:
        writer.writerow(
            (
                point.entity_id,
                ";".join(point.protein_refs),
                f"{point.log2_fold_change:g}",
                f"{point.raw_p_value:g}",
                f"{point.adjusted_p_value:g}",
                f"{point.negative_log10_adjusted_p_value:g}",
                str(point.highlighted).lower(),
            )
        )
    return handle.getvalue()


def export_label_based_differential_matrix_tsv(
    report: LabelBasedDifferentialInputReport,
    path: Path,
) -> None:
    """Write one labeled differential matrix to a stable TSV artifact."""

    write_output_table_tsv(path, render_label_based_differential_matrix_tsv(report))


def export_label_based_differential_missingness_tsv(
    report: LabelBasedDifferentialInputReport,
    path: Path,
) -> None:
    """Write one labeled differential missingness mask to a stable TSV artifact."""

    write_output_table_tsv(
        path, render_label_based_differential_missingness_tsv(report)
    )


def export_label_based_differential_results_tsv(
    report: LabelBasedDifferentialAnalysisReport,
    path: Path,
) -> None:
    """Write one labeled differential result surface to a stable TSV artifact."""

    write_output_table_tsv(path, render_label_based_differential_results_tsv(report))


def export_label_based_normalization_balance_plot_tsv(
    plot: LabelBasedNormalizationBalancePlot,
    path: Path,
) -> None:
    """Write one labeled normalization-balance plot payload as TSV."""

    write_output_table_tsv(
        path, render_label_based_normalization_balance_plot_tsv(plot)
    )


def export_label_based_differential_volcano_plot_tsv(
    plot: LabelBasedDifferentialVolcanoPlot,
    path: Path,
) -> None:
    """Write one labeled volcano plot payload as TSV."""

    write_output_table_tsv(path, render_label_based_differential_volcano_plot_tsv(plot))


__all__ = [
    "export_label_based_differential_matrix_tsv",
    "export_label_based_differential_missingness_tsv",
    "export_label_based_differential_results_tsv",
    "export_label_based_differential_volcano_plot_tsv",
    "export_label_based_normalization_balance_plot_tsv",
    "render_label_based_differential_matrix_tsv",
    "render_label_based_differential_missingness_tsv",
    "render_label_based_differential_results_tsv",
    "render_label_based_differential_volcano_plot_tsv",
    "render_label_based_normalization_balance_plot_tsv",
]
