# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Quantification review-bundle assembly with explicit preparation stages."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceTestType,
    ImputationMethod,
    Ms1FeatureRecord,
    NormalizationMethod,
    PairedDifferentialPolicy,
    QuantEntityLevel,
    QuantRollupMethod,
    TimeCourseTestingPolicy,
    build_label_free_intensity_table,
    build_quant_artifact_bundle,
    build_quant_design_matrix_report,
    fit_quant_design_matrix_model,
)
from bijux_proteomics.quantification.missingness import (
    build_missingness_condition_summary_report,
    build_missingness_entity_summary_report,
    build_missingness_intensity_dependence_report,
)
from bijux_proteomics.quantification.missingness.readiness import (
    build_quant_decision_readiness_report,
)
from bijux_proteomics.quantification.normalization import (
    build_imputation_report,
    build_imputation_sensitivity_report,
    build_normalization_comparison_report,
    build_normalization_strategy_comparison_report,
    impute_label_free_table,
    normalize_label_free_table,
)
from bijux_proteomics.quantification.provenance.missingness_mechanism_profile import (
    build_missingness_mechanism_profile_report,
)
from bijux_proteomics.quantification.provenance.replicate_qc import (
    build_replicate_and_batch_qc_report,
)
from bijux_proteomics.quantification.provenance.review.channel_diagnostics import (
    build_normalization_policy_comparison_matrix_report,
)
from bijux_proteomics.quantification.provenance.review.effect_size_review import (
    build_effect_size_first_differential_abundance_report,
)
from bijux_proteomics.quantification.provenance.review.lfq_provenance import (
    build_lfq_feature_peptide_protein_provenance_report,
)
from bijux_proteomics.quantification.provenance.review.models import QuantReviewBundle
from bijux_proteomics.quantification.provenance.review.rollup_comparison import (
    build_protein_rollup_strategy_comparison_report,
)
from bijux_proteomics.quantification.statistics import (
    build_differential_abundance_report,
    build_multi_condition_differential_abundance_report,
    build_time_course_differential_report,
)
from bijux_proteomics.quantification.statistics.multi_contrast_consistency import (
    build_multi_contrast_consistency_report,
)

_EVIDENCE_POINTERS = (
    "quant_artifact_bundle.matrix_export",
    "quant_artifact_bundle.normalization_comparison_report",
    "quant_artifact_bundle.imputation_report",
    "quant_artifact_bundle.imputation_sensitivity_report",
    "quant_artifact_bundle.limma_compatible_package",
    "quant_artifact_bundle.msstats_compatible_input_report",
    "quant_artifact_bundle.replicate_qc_report.replicate_correlation_report.entries",
    "quant_artifact_bundle.replicate_qc_report.replicate_cv_report.entries",
    "quant_artifact_bundle.replicate_qc_report.outlier_samples",
    "quant_artifact_bundle.design_matrix_report",
    "quant_artifact_bundle.design_model_fit_report",
    "quant_artifact_bundle.differential_abundance_report",
    "quant_artifact_bundle.differential_abundance_multi_condition_report",
    "quant_artifact_bundle.time_course_differential_report",
    "quant_review_bundle.multi_contrast_consistency_report.entities",
    "lfq_provenance.feature_entries",
    "quant_review_bundle.normalization_comparison",
    "quant_review_bundle.imputation_report",
    "rollup_strategy_comparison.entries",
    "missingness_profile.entries",
    "missingness_entity_summary.entries",
    "missingness_condition_summary.entries",
    "missingness_intensity_dependence.plot_points",
    "qc_report.replicate_correlation_report.entries",
    "qc_report.replicate_cv_report.entries",
    "qc_report.sample_pca_report.entries",
    "qc_report.condition_clustering_report",
    "qc_report.outlier_samples",
    "quant_decision_readiness",
)


def _measured_design_entries(
    records: tuple[Ms1FeatureRecord, ...],
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[ExperimentalDesignEntry, ...]:
    observed_sample_ids = {record.sample_id for record in records}
    return tuple(
        entry for entry in design_entries if entry.sample_id in observed_sample_ids
    )


def _covariate_fields(
    measured_design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                field
                for entry in measured_design_entries
                for field, value in entry.metadata.items()
                if field != "timepoint" and value not in ("", None)
            }
        )
    )


def _timepoint_field(
    measured_design_entries: tuple[ExperimentalDesignEntry, ...],
) -> str | None:
    return (
        "timepoint"
        if all(
            entry.metadata.get("timepoint") not in ("", None)
            for entry in measured_design_entries
        )
        else None
    )


def _pairing_field(
    measured_design_entries: tuple[ExperimentalDesignEntry, ...],
) -> str | None:
    return (
        "pair_id"
        if all(entry.pair_id not in (None, "") for entry in measured_design_entries)
        else None
    )


def _build_peptide_tables(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    aggregation_method: QuantRollupMethod,
    normalization_method: NormalizationMethod,
) -> tuple[Any, Any, Any]:
    peptide_table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=aggregation_method,
    )
    normalized_table = (
        normalize_label_free_table(peptide_table, method=normalization_method)
        if normalization_method is not NormalizationMethod.NONE
        else peptide_table
    )
    normalization_comparison = build_normalization_comparison_report(
        peptide_table,
        normalized_table,
    )
    return peptide_table, normalized_table, normalization_comparison


def _build_missingness_context(
    normalized_table: Any,
    *,
    imputation_method: ImputationMethod,
    measured_design_entries: tuple[ExperimentalDesignEntry, ...],
    conditions: tuple[str, ...],
) -> tuple[Any, Any, Any | None, Any, Any, Any, Any]:
    imputed_table = impute_label_free_table(
        normalized_table,
        method=imputation_method,
    )
    imputation_report = build_imputation_report(
        normalized_table,
        imputed_table,
    )
    missingness_entity_summary = build_missingness_entity_summary_report(imputed_table)
    missingness_condition_summary = build_missingness_condition_summary_report(
        imputed_table,
        design_entries=measured_design_entries,
    )
    missingness_intensity_dependence = build_missingness_intensity_dependence_report(
        imputed_table
    )
    missingness_profile = build_missingness_mechanism_profile_report(
        imputed_table,
        design_entries=measured_design_entries,
    )
    imputation_sensitivity = (
        build_imputation_sensitivity_report(
            normalized_table,
            measured_design_entries,
            condition_a=conditions[0],
            condition_b=conditions[1],
        )
        if len(conditions) >= 2
        else None
    )
    return (
        imputed_table,
        imputation_report,
        imputation_sensitivity,
        missingness_entity_summary,
        missingness_condition_summary,
        missingness_intensity_dependence,
        missingness_profile,
    )


def _build_primary_differential_report(
    imputed_table: Any,
    *,
    measured_design_entries: tuple[ExperimentalDesignEntry, ...],
    conditions: tuple[str, ...],
    pairing_field: str | None,
    timepoint_field: str | None,
) -> Any | None:
    if len(conditions) != 2:
        return None
    try:
        return build_differential_abundance_report(
            imputed_table,
            measured_design_entries,
            condition_a=conditions[0],
            condition_b=conditions[1],
            test_type=(
                DifferentialAbundanceTestType.PAIRED_T_TEST
                if pairing_field is not None
                else DifferentialAbundanceTestType.WELCH_T_TEST
            ),
            paired_policy=(
                PairedDifferentialPolicy(pair_id_field=pairing_field)
                if pairing_field is not None
                else None
            ),
        )
    except ValueError as error:
        if not (
            timepoint_field is not None
            and "different_analysis_family_required" in str(error)
        ):
            raise
        return None


def _build_time_course_review(
    imputed_table: Any,
    *,
    measured_design_entries: tuple[ExperimentalDesignEntry, ...],
    timepoint_field: str | None,
    pairing_field: str | None,
    covariate_fields: tuple[str, ...],
) -> Any | None:
    if timepoint_field is None:
        return None
    return build_time_course_differential_report(
        imputed_table,
        measured_design_entries,
        policy=TimeCourseTestingPolicy(
            timepoint_field=timepoint_field,
            batch_field="batch",
            pairing_field=pairing_field,
            covariate_fields=covariate_fields,
        ),
    )


def _build_multi_condition_review(
    imputed_table: Any,
    *,
    measured_design_entries: tuple[ExperimentalDesignEntry, ...],
    conditions: tuple[str, ...],
    design_matrix_report: Any,
) -> Any | None:
    if len(conditions) <= 2:
        return None
    try:
        return build_multi_condition_differential_abundance_report(
            imputed_table,
            measured_design_entries,
            test_type=DifferentialAbundanceTestType.LINEAR_MODEL_CONTRAST,
            design_matrix=design_matrix_report,
        )
    except ValueError as error:
        if "insufficient_group_size" not in str(error):
            raise
        return None


def _build_effect_size_review(
    imputed_table: Any,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    conditions: tuple[str, ...],
    timepoint_field: str | None,
) -> Any | None:
    if len(conditions) != 2:
        return None
    try:
        return build_effect_size_first_differential_abundance_report(
            imputed_table,
            design_entries=design_entries,
            condition_a=conditions[0],
            condition_b=conditions[1],
        )
    except ValueError as error:
        if not (
            timepoint_field is not None
            and "different_analysis_family_required" in str(error)
        ):
            raise
        return None


def _build_backend_support(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    peptide_table: Any,
    imputed_table: Any,
    measured_design_entries: tuple[ExperimentalDesignEntry, ...],
    covariate_fields: tuple[str, ...],
    pairing_field: str | None,
    timepoint_field: str | None,
    design_matrix_report: Any,
    normalization_comparison: Any,
    imputation_report: Any,
    imputation_sensitivity: Any | None,
    missingness_entity_summary: Any,
    missingness_condition_summary: Any,
    missingness_intensity_dependence: Any,
    differential_report: Any | None,
    multi_condition_differential_report: Any | None,
    time_course_differential_report: Any | None,
) -> tuple[Any, Any, Any, Any, Any]:
    from bijux_proteomics.quantification.statistics.statistical_backend import (
        build_limma_compatible_quant_package,
        build_msstats_compatible_input_report,
    )

    limma_package = build_limma_compatible_quant_package(
        imputed_table,
        measured_design_entries,
        batch_field="batch",
        covariate_fields=covariate_fields,
        pairing_field=pairing_field,
        timepoint_field=timepoint_field,
    )
    msstats_input_report = build_msstats_compatible_input_report(
        records,
        measured_design_entries,
    )
    design_model_fit_report = fit_quant_design_matrix_model(
        imputed_table,
        design_matrix_report,
    )
    qc_report = build_replicate_and_batch_qc_report(
        imputed_table,
        design_entries=measured_design_entries,
    )
    artifact_bundle = build_quant_artifact_bundle(
        imputed_table,
        design_entries=measured_design_entries,
        imputation_report=imputation_report,
        imputation_sensitivity_report=imputation_sensitivity,
        missingness_entity_summary=missingness_entity_summary,
        missingness_condition_summary=missingness_condition_summary,
        missingness_intensity_dependence=missingness_intensity_dependence,
        replicate_qc_report=qc_report,
        normalization_comparison_report=normalization_comparison,
        normalization_strategy_report=build_normalization_strategy_comparison_report(
            peptide_table
        ),
        limma_compatible_package=limma_package,
        msstats_compatible_input_report=msstats_input_report,
        design_matrix_report=design_matrix_report,
        design_model_fit_report=design_model_fit_report,
        differential_abundance_report=differential_report,
        differential_abundance_multi_condition_report=(
            multi_condition_differential_report
        ),
        time_course_differential_report=time_course_differential_report,
    )
    return (
        artifact_bundle,
        limma_package,
        msstats_input_report,
        design_model_fit_report,
        qc_report,
    )


def _build_review_caveats(
    *,
    multi_condition_differential_report: Any | None,
    multi_contrast_consistency_report: Any | None,
    qc_report: Any,
    decision_readiness: Any,
    effect_size_da_report: Any | None,
) -> tuple[str, ...]:
    caveats: list[str] = []
    if effect_size_da_report is None and multi_condition_differential_report is None:
        caveats.append(
            "differential abundance report is unavailable because fewer than two conditions were provided"
        )
    if multi_condition_differential_report is not None:
        caveats.append(
            "multi-condition study emitted pairwise differential contrasts plus a cross-contrast consistency review instead of one primary effect-size ranking"
        )
    if (
        multi_contrast_consistency_report is not None
        and multi_contrast_consistency_report.summary.direction_conflict_count > 0
    ):
        caveats.append(
            "multi-condition contrast review found contradictory directionality across significant contrasts"
        )
    if qc_report.outlier_samples:
        caveats.append(
            "qc outlier samples were detected and should be reviewed before publication decisions"
        )
    if decision_readiness.readiness_state.value != "decision_grade":
        caveats.append(decision_readiness.note)
    return tuple(caveats)


def build_quant_review_bundle(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    imputation_method: ImputationMethod = ImputationMethod.NONE,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
) -> QuantReviewBundle:
    """Build a full quant review bundle from feature-level quant records."""
    measured_design_entries = _measured_design_entries(records, design_entries)
    covariate_fields = _covariate_fields(measured_design_entries)
    timepoint_field = _timepoint_field(measured_design_entries)
    pairing_field = _pairing_field(measured_design_entries)
    conditions = tuple(sorted({entry.condition for entry in measured_design_entries}))
    peptide_table, normalized_table, normalization_comparison = _build_peptide_tables(
        records,
        aggregation_method=aggregation_method,
        normalization_method=normalization_method,
    )
    (
        imputed_table,
        imputation_report,
        imputation_sensitivity,
        missingness_entity_summary,
        missingness_condition_summary,
        missingness_intensity_dependence,
        missingness_profile,
    ) = _build_missingness_context(
        normalized_table,
        imputation_method=imputation_method,
        measured_design_entries=measured_design_entries,
        conditions=conditions,
    )
    design_matrix_report = build_quant_design_matrix_report(
        measured_design_entries,
        batch_field="batch",
        covariate_fields=covariate_fields,
        pairing_field=pairing_field,
        timepoint_field=timepoint_field,
    )
    differential_report = _build_primary_differential_report(
        imputed_table,
        measured_design_entries=measured_design_entries,
        conditions=conditions,
        pairing_field=pairing_field,
        timepoint_field=timepoint_field,
    )
    time_course_differential_report = _build_time_course_review(
        imputed_table,
        measured_design_entries=measured_design_entries,
        timepoint_field=timepoint_field,
        pairing_field=pairing_field,
        covariate_fields=covariate_fields,
    )
    multi_condition_differential_report = _build_multi_condition_review(
        imputed_table,
        measured_design_entries=measured_design_entries,
        conditions=conditions,
        design_matrix_report=design_matrix_report,
    )
    multi_contrast_consistency_report = (
        build_multi_contrast_consistency_report(
            multi_condition_differential_report,
            entity_protein_refs=imputed_table.entity_protein_refs,
        )
        if multi_condition_differential_report is not None
        else None
    )
    (
        artifact_bundle,
        limma_package,
        msstats_input_report,
        design_model_fit_report,
        qc_report,
    ) = _build_backend_support(
        records,
        peptide_table=peptide_table,
        imputed_table=imputed_table,
        measured_design_entries=measured_design_entries,
        covariate_fields=covariate_fields,
        pairing_field=pairing_field,
        timepoint_field=timepoint_field,
        design_matrix_report=design_matrix_report,
        normalization_comparison=normalization_comparison,
        imputation_report=imputation_report,
        imputation_sensitivity=imputation_sensitivity,
        missingness_entity_summary=missingness_entity_summary,
        missingness_condition_summary=missingness_condition_summary,
        missingness_intensity_dependence=missingness_intensity_dependence,
        differential_report=differential_report,
        multi_condition_differential_report=multi_condition_differential_report,
        time_course_differential_report=time_course_differential_report,
    )
    effect_size_da_report = _build_effect_size_review(
        imputed_table,
        design_entries=design_entries,
        conditions=conditions,
        timepoint_field=timepoint_field,
    )
    lfq_provenance = build_lfq_feature_peptide_protein_provenance_report(
        records,
        aggregation_method=aggregation_method,
        normalization_method=normalization_method,
    )
    decision_readiness = build_quant_decision_readiness_report(
        imputed_table,
        design_entries=design_entries,
    )
    caveats = _build_review_caveats(
        multi_condition_differential_report=multi_condition_differential_report,
        multi_contrast_consistency_report=multi_contrast_consistency_report,
        qc_report=qc_report,
        decision_readiness=decision_readiness,
        effect_size_da_report=effect_size_da_report,
    )
    return QuantReviewBundle(
        artifact_bundle_hash=artifact_bundle.document_schema.content_hash or "",
        lfq_provenance=lfq_provenance,
        normalization_comparison=normalization_comparison,
        imputation_report=imputation_report,
        imputation_sensitivity=imputation_sensitivity,
        normalization_matrix=build_normalization_policy_comparison_matrix_report(
            peptide_table
        ),
        rollup_strategy_comparison=build_protein_rollup_strategy_comparison_report(
            records
        ),
        limma_compatible_package=limma_package,
        msstats_compatible_input_report=msstats_input_report,
        design_matrix_report=design_matrix_report,
        design_model_fit_report=design_model_fit_report,
        effect_size_da_report=effect_size_da_report,
        differential_abundance_multi_condition_report=(
            multi_condition_differential_report
        ),
        multi_contrast_consistency_report=multi_contrast_consistency_report,
        time_course_differential_report=time_course_differential_report,
        missingness_profile=missingness_profile,
        missingness_entity_summary=missingness_entity_summary,
        missingness_condition_summary=missingness_condition_summary,
        missingness_intensity_dependence=missingness_intensity_dependence,
        qc_report=qc_report,
        decision_readiness=decision_readiness,
        evidence_pointers=_EVIDENCE_POINTERS,
        caveats=caveats,
    )


__all__ = ["build_quant_review_bundle"]
