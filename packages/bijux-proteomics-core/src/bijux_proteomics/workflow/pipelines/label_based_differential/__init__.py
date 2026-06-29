# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Labeled differential workflow owners grouped by stable scientific boundary."""

from __future__ import annotations

from bijux_proteomics.workflow.pipelines.label_based_differential.inputs import (
    build_input_report_from_protein_matrix,
    build_input_report_from_silac_ratio_report,
    build_silac_differential_input_report,
    build_tmt_differential_input_report,
    fill_missing_matrix_values,
)
from bijux_proteomics.workflow.pipelines.label_based_differential.models import (
    LabelBasedDifferentialAnalysisReport,
    LabelBasedDifferentialInputReport,
    LabelBasedDifferentialMatrixRow,
    LabelBasedDifferentialMatrixSummary,
    LabelBasedDifferentialMatrixValue,
    LabelBasedDifferentialSourceKind,
    LabelBasedDifferentialVolcanoPlot,
    LabelBasedDifferentialVolcanoPoint,
    LabelBasedMeasurementKind,
    LabelBasedNormalizationBalancePlot,
    LabelBasedNormalizationBalancePoint,
)
from bijux_proteomics.workflow.pipelines.label_based_differential.normalization import (
    build_label_based_normalization_balance_plot,
    normalize_input_report,
)
from bijux_proteomics.workflow.pipelines.label_based_differential.rendering import (
    export_label_based_differential_matrix_tsv,
    export_label_based_differential_missingness_tsv,
    export_label_based_differential_results_tsv,
    export_label_based_differential_volcano_plot_tsv,
    export_label_based_normalization_balance_plot_tsv,
    render_label_based_differential_matrix_tsv,
    render_label_based_differential_missingness_tsv,
    render_label_based_differential_results_tsv,
    render_label_based_differential_volcano_plot_tsv,
    render_label_based_normalization_balance_plot_tsv,
)
from bijux_proteomics.workflow.pipelines.label_based_differential.statistics import (
    build_label_based_differential_report,
    build_label_based_differential_volcano_plot,
    build_multi_condition_label_based_differential_report,
    filter_label_based_design_entries,
    fit_label_based_design_matrix_model,
    list_label_based_conditions,
    resolve_label_based_contrast,
)

__all__ = [
    "LabelBasedDifferentialAnalysisReport",
    "LabelBasedDifferentialInputReport",
    "LabelBasedDifferentialMatrixRow",
    "LabelBasedDifferentialMatrixSummary",
    "LabelBasedDifferentialMatrixValue",
    "LabelBasedDifferentialSourceKind",
    "LabelBasedDifferentialVolcanoPlot",
    "LabelBasedDifferentialVolcanoPoint",
    "LabelBasedMeasurementKind",
    "LabelBasedNormalizationBalancePlot",
    "LabelBasedNormalizationBalancePoint",
    "build_label_based_differential_report",
    "build_label_based_differential_volcano_plot",
    "build_label_based_normalization_balance_plot",
    "build_input_report_from_protein_matrix",
    "build_input_report_from_silac_ratio_report",
    "build_multi_condition_label_based_differential_report",
    "build_silac_differential_input_report",
    "build_tmt_differential_input_report",
    "export_label_based_differential_matrix_tsv",
    "export_label_based_differential_missingness_tsv",
    "export_label_based_differential_results_tsv",
    "export_label_based_differential_volcano_plot_tsv",
    "export_label_based_normalization_balance_plot_tsv",
    "fill_missing_matrix_values",
    "filter_label_based_design_entries",
    "fit_label_based_design_matrix_model",
    "list_label_based_conditions",
    "normalize_input_report",
    "render_label_based_differential_matrix_tsv",
    "render_label_based_differential_missingness_tsv",
    "render_label_based_differential_results_tsv",
    "render_label_based_differential_volcano_plot_tsv",
    "render_label_based_normalization_balance_plot_tsv",
    "resolve_label_based_contrast",
]
