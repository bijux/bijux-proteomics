# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned labeled-proteomics differential-analysis workflows."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.isotope_labeling import (
    SilacColumnMapping,
    SilacQuantificationPolicy,
)
from bijux_proteomics.multiplex import (
    TmtReporterChannelColumn,
    TmtReporterColumnMapping,
    TmtSearchResultSourceKind,
)
from bijux_proteomics.quantification.contracts.differential import (
    DifferentialAbundanceReport,
    DifferentialReplicatePolicy,
    MultiConditionDifferentialAbundanceReport,
)
from bijux_proteomics.quantification.contracts.input_models import (
    NormalizationMethod,
    QuantAssessmentDisposition,
)
from bijux_proteomics.quantification.design_matrix import (
    build_quant_design_matrix_report,
)
from bijux_proteomics.quantification.differential_abundance import (
    apply_benjamini_hochberg,
    render_differential_abundance_tsv,
    render_multi_condition_differential_abundance_tsv,
)
from bijux_proteomics.study import (
    ExperimentDesign,
    ExperimentDesignAnalysisFamily,
    build_experiment_design,
    coerce_experiment_design,
    require_feasible_experiment_design_for_analysis,
    require_valid_experiment_design_for_differential_analysis,
)
from bijux_proteomics.workflow.pipelines.label_based_differential.inputs import (
    build_silac_differential_input_report,
    build_tmt_differential_input_report,
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
    _normalize_input_report,
    build_label_based_normalization_balance_plot,
)
from bijux_proteomics.workflow.pipelines.label_based_differential.statistics import (
    _analysis_design_entries,
    _build_differential_report,
    _build_multi_condition_differential_report,
    _fit_design_matrix_model,
    _resolve_selected_contrast,
    build_label_based_differential_volcano_plot,
)


def build_label_based_differential_analysis_report(
    input_report: LabelBasedDifferentialInputReport,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
    replicate_policy: DifferentialReplicatePolicy | None = None,
) -> LabelBasedDifferentialAnalysisReport:
    """Normalize one labeled matrix, build the design, and run differential testing."""

    experiment_design = coerce_experiment_design(design_entries)
    experiment_design = require_valid_experiment_design_for_differential_analysis(
        experiment_design,
        require_complete_plex_channels=bool(experiment_design.plexes),
    )
    analysis_design_entries = _analysis_design_entries(
        input_report,
        design_entries=experiment_design.entries,
    )
    analysis_experiment_design = (
        require_valid_experiment_design_for_differential_analysis(
            build_experiment_design(analysis_design_entries),
            condition_a=condition_a,
            condition_b=condition_b,
            batch_field=batch_field if batch_field else None,
            pairing_field=pairing_field,
        )
    )
    analysis_design_entries = analysis_experiment_design.entries
    normalized_matrix, normalization_factors = _normalize_input_report(
        input_report,
        method=normalization_method,
    )
    design_matrix = build_quant_design_matrix_report(
        analysis_design_entries,
        batch_field=batch_field,
        covariate_fields=tuple(dict.fromkeys(covariate_fields)),
        pairing_field=pairing_field,
    )
    design_model_fit = _fit_design_matrix_model(
        normalized_matrix,
        design_matrix,
    )
    selected_contrast = _resolve_selected_contrast(
        analysis_design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    if selected_contrast is not None and any(
        entry.metadata.get("timepoint") not in ("", None)
        for entry in analysis_design_entries
    ):
        raise ValueError(
            "longitudinal labeled designs require time_course_differential rather than pairwise_differential"
        )
    try:
        require_feasible_experiment_design_for_analysis(
            analysis_experiment_design,
            chosen_analysis_family=(
                ExperimentDesignAnalysisFamily.PAIRWISE_DIFFERENTIAL
                if selected_contrast is not None
                else ExperimentDesignAnalysisFamily.MULTI_CONDITION_DIFFERENTIAL
            ),
            condition_a=(
                selected_contrast[0] if selected_contrast is not None else condition_a
            ),
            condition_b=(
                selected_contrast[1] if selected_contrast is not None else condition_b
            ),
            batch_field=batch_field if batch_field else None,
            pairing_field=pairing_field,
        )
    except ValueError as error:
        active_replicate_policy = replicate_policy or DifferentialReplicatePolicy()
        if (
            selected_contrast is not None
            and active_replicate_policy.disposition
            is QuantAssessmentDisposition.ENFORCED
            and "insufficient_group_size" in str(error)
        ):
            raise ValueError(
                "minimum replicate policy not satisfied for labeled differential analysis"
            ) from error
        raise
    differential_report: DifferentialAbundanceReport | None = None
    multi_condition_report: MultiConditionDifferentialAbundanceReport | None = None
    volcano_plot: LabelBasedDifferentialVolcanoPlot | None = None
    if selected_contrast is not None:
        differential_report = apply_benjamini_hochberg(
            _build_differential_report(
                normalized_matrix,
                analysis_design_entries,
                condition_a=selected_contrast[0],
                condition_b=selected_contrast[1],
                replicate_policy=replicate_policy,
            )
        )
        volcano_plot = build_label_based_differential_volcano_plot(
            differential_report,
            protein_refs_by_entity={
                row.entity_id: row.protein_refs for row in normalized_matrix.rows
            },
        )
    else:
        multi_condition_report = _build_multi_condition_differential_report(
            normalized_matrix,
            analysis_design_entries,
            replicate_policy=replicate_policy,
        )

    return LabelBasedDifferentialAnalysisReport(
        input_report=input_report,
        normalization_method=normalization_method,
        normalization_factors=normalization_factors,
        normalized_matrix=normalized_matrix,
        normalization_balance_plot=build_label_based_normalization_balance_plot(
            input_report,
            normalized_matrix,
            method=normalization_method,
        ),
        design_matrix=design_matrix,
        design_model_fit=design_model_fit,
        differential_abundance_report=differential_report,
        differential_abundance_multi_condition_report=multi_condition_report,
        volcano_plot=volcano_plot,
        note=(
            "labeled differential analysis preserves normalization, explicit design encoding, and benjamini-hochberg-corrected differential results"
        ),
    )


def build_tmt_differential_analysis_report(
    result_tsv_path: Path,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    source_kind: TmtSearchResultSourceKind = TmtSearchResultSourceKind.MAXQUANT,
    mapping: TmtReporterColumnMapping | None = None,
    channel_columns: tuple[TmtReporterChannelColumn, ...] = (),
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
    replicate_policy: DifferentialReplicatePolicy | None = None,
) -> LabelBasedDifferentialAnalysisReport:
    """Build TMT normalization, design, and differential results in one path."""

    input_report = build_tmt_differential_input_report(
        result_tsv_path,
        design_entries,
        source_kind=source_kind,
        mapping=mapping,
        channel_columns=channel_columns,
    )
    return build_label_based_differential_analysis_report(
        input_report,
        design_entries,
        normalization_method=normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        batch_field=batch_field,
        covariate_fields=covariate_fields,
        pairing_field=pairing_field,
        replicate_policy=replicate_policy,
    )


def build_silac_differential_analysis_report(
    feature_tsv_path: Path,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    mapping: SilacColumnMapping | None = None,
    quantification_policy: SilacQuantificationPolicy | None = None,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
    replicate_policy: DifferentialReplicatePolicy | None = None,
) -> LabelBasedDifferentialAnalysisReport:
    """Build SILAC normalization, design, and differential results in one path."""

    input_report = build_silac_differential_input_report(
        feature_tsv_path,
        mapping=mapping,
        quantification_policy=quantification_policy,
    )
    return build_label_based_differential_analysis_report(
        input_report,
        design_entries,
        normalization_method=normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        batch_field=batch_field,
        covariate_fields=covariate_fields,
        pairing_field=pairing_field,
        replicate_policy=replicate_policy,
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
    "build_label_based_differential_analysis_report",
    "build_label_based_differential_volcano_plot",
    "build_label_based_normalization_balance_plot",
    "build_silac_differential_analysis_report",
    "build_silac_differential_input_report",
    "build_tmt_differential_analysis_report",
    "build_tmt_differential_input_report",
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
