# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Quantification and QC capability surfaces."""

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceTestType,
    ImputationMethod,
    LabelBasedChannelRole,
    LabelBasedQuantPolicy,
    LabelFreeQuantTable,
    Ms1FeatureRecord,
    MultiplexNormalizationPolicy,
    NormalizationMethod,
    PairedDifferentialPolicy,
    QuantEntityLevel,
    QuantRollupMethod,
    TimeCourseTestingPolicy,
    build_label_based_quant_bundle,
    build_label_free_intensity_table,
    build_label_free_provenance_bundle,
    build_multiplex_channel_balance_report,
    build_quant_artifact_bundle,
    build_quant_design_matrix_report,
    fit_quant_design_matrix_model,
)
from bijux_proteomics.quantification.missingness import (
    build_missingness_condition_summary_report,
    build_missingness_entity_summary_report,
    build_missingness_intensity_dependence_report,
    summarize_missing_values,
)
from bijux_proteomics.quantification.normalization import (
    build_imputation_report,
    build_imputation_sensitivity_report,
    build_normalization_comparison_report,
    build_normalization_strategy_comparison_report,
    impute_label_free_table,
    normalize_label_free_table,
)
from bijux_proteomics.quantification.missingness.readiness import (
    build_quant_decision_readiness_report,
)
from bijux_proteomics.quantification.provenance.review.channel_diagnostics import (
    build_label_based_quant_channel_ledger,
    build_multiplex_channel_balance_diagnostics_report,
    build_normalization_policy_comparison_matrix_report,
)
from bijux_proteomics.quantification.provenance.review.rollup_comparison import (
    build_protein_rollup_strategy_comparison_report,
)
from bijux_proteomics.quantification.provenance.missingness_mechanism_profile import (
    MissingnessMechanismKind as MissingnessMechanismKind,
)
from bijux_proteomics.quantification.provenance.missingness_mechanism_profile import (
    MissingnessMechanismProfileReport as MissingnessMechanismProfileReport,
)
from bijux_proteomics.quantification.provenance.missingness_mechanism_profile import (
    build_missingness_mechanism_profile_report as build_missingness_mechanism_profile_report,
)
from bijux_proteomics.quantification.provenance.replicate_qc import (
    build_replicate_and_batch_qc_report,
)
from bijux_proteomics.quantification.statistics import (
    apply_benjamini_hochberg,
    build_differential_abundance_report,
    build_multi_condition_differential_abundance_report,
    build_time_course_differential_report,
)
from bijux_proteomics.quantification.statistics.multi_contrast_consistency import (
    build_multi_contrast_consistency_report,
)
from bijux_proteomics.study.replicate_structure import (
    count_effective_statistical_units_by_condition,
)
from bijux_proteomics.quantification.provenance.review.models import (
    DifferentialAbundanceDesignIssue,
    DifferentialAbundanceDesignValidationReport,
    EffectSizeFirstDaEntry,
    EffectSizeFirstDaReport,
    LabelBasedQuantChannelLedgerEntry,
    LabelBasedQuantChannelLedgerReport,
    LfqFeaturePeptideProteinProvenanceReport,
    MultipleTestingScopeBenchmarkEntry,
    MultipleTestingScopeBenchmarkReport,
    MultipleTestingScopeBenchmarkStatus,
    MultiplexChannelBalanceDiagnosticsReport,
    NormalizationPolicyComparisonEntry,
    NormalizationPolicyComparisonMatrixReport,
    ProteinRollupStrategyComparisonEntry,
    ProteinRollupStrategyComparisonReport,
    ProteinRollupStrategyKind,
    ProteinRollupStrategyValue,
    QuantNormalizationPolicyKind,
    QuantReviewBundle,
)


def build_lfq_feature_peptide_protein_provenance_report(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    top_n: int = 3,
) -> LfqFeaturePeptideProteinProvenanceReport:
    """Build LFQ provenance preserving feature, peptide, protein, and missingness context."""
    bundle = build_label_free_provenance_bundle(
        records,
        aggregation_method=aggregation_method,
        normalization_method=normalization_method,
        top_n=top_n,
    )
    peptide_table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    protein_table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    if normalization_method is not NormalizationMethod.NONE:
        peptide_table = normalize_label_free_table(
            peptide_table, method=normalization_method
        )
        protein_table = normalize_label_free_table(
            protein_table, method=normalization_method
        )

    peptide_missingness = summarize_missing_values(peptide_table)
    protein_missingness = summarize_missing_values(protein_table)
    return LfqFeaturePeptideProteinProvenanceReport(
        provenance_bundle=bundle,
        peptide_missingness=peptide_missingness,
        protein_missingness=protein_missingness,
        feature_entry_count=len(bundle.feature_entries),
        peptide_entry_count=len(bundle.peptide_entries),
        protein_entry_count=len(bundle.protein_entries),
        normalization_method=normalization_method,
        note=(
            "lfq provenance preserves feature-to-peptide-to-protein evidence while retaining missingness and normalization context"
        ),
    )

def validate_differential_abundance_design_context(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    contrasts: tuple[tuple[str, str], ...],
    covariates: tuple[str, ...] = (),
    blocking_field: str | None = "batch",
    min_replicates_per_condition: int = 2,
    multiple_testing_scope: str = "global_per_analysis",
) -> DifferentialAbundanceDesignValidationReport:
    """Validate DA design assumptions before running statistical comparisons."""
    condition_replicates = count_effective_statistical_units_by_condition(
        design_entries
    )
    issues: list[DifferentialAbundanceDesignIssue] = []
    known_conditions = set(condition_replicates)
    for left, right in contrasts:
        if left == right:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="degenerate_contrast",
                    message=f"contrast {left} vs {right} is degenerate",
                    severity="error",
                )
            )
        missing = [
            condition
            for condition in (left, right)
            if condition not in known_conditions
        ]
        if missing:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="unknown_contrast_condition",
                    message=f"contrast references unknown conditions: {', '.join(missing)}",
                    severity="error",
                )
            )
    for condition, replicate_count in sorted(condition_replicates.items()):
        if replicate_count < min_replicates_per_condition:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="insufficient_replicates",
                    message=(
                        f"condition {condition} has {replicate_count} replicates; "
                        f"minimum is {min_replicates_per_condition}"
                    ),
                    severity="error",
                )
            )
    covariate_lookup = {
        "batch": lambda entry: entry.batch,
        "instrument": lambda entry: entry.instrument,
        "fraction": lambda entry: entry.fraction,
        "replicate": lambda entry: entry.replicate,
    }
    for covariate in covariates:
        resolver = covariate_lookup.get(covariate)
        if resolver is None:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="unknown_covariate",
                    message=f"covariate {covariate!r} is not recognized",
                    severity="warning",
                )
            )
            continue
        values = [resolver(entry) for entry in design_entries]
        if all(value in (None, "", 0) for value in values):
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="empty_covariate",
                    message=f"covariate {covariate!r} has no populated values",
                    severity="warning",
                )
            )
    if blocking_field:
        resolver = covariate_lookup.get(blocking_field)
        if resolver is None:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="unknown_blocking_field",
                    message=f"blocking field {blocking_field!r} is not recognized",
                    severity="warning",
                )
            )
        else:
            if all(resolver(entry) in (None, "", 0) for entry in design_entries):
                issues.append(
                    DifferentialAbundanceDesignIssue(
                        code="missing_blocking_values",
                        message=f"blocking field {blocking_field!r} has no populated values",
                        severity="warning",
                    )
                )
    if multiple_testing_scope not in {
        "global_per_analysis",
        "per_contrast",
        "hierarchical",
    }:
        issues.append(
            DifferentialAbundanceDesignIssue(
                code="unsupported_multiple_testing_scope",
                message=(
                    "multiple-testing scope must be one of "
                    "'global_per_analysis', 'per_contrast', or 'hierarchical'"
                ),
                severity="error",
            )
        )
    return DifferentialAbundanceDesignValidationReport(
        valid=not any(issue.severity == "error" for issue in issues),
        condition_replicates=condition_replicates,
        issues=tuple(issues),
    )


def build_multiple_testing_scope_benchmark_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    condition_a: str,
    condition_b: str,
    scopes: tuple[str, ...] = (
        "global_per_analysis",
        "per_contrast",
        "hierarchical",
    ),
) -> MultipleTestingScopeBenchmarkReport:
    """Benchmark which multiple-testing scopes are actually supported today."""
    entries: list[MultipleTestingScopeBenchmarkEntry] = []
    da_report = build_differential_abundance_report(
        table,
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    bh_report = apply_benjamini_hochberg(da_report)
    adjusted_values = [
        entry.adjusted_p_value
        for entry in bh_report.entries
        if entry.adjusted_p_value is not None
    ]
    monotonic = all(
        left <= right
        for left, right in zip(adjusted_values, adjusted_values[1:], strict=False)
    )
    for scope in scopes:
        validation = validate_differential_abundance_design_context(
            design_entries,
            contrasts=((condition_a, condition_b),),
            multiple_testing_scope=scope,
        )
        if scope == "hierarchical":
            entries.append(
                MultipleTestingScopeBenchmarkEntry(
                    scope=scope,
                    status=MultipleTestingScopeBenchmarkStatus.REFUSED,
                    adjusted_p_values_complete=False,
                    adjusted_p_values_monotonic=False,
                    evidence_count=len(bh_report.entries),
                    note="hierarchical multiple-testing support is still refused because no hierarchical correction engine is implemented",
                )
            )
            continue
        entries.append(
            MultipleTestingScopeBenchmarkEntry(
                scope=scope,
                status=(
                    MultipleTestingScopeBenchmarkStatus.SUPPORTED
                    if validation.valid
                    else MultipleTestingScopeBenchmarkStatus.REFUSED
                ),
                adjusted_p_values_complete=all(
                    entry.adjusted_p_value is not None for entry in bh_report.entries
                ),
                adjusted_p_values_monotonic=monotonic,
                evidence_count=len(bh_report.entries),
                note=(
                    "benjamini-hochberg-corrected report remains complete and monotonic under the current one-contrast benchmark surface"
                    if validation.valid
                    else "design validation failed before a supported multiple-testing benchmark could be claimed"
                ),
            )
        )
    note = "multiple-testing benchmark distinguishes supported report-wide correction from explicitly refused hierarchical scope"
    return MultipleTestingScopeBenchmarkReport(entries=tuple(entries), note=note)


def build_effect_size_first_differential_abundance_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    condition_a: str,
    condition_b: str,
) -> EffectSizeFirstDaReport:
    """Build a DA report ranked by effect size with statistical and QC caveats retained."""
    paired_policy = (
        PairedDifferentialPolicy()
        if all(entry.pair_id not in (None, "") for entry in design_entries)
        else None
    )
    da = build_differential_abundance_report(
        table,
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
        test_type=(
            DifferentialAbundanceTestType.PAIRED_T_TEST
            if paired_policy is not None
            else DifferentialAbundanceTestType.WELCH_T_TEST
        ),
        paired_policy=paired_policy,
    )
    entries: list[EffectSizeFirstDaEntry] = []
    for entry in da.entries:
        caveats: list[str] = []
        if entry.observations_a == 0 or entry.observations_b == 0:
            caveats.append("one condition has no observed replicates for this entity")
        if entry.adjusted_p_value is None:
            caveats.append("adjusted p-value is unavailable")
        if entry.uncertainty_note:
            caveats.append(entry.uncertainty_note)
        if entry.effect_size_cohens_d is None:
            caveats.append("effect size could not be estimated robustly")
        entries.append(
            EffectSizeFirstDaEntry(
                entity_id=entry.entity_id,
                log2_fold_change=entry.log2_fold_change,
                effect_size_cohens_d=entry.effect_size_cohens_d,
                standard_error=entry.standard_error,
                confidence_interval_low=entry.confidence_interval_low,
                confidence_interval_high=entry.confidence_interval_high,
                p_value=entry.p_value,
                adjusted_p_value=entry.adjusted_p_value,
                observations_a=entry.observations_a,
                observations_b=entry.observations_b,
                uncertainty_note=entry.uncertainty_note,
                caveats=tuple(caveats),
            )
        )
    ranked = tuple(
        sorted(
            entries,
            key=lambda item: (
                -(
                    abs(item.effect_size_cohens_d)
                    if item.effect_size_cohens_d is not None
                    else abs(item.log2_fold_change)
                ),
                item.adjusted_p_value if item.adjusted_p_value is not None else 1.0,
                item.entity_id,
            ),
        )
    )
    global_caveats: list[str] = []
    if any(entry.adjusted_p_value is None for entry in ranked):
        global_caveats.append("some entities are missing adjusted p-values")
    if any(entry.observations_a < 2 or entry.observations_b < 2 for entry in ranked):
        global_caveats.append("one or more entities have low replicate support")
    if not global_caveats:
        global_caveats.append(
            "effect-size ranking includes complete statistical annotations"
        )
    return EffectSizeFirstDaReport(
        condition_a=condition_a,
        condition_b=condition_b,
        entries=ranked,
        global_caveats=tuple(global_caveats),
    )


def build_quant_review_bundle(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    imputation_method: ImputationMethod = ImputationMethod.NONE,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
) -> QuantReviewBundle:
    """Build a full quant review bundle from feature-level quant records."""
    observed_sample_ids = {record.sample_id for record in records}
    measured_design_entries = tuple(
        entry for entry in design_entries if entry.sample_id in observed_sample_ids
    )
    covariate_fields = tuple(
        sorted(
            {
                field
                for entry in measured_design_entries
                for field, value in entry.metadata.items()
                if field != "timepoint" and value not in ("", None)
            }
        )
    )
    timepoint_field = (
        "timepoint"
        if all(
            entry.metadata.get("timepoint") not in ("", None)
            for entry in measured_design_entries
        )
        else None
    )
    pairing_field = (
        "pair_id"
        if all(entry.pair_id not in (None, "") for entry in measured_design_entries)
        else None
    )
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
    conditions = tuple(sorted({entry.condition for entry in measured_design_entries}))
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
    missingness = build_missingness_mechanism_profile_report(
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
    design_matrix_report = build_quant_design_matrix_report(
        measured_design_entries,
        batch_field="batch",
        covariate_fields=covariate_fields,
        pairing_field=pairing_field,
        timepoint_field=timepoint_field,
    )
    differential_report = None
    if len(conditions) == 2:
        try:
            differential_report = build_differential_abundance_report(
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
    time_course_differential_report = (
        build_time_course_differential_report(
            imputed_table,
            measured_design_entries,
            policy=TimeCourseTestingPolicy(
                timepoint_field=timepoint_field,
                batch_field="batch",
                pairing_field=pairing_field,
                covariate_fields=covariate_fields,
            ),
        )
        if timepoint_field is not None
        else None
    )
    multi_condition_differential_report = None
    if len(conditions) > 2:
        try:
            multi_condition_differential_report = (
                build_multi_condition_differential_abundance_report(
                    imputed_table,
                    measured_design_entries,
                    test_type=DifferentialAbundanceTestType.LINEAR_MODEL_CONTRAST,
                    design_matrix=design_matrix_report,
                )
            )
        except ValueError as error:
            if "insufficient_group_size" not in str(error):
                raise
    multi_contrast_consistency_report = (
        build_multi_contrast_consistency_report(
            multi_condition_differential_report,
            entity_protein_refs=imputed_table.entity_protein_refs,
        )
        if multi_condition_differential_report is not None
        else None
    )
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
    lfq_provenance = build_lfq_feature_peptide_protein_provenance_report(
        records,
        aggregation_method=aggregation_method,
        normalization_method=normalization_method,
    )
    normalization_matrix = build_normalization_policy_comparison_matrix_report(
        peptide_table
    )
    rollup_strategy = build_protein_rollup_strategy_comparison_report(records)
    decision_readiness = build_quant_decision_readiness_report(
        imputed_table,
        design_entries=design_entries,
    )
    da_report = None
    if len(conditions) == 2:
        try:
            da_report = build_effect_size_first_differential_abundance_report(
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
    caveats: list[str] = []
    if da_report is None and multi_condition_differential_report is None:
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
    evidence_pointers = (
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
    return QuantReviewBundle(
        artifact_bundle_hash=artifact_bundle.document_schema.content_hash or "",
        lfq_provenance=lfq_provenance,
        normalization_comparison=normalization_comparison,
        imputation_report=imputation_report,
        imputation_sensitivity=imputation_sensitivity,
        normalization_matrix=normalization_matrix,
        rollup_strategy_comparison=rollup_strategy,
        limma_compatible_package=limma_package,
        msstats_compatible_input_report=msstats_input_report,
        design_matrix_report=design_matrix_report,
        design_model_fit_report=design_model_fit_report,
        effect_size_da_report=da_report,
        differential_abundance_multi_condition_report=(
            multi_condition_differential_report
        ),
        multi_contrast_consistency_report=multi_contrast_consistency_report,
        time_course_differential_report=time_course_differential_report,
        missingness_profile=missingness,
        missingness_entity_summary=missingness_entity_summary,
        missingness_condition_summary=missingness_condition_summary,
        missingness_intensity_dependence=missingness_intensity_dependence,
        qc_report=qc_report,
        decision_readiness=decision_readiness,
        evidence_pointers=evidence_pointers,
        caveats=tuple(caveats),
    )
