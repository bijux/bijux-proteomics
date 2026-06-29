# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Workflow orchestration entry points for labeled differential analysis."""

from __future__ import annotations

from pathlib import Path

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
from bijux_proteomics.quantification.differential_abundance import apply_benjamini_hochberg
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
    LabelBasedDifferentialVolcanoPlot,
)
from bijux_proteomics.workflow.pipelines.label_based_differential.normalization import (
    build_label_based_normalization_balance_plot,
    normalize_input_report,
)
from bijux_proteomics.workflow.pipelines.label_based_differential.statistics import (
    build_label_based_differential_report,
    build_label_based_differential_volcano_plot,
    build_multi_condition_label_based_differential_report,
    filter_label_based_design_entries,
    fit_label_based_design_matrix_model,
    resolve_label_based_contrast,
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
    analysis_design_entries = filter_label_based_design_entries(
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
    normalized_matrix, normalization_factors = normalize_input_report(
        input_report,
        method=normalization_method,
    )
    design_matrix = build_quant_design_matrix_report(
        analysis_design_entries,
        batch_field=batch_field,
        covariate_fields=tuple(dict.fromkeys(covariate_fields)),
        pairing_field=pairing_field,
    )
    design_model_fit = fit_label_based_design_matrix_model(
        normalized_matrix,
        design_matrix,
    )
    selected_contrast = resolve_label_based_contrast(
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
            build_label_based_differential_report(
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
        multi_condition_report = build_multi_condition_label_based_differential_report(
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


__all__ = [
    "build_label_based_differential_analysis_report",
    "build_silac_differential_analysis_report",
    "build_tmt_differential_analysis_report",
]
