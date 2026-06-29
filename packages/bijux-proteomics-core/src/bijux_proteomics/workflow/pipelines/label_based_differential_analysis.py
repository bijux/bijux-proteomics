# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned labeled-proteomics differential-analysis workflows."""

from __future__ import annotations

import csv
from io import StringIO
from itertools import combinations
import math
from pathlib import Path

import numpy as np

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
from bijux_proteomics.quantification.contracts.design import (
    QuantDesignContrastEstimateEntry,
    QuantDesignMatrixReport,
    QuantDesignModelCoefficientEntry,
    QuantDesignModelFitReport,
)
from bijux_proteomics.quantification.contracts.differential import (
    DifferentialAbundanceAssumptionReport,
    DifferentialAbundanceContrast,
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    DifferentialAbundanceTestType,
    DifferentialReplicatePolicy,
    MultiConditionDifferentialAbundanceReport,
    _effect_size_and_uncertainty,
    _welch_t_test,
)
from bijux_proteomics.quantification.contracts.input_models import (
    ImputationMethod,
    NormalizationMethod,
    QuantAssessmentDisposition,
    QuantEntityLevel,
)
from bijux_proteomics.quantification.contracts.matrix_building import _condition_lookup
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
    count_effective_statistical_units_by_condition,
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
            contrasts=tuple(combinations(_condition_names(analysis_design_entries), 2)),
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


def build_label_based_differential_volcano_plot(
    report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]],
    adjusted_p_value_threshold: float = 0.1,
    absolute_log2_fold_change_threshold: float = 1.0,
) -> LabelBasedDifferentialVolcanoPlot:
    """Build one volcano payload over a BH-corrected labeled differential report."""

    points: list[LabelBasedDifferentialVolcanoPoint] = []
    for entry in report.entries:
        adjusted_p_value = entry.adjusted_p_value or entry.p_value
        highlighted = (
            adjusted_p_value <= adjusted_p_value_threshold
            and abs(entry.log2_fold_change) >= absolute_log2_fold_change_threshold
        )
        points.append(
            LabelBasedDifferentialVolcanoPoint(
                entity_id=entry.entity_id,
                protein_refs=protein_refs_by_entity.get(entry.entity_id, ()),
                log2_fold_change=entry.log2_fold_change,
                raw_p_value=entry.p_value,
                adjusted_p_value=adjusted_p_value,
                negative_log10_adjusted_p_value=_negative_log10(adjusted_p_value),
                highlighted=highlighted,
            )
        )
    return LabelBasedDifferentialVolcanoPlot(
        condition_a=report.condition_a,
        condition_b=report.condition_b,
        significant_point_count=sum(1 for point in points if point.highlighted),
        points=tuple(
            sorted(
                points,
                key=lambda point: (
                    -point.negative_log10_adjusted_p_value,
                    -abs(point.log2_fold_change),
                    point.entity_id,
                ),
            )
        ),
        note=(
            "volcano plot preserves fold change and adjusted significance for one explicit labeled contrast"
        ),
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


def _fit_design_matrix_model(
    report: LabelBasedDifferentialInputReport,
    design_matrix: QuantDesignMatrixReport,
) -> QuantDesignModelFitReport:
    sample_ids = tuple(row.sample_id for row in design_matrix.rows)
    full_matrix = np.array(
        [row.column_values for row in design_matrix.rows], dtype=float
    )
    column_index = {
        column.column_name: index for index, column in enumerate(design_matrix.columns)
    }
    row_lookup = {row.entity_id: row for row in report.rows}
    coefficient_entries: list[QuantDesignModelCoefficientEntry] = []
    contrast_estimates: list[QuantDesignContrastEstimateEntry] = []
    fitted_entity_count = 0
    skipped_entity_count = 0
    for entity_id in sorted(row_lookup):
        row = row_lookup[entity_id]
        value_lookup = {value.sample_id: value for value in row.values}
        observed_rows: list[np.ndarray] = []
        observed_values: list[float] = []
        for row_index, sample_id in enumerate(sample_ids):
            value = value_lookup.get(sample_id)
            if value is None or value.abundance is None:
                continue
            transformed = _transformed_value(
                value.abundance,
                measurement_kind=report.measurement_kind,
            )
            if transformed is None:
                continue
            observed_rows.append(full_matrix[row_index])
            observed_values.append(transformed)
        if len(observed_values) < 2:
            skipped_entity_count += 1
            continue
        x_matrix = np.vstack(observed_rows)
        y_vector = np.array(observed_values, dtype=float)
        coefficients, _, _, _ = np.linalg.lstsq(x_matrix, y_vector, rcond=None)
        rank = int(np.linalg.matrix_rank(x_matrix))
        residual_df = max(len(observed_values) - rank, 0)
        fitted_entity_count += 1
        for column, estimate in zip(design_matrix.columns, coefficients, strict=False):
            coefficient_entries.append(
                QuantDesignModelCoefficientEntry(
                    entity_id=entity_id,
                    coefficient_name=column.column_name,
                    estimate=float(estimate),
                    observed_sample_count=len(observed_values),
                    design_rank=rank,
                    residual_degrees_of_freedom=residual_df,
                )
            )
        for contrast in design_matrix.contrasts:
            estimate = sum(
                coefficients[column_index[column_name]] * weight
                for column_name, weight in contrast.coefficient_weights.items()
            )
            contrast_estimates.append(
                QuantDesignContrastEstimateEntry(
                    entity_id=entity_id,
                    contrast_name=contrast.contrast_name,
                    condition_a=contrast.condition_a,
                    condition_b=contrast.condition_b,
                    estimate=float(estimate),
                )
            )
    return QuantDesignModelFitReport(
        entity_level=QuantEntityLevel.PROTEIN,
        normalization_method=NormalizationMethod.NONE,
        imputation_method=ImputationMethod.NONE,
        design_matrix=design_matrix,
        fitted_entity_count=fitted_entity_count,
        skipped_entity_count=skipped_entity_count,
        coefficient_entries=tuple(coefficient_entries),
        contrast_estimates=tuple(contrast_estimates),
        note=(
            "design-model coefficients use one least-squares fit per labeled protein entity over transformed observed samples"
        ),
    )


def _build_differential_report(
    report: LabelBasedDifferentialInputReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str,
    condition_b: str,
    replicate_policy: DifferentialReplicatePolicy | None,
) -> DifferentialAbundanceReport:
    active_policy = replicate_policy or DifferentialReplicatePolicy()
    condition_by_sample = _condition_lookup(design_entries)
    samples_a = tuple(
        sample_id
        for sample_id, condition in condition_by_sample.items()
        if condition == condition_a
    )
    samples_b = tuple(
        sample_id
        for sample_id, condition in condition_by_sample.items()
        if condition == condition_b
    )
    if not samples_a or not samples_b:
        raise ValueError("both conditions must map to at least one sample")
    effective_units_by_condition = count_effective_statistical_units_by_condition(
        design_entries
    )
    if (
        effective_units_by_condition.get(condition_a, 0)
        < active_policy.min_replicates_per_condition
        or effective_units_by_condition.get(condition_b, 0)
        < active_policy.min_replicates_per_condition
    ) and active_policy.disposition is QuantAssessmentDisposition.ENFORCED:
        raise ValueError(
            "minimum replicate policy not satisfied for labeled differential analysis"
        )
    entries: list[DifferentialAbundanceEntry] = []
    for row in report.rows:
        value_lookup = {value.sample_id: value for value in row.values}
        values_a = np.array(
            [
                transformed
                for sample_id in samples_a
                if (value := value_lookup.get(sample_id)) is not None
                and value.abundance is not None
                and (
                    transformed := _transformed_value(
                        value.abundance,
                        measurement_kind=report.measurement_kind,
                    )
                )
                is not None
            ],
            dtype=float,
        )
        values_b = np.array(
            [
                transformed
                for sample_id in samples_b
                if (value := value_lookup.get(sample_id)) is not None
                and value.abundance is not None
                and (
                    transformed := _transformed_value(
                        value.abundance,
                        measurement_kind=report.measurement_kind,
                    )
                )
                is not None
            ],
            dtype=float,
        )
        mean_a = float(np.mean(values_a)) if values_a.size else 0.0
        mean_b = float(np.mean(values_b)) if values_b.size else 0.0
        log2_fold_change, p_value = _welch_t_test(values_a, values_b)
        (
            standard_error,
            confidence_interval_low,
            confidence_interval_high,
            effect_size_cohens_d,
            uncertainty_note,
        ) = _effect_size_and_uncertainty(values_a, values_b, log2_fold_change)
        entries.append(
            DifferentialAbundanceEntry(
                entity_id=row.entity_id,
                condition_a=condition_a,
                condition_b=condition_b,
                observations_a=int(values_a.size),
                observations_b=int(values_b.size),
                mean_log2_abundance_a=mean_a,
                mean_log2_abundance_b=mean_b,
                log2_fold_change=log2_fold_change,
                p_value=p_value,
                standard_error=standard_error,
                confidence_interval_low=confidence_interval_low,
                confidence_interval_high=confidence_interval_high,
                effect_size_cohens_d=effect_size_cohens_d,
                uncertainty_note=uncertainty_note,
            )
        )
    entries = sorted(
        entries,
        key=lambda entry: (
            entry.p_value,
            -abs(entry.log2_fold_change),
            entry.entity_id,
        ),
    )
    return DifferentialAbundanceReport(
        entity_level=QuantEntityLevel.PROTEIN,
        normalization_method=NormalizationMethod.NONE,
        imputation_method=ImputationMethod.NONE,
        condition_a=condition_a,
        condition_b=condition_b,
        replicate_policy=active_policy,
        assumption_report=DifferentialAbundanceAssumptionReport(
            test_type=DifferentialAbundanceTestType.WELCH_T_TEST,
            variance_assumption="unequal_variance",
            multiple_testing_scope="uncorrected_report_wide_entities",
            replicate_policy=active_policy,
        ),
        entries=tuple(entries),
    )


def _build_multi_condition_differential_report(
    report: LabelBasedDifferentialInputReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    contrasts: tuple[tuple[str, str], ...],
    replicate_policy: DifferentialReplicatePolicy | None,
) -> MultiConditionDifferentialAbundanceReport:
    active_policy = replicate_policy or DifferentialReplicatePolicy()
    differential_reports: list[DifferentialAbundanceReport] = []
    contrast_entries: list[DifferentialAbundanceContrast] = []
    for condition_a, condition_b in contrasts:
        contrast_entries.append(
            DifferentialAbundanceContrast(
                condition_a=condition_a,
                condition_b=condition_b,
            )
        )
        differential_reports.append(
            apply_benjamini_hochberg(
                _build_differential_report(
                    report,
                    design_entries,
                    condition_a=condition_a,
                    condition_b=condition_b,
                    replicate_policy=active_policy,
                )
            )
        )
    return MultiConditionDifferentialAbundanceReport(
        entity_level=QuantEntityLevel.PROTEIN,
        normalization_method=NormalizationMethod.NONE,
        imputation_method=ImputationMethod.NONE,
        condition_count=len(_condition_names(design_entries)),
        replicate_policy=active_policy,
        contrasts=tuple(contrast_entries),
        reports=tuple(differential_reports),
        note=(
            "pairwise labeled differential analysis preserves one benjamini-hochberg-corrected report per selected condition contrast"
        ),
    )


def _condition_names(
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                condition
                for condition in _condition_lookup(design_entries).values()
                if condition
            }
        )
    )


def _analysis_design_entries(
    report: LabelBasedDifferentialInputReport,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[ExperimentalDesignEntry, ...]:
    sample_id_set = set(report.sample_ids)
    filtered = tuple(
        entry for entry in design_entries if entry.sample_id in sample_id_set
    )
    if not filtered:
        raise ValueError(
            "labeled differential analysis requires design entries for the analysis sample ids"
        )
    return filtered


def _resolve_selected_contrast(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None,
    condition_b: str | None,
) -> tuple[str, str] | None:
    conditions = _condition_names(design_entries)
    if condition_a is None and condition_b is None:
        if len(conditions) == 2:
            return conditions[0], conditions[1]
        return None
    if condition_a is None or condition_b is None:
        raise ValueError("both condition names must be provided together")
    if condition_a == condition_b:
        raise ValueError("condition contrast must compare two distinct conditions")
    known_conditions = set(conditions)
    unknown = sorted({condition_a, condition_b} - known_conditions)
    if unknown:
        raise ValueError(
            "labeled differential contrast references unknown conditions: "
            + ", ".join(unknown)
        )
    return condition_a, condition_b


def _transformed_value(
    abundance: float,
    *,
    measurement_kind: LabelBasedMeasurementKind,
) -> float | None:
    if abundance < 0.0:
        return None
    if measurement_kind is LabelBasedMeasurementKind.INTENSITY:
        return float(math.log2(abundance + 1.0))
    if abundance <= 0.0:
        return None
    return float(math.log2(abundance))


def _negative_log10(value: float) -> float:
    clipped = max(value, 1e-300)
    return float(-math.log10(clipped))


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
