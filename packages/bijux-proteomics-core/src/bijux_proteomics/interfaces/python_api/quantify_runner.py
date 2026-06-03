# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Quantification runner shared by the split quantify command."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


def _normalize_optional_field_name(value: str | None) -> str | None:
    if value is None:
        return None
    return value or None


def run_quantify_command(
    input_table: Path,
    measure: str,
    entity_level: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    imputation: str,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    design_path: Path | None,
    condition_a: str | None,
    condition_b: str | None,
    differential_tsv_out: Path | None,
    broken_pairs_tsv_out: Path | None,
    multi_contrast_consistency_tsv_out: Path | None,
    batch_effect_summary_tsv_out: Path | None,
    batch_effect_batches_tsv_out: Path | None,
    batch_effect_components_tsv_out: Path | None,
    time_course_tsv_out: Path | None,
    design_covariates: tuple[str, ...],
    design_batch_field: str,
    design_pairing_field: str | None,
    design_timepoint_field: str | None,
    design_timepoint_order_file: Path | None,
    design_matrix_tsv_out: Path | None,
    design_coefficients_tsv_out: Path | None,
    design_contrasts_tsv_out: Path | None,
    limma_assay_tsv_out: Path | None,
    limma_samples_tsv_out: Path | None,
    limma_design_tsv_out: Path | None,
    limma_contrasts_tsv_out: Path | None,
    msstats_input_tsv_out: Path | None,
    limma_results_path: Path | None,
    msstats_results_path: Path | None,
    report_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        mapping = Ms1FeatureColumnMapping(
            sample_id=sample_column,
            feature_id=feature_id_column,
            peptide=peptide_column,
            intensity=intensity_column,
            protein_refs=protein_refs_column,
            charge=charge_column,
            mz=mz_column,
            retention_time_seconds=retention_time_column,
            missing_reason=missing_reason_column,
            protein_separator=protein_separator,
        )
        parse_report = parse_ms1_feature_table(
            input_table,
            mapping=mapping,
        )
        quant_entity_level = QuantEntityLevel(entity_level)
        quant_measure = QuantMeasureKind(measure)
        rollup_method = QuantRollupMethod(aggregation)
        effective_batch_field = _normalize_optional_field_name(design_batch_field)
        effective_pairing_field = _normalize_optional_field_name(design_pairing_field)
        effective_timepoint_field = _normalize_optional_field_name(
            design_timepoint_field
        )
        design_entries: tuple[ExperimentalDesignEntry, ...] = ()
        if design_path is not None:
            design_report = parse_experimental_design_table(design_path)
            if design_report.rejected_rows:
                raise click.ClickException("design table contains rejected rows")
            design_entries = design_report.accepted_entries
        missingness_entity_summary = None
        missingness_condition_summary = None
        missingness_intensity_dependence = None
        missingness_mechanism_report = None
        normalization_comparison = None
        normalization_strategy = None
        imputation_report = None
        imputation_sensitivity = None
        if quant_measure is QuantMeasureKind.SPECTRAL_COUNT:
            table = build_spectral_count_table(
                parse_report.accepted_records,
                entity_level=quant_entity_level,
            )
        else:
            raw_table = build_label_free_intensity_table(
                parse_report.accepted_records,
                entity_level=quant_entity_level,
                aggregation_method=rollup_method,
                top_n=top_n,
            )
            normalization_strategy = build_normalization_strategy_comparison_report(
                raw_table
            )
            normalized_table = normalize_label_free_table(
                raw_table,
                method=NormalizationMethod(normalization),
            )
            normalization_comparison = build_normalization_comparison_report(
                raw_table,
                normalized_table,
            )
            table = impute_label_free_table(
                normalized_table,
                method=ImputationMethod(imputation),
                design_entries=design_entries,
            )
            imputation_report = build_imputation_report(
                normalized_table,
                table,
            )
        missing_summary = summarize_missing_values(table)
        batch_effect = None
        replicate_correlations = None
        replicate_qc = None
        design_matrix = None
        design_model_fit = None
        limma_package = None
        msstats_input_report = None
        time_course_differential = None
        selected_contrast: tuple[str, str] | None = None
        differential = None
        differential_multi_condition = None
        multi_contrast_consistency = None
        if design_path is not None:
            contrast_was_explicit = condition_a is not None or condition_b is not None
            if effective_pairing_field is None and all(
                entry.pair_id not in (None, "") for entry in design_entries
            ):
                effective_pairing_field = "pair_id"
            effective_covariates = tuple(dict.fromkeys(design_covariates))
            if (
                effective_timepoint_field is None
                and "timepoint" in effective_covariates
            ):
                effective_timepoint_field = "timepoint"
                effective_covariates = tuple(
                    field for field in effective_covariates if field != "timepoint"
                )
            elif effective_timepoint_field is None and all(
                entry.metadata.get("timepoint") not in (None, "")
                for entry in design_entries
            ):
                effective_timepoint_field = "timepoint"
            declared_timepoint_order = (
                _parse_timepoint_order_file(design_timepoint_order_file)
                if design_timepoint_order_file is not None
                else ()
            )
            design_matrix = build_quant_design_matrix_report(
                design_entries,
                batch_field=effective_batch_field,
                covariate_fields=effective_covariates,
                pairing_field=effective_pairing_field,
                timepoint_field=effective_timepoint_field,
            )
            design_model_fit = fit_quant_design_matrix_model(
                table,
                design_matrix,
            )
            if quant_measure is QuantMeasureKind.INTENSITY:
                limma_package = build_limma_compatible_quant_package(
                    table,
                    design_entries,
                    batch_field=effective_batch_field,
                    covariate_fields=effective_covariates,
                    pairing_field=effective_pairing_field,
                    timepoint_field=effective_timepoint_field,
                )
                msstats_input_report = build_msstats_compatible_input_report(
                    parse_report.accepted_records,
                    design_entries,
                )
            batch_effect = build_batch_effect_estimator_report(
                table,
                design_entries,
                batch_field=effective_batch_field or "batch",
            )
            replicate_qc = build_replicate_and_batch_qc_report(
                table,
                design_entries=design_entries,
            )
            replicate_correlations = replicate_qc.replicate_correlation_report
            if effective_timepoint_field is not None:
                time_course_differential = build_time_course_differential_report(
                    table,
                    design_entries,
                    policy=TimeCourseTestingPolicy(
                        timepoint_field=effective_timepoint_field,
                        ordered_timepoints=declared_timepoint_order,
                        batch_field=effective_batch_field,
                        pairing_field=effective_pairing_field,
                        covariate_fields=effective_covariates,
                    ),
                )
            if quant_measure is QuantMeasureKind.INTENSITY:
                conditions = tuple(
                    sorted(
                        {entry.condition for entry in design_entries if entry.condition}
                    )
                )
                missingness_classifier = build_missingness_classifier_report(
                    table,
                    design_entries=design_entries,
                )
                missingness_entity_summary = missingness_classifier.entity_summary
                missingness_condition_summary = missingness_classifier.condition_summary
                missingness_intensity_dependence = (
                    missingness_classifier.intensity_dependence
                )
                missingness_mechanism_report = missingness_classifier.mechanism_report
                if condition_a is not None or condition_b is not None:
                    if not condition_a or not condition_b:
                        raise click.ClickException(
                            "both --condition-a and --condition-b are required together"
                        )
                    selected_contrast = (condition_a, condition_b)
                elif len(conditions) == 2:
                    selected_contrast = (conditions[0], conditions[1])

                if selected_contrast is not None:
                    sensitivity_methods: tuple[ImputationMethod, ...] = (
                        ImputationMethod.NONE,
                        ImputationMethod.LOW_INTENSITY,
                        ImputationMethod.KNN,
                    )
                    selected_imputation_method = ImputationMethod(imputation)
                    if (
                        selected_imputation_method
                        is ImputationMethod.GROUP_AWARE_LOW_INTENSITY
                    ):
                        sensitivity_methods = sensitivity_methods + (
                            ImputationMethod.GROUP_AWARE_LOW_INTENSITY,
                        )
                    imputation_sensitivity = build_imputation_sensitivity_report(
                        normalized_table,
                        design_entries,
                        condition_a=selected_contrast[0],
                        condition_b=selected_contrast[1],
                        methods=sensitivity_methods,
                    )
                    paired_policy = (
                        PairedDifferentialPolicy(
                            pair_id_field=effective_pairing_field,
                        )
                        if effective_pairing_field is not None
                        else None
                    )
                    try:
                        differential = build_differential_abundance_report(
                            table,
                            design_entries,
                            condition_a=selected_contrast[0],
                            condition_b=selected_contrast[1],
                            test_type=(
                                DifferentialAbundanceTestType.PAIRED_T_TEST
                                if paired_policy is not None
                                else DifferentialAbundanceTestType.LINEAR_MODEL_CONTRAST
                            ),
                            design_matrix=design_matrix,
                            paired_policy=paired_policy,
                        )
                    except ValueError:
                        requires_differential_output = any(
                            output is not None
                            for output in (
                                differential_tsv_out,
                                broken_pairs_tsv_out,
                                limma_results_path,
                                msstats_results_path,
                            )
                        )
                        if contrast_was_explicit or requires_differential_output:
                            raise
                        selected_contrast = None
                elif len(conditions) > 2:
                    differential_multi_condition = (
                        build_multi_condition_differential_abundance_report(
                            table,
                            design_entries,
                        )
                    )
                    multi_contrast_consistency = (
                        build_multi_contrast_consistency_report(
                            differential_multi_condition,
                            entity_protein_refs=table.entity_protein_refs,
                        )
                    )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if differential_tsv_out is not None:
        if differential is not None:
            export_differential_abundance_tsv(differential, differential_tsv_out)
        elif differential_multi_condition is not None:
            export_multi_condition_differential_abundance_tsv(
                differential_multi_condition,
                differential_tsv_out,
            )
        else:
            raise click.ClickException(
                "differential tsv export requires a resolvable contrast or at least two conditions"
            )
    if broken_pairs_tsv_out is not None:
        if differential is None:
            raise click.ClickException(
                "broken-pair export requires a resolvable two-condition differential contrast"
            )
        export_differential_broken_pairs_tsv(differential, broken_pairs_tsv_out)
    if multi_contrast_consistency_tsv_out is not None:
        if multi_contrast_consistency is None:
            raise click.ClickException(
                "multi-contrast consistency export requires intensity quantification with at least three conditions"
            )
        export_multi_contrast_consistency_tsv(
            multi_contrast_consistency,
            multi_contrast_consistency_tsv_out,
        )
    if batch_effect_summary_tsv_out is not None:
        if batch_effect is None:
            raise click.ClickException("batch effect export requires --design")
        export_batch_effect_summary_tsv(batch_effect, batch_effect_summary_tsv_out)
    if batch_effect_batches_tsv_out is not None:
        if batch_effect is None:
            raise click.ClickException("batch effect export requires --design")
        export_batch_effect_batches_tsv(batch_effect, batch_effect_batches_tsv_out)
    if batch_effect_components_tsv_out is not None:
        if batch_effect is None:
            raise click.ClickException("batch effect export requires --design")
        export_batch_effect_principal_components_tsv(
            batch_effect,
            batch_effect_components_tsv_out,
        )
    if time_course_tsv_out is not None:
        if time_course_differential is None:
            raise click.ClickException(
                "time-course export requires --design with populated ordered timepoint metadata"
            )
        export_time_course_differential_tsv(
            time_course_differential,
            time_course_tsv_out,
        )
    if design_matrix_tsv_out is not None:
        if design_matrix is None:
            raise click.ClickException("design matrix export requires --design")
        export_quant_design_matrix_tsv(design_matrix, design_matrix_tsv_out)
    if design_coefficients_tsv_out is not None:
        if design_model_fit is None:
            raise click.ClickException("design coefficient export requires --design")
        export_quant_design_model_coefficients_tsv(
            design_model_fit,
            design_coefficients_tsv_out,
        )
    if design_contrasts_tsv_out is not None:
        if design_model_fit is None:
            raise click.ClickException("design contrast export requires --design")
        export_quant_design_contrast_estimates_tsv(
            design_model_fit,
            design_contrasts_tsv_out,
        )
    if limma_assay_tsv_out is not None:
        if limma_package is None:
            raise click.ClickException(
                "limma assay export requires intensity quantification with --design"
            )
        export_limma_assay_matrix_tsv(limma_package, limma_assay_tsv_out)
    if limma_samples_tsv_out is not None:
        if limma_package is None:
            raise click.ClickException(
                "limma sample export requires intensity quantification with --design"
            )
        export_limma_sample_annotations_tsv(limma_package, limma_samples_tsv_out)
    if limma_design_tsv_out is not None:
        if limma_package is None:
            raise click.ClickException(
                "limma design export requires intensity quantification with --design"
            )
        export_limma_design_matrix_tsv(limma_package, limma_design_tsv_out)
    if limma_contrasts_tsv_out is not None:
        if limma_package is None:
            raise click.ClickException(
                "limma contrast export requires intensity quantification with --design"
            )
        export_limma_contrast_matrix_tsv(limma_package, limma_contrasts_tsv_out)
    if msstats_input_tsv_out is not None:
        if msstats_input_report is None:
            raise click.ClickException(
                "msstats input export requires intensity quantification with --design"
            )
        export_msstats_compatible_input_tsv(
            msstats_input_report,
            msstats_input_tsv_out,
        )
    limma_result_import = None
    limma_validation = None
    if limma_results_path is not None:
        if selected_contrast is None or differential is None:
            raise click.ClickException(
                "limma result import requires intensity quantification with --design and a resolvable contrast"
            )
        limma_result_import = parse_limma_result_table(
            limma_results_path,
            condition_a=selected_contrast[0],
            condition_b=selected_contrast[1],
        )
        limma_validation = build_statistical_backend_validation_report(
            limma_result_import,
            differential,
        )
    msstats_result_import = None
    msstats_validation = None
    if msstats_results_path is not None:
        if selected_contrast is None or differential is None:
            raise click.ClickException(
                "msstats result import requires intensity quantification with --design and a resolvable contrast"
            )
        msstats_result_import = parse_msstats_result_table(
            msstats_results_path,
            condition_a=selected_contrast[0],
            condition_b=selected_contrast[1],
        )
        msstats_validation = build_statistical_backend_validation_report(
            msstats_result_import,
            differential,
        )

    payload = {
        "accepted_features": len(parse_report.accepted_records),
        "rejected_features": len(parse_report.rejected_rows),
        "table": table.to_dict(),
        "missing_summary": missing_summary.to_dict(),
        "missingness_entity_summary": (
            missingness_entity_summary.to_dict()
            if missingness_entity_summary is not None
            else None
        ),
        "missingness_condition_summary": (
            missingness_condition_summary.to_dict()
            if missingness_condition_summary is not None
            else None
        ),
        "missingness_intensity_dependence": (
            missingness_intensity_dependence.to_dict()
            if missingness_intensity_dependence is not None
            else None
        ),
        "missingness_mechanism_report": (
            missingness_mechanism_report.to_dict()
            if missingness_mechanism_report is not None
            else None
        ),
        "normalization_comparison": (
            normalization_comparison.to_dict()
            if normalization_comparison is not None
            else None
        ),
        "normalization_strategy": (
            normalization_strategy.to_dict()
            if normalization_strategy is not None
            else None
        ),
        "imputation_report": (
            imputation_report.to_dict() if imputation_report is not None else None
        ),
        "imputation_sensitivity": (
            imputation_sensitivity.to_dict()
            if imputation_sensitivity is not None
            else None
        ),
        "design_entries": len(design_entries),
        "design_matrix": design_matrix.to_dict() if design_matrix is not None else None,
        "design_model_fit": (
            design_model_fit.to_dict() if design_model_fit is not None else None
        ),
        "limma_compatible_package": (
            limma_package.to_dict() if limma_package is not None else None
        ),
        "msstats_compatible_input_report": (
            msstats_input_report.to_dict() if msstats_input_report is not None else None
        ),
        "limma_result_import": (
            limma_result_import.to_dict() if limma_result_import is not None else None
        ),
        "limma_validation": (
            limma_validation.to_dict() if limma_validation is not None else None
        ),
        "msstats_result_import": (
            msstats_result_import.to_dict()
            if msstats_result_import is not None
            else None
        ),
        "msstats_validation": (
            msstats_validation.to_dict() if msstats_validation is not None else None
        ),
        "batch_effect": batch_effect.to_dict() if batch_effect is not None else None,
        "replicate_correlations": (
            replicate_correlations.to_dict()
            if replicate_correlations is not None
            else None
        ),
        "replicate_qc": replicate_qc.to_dict() if replicate_qc is not None else None,
        "replicate_cv": (
            replicate_qc.replicate_cv_report.to_dict()
            if replicate_qc is not None
            else None
        ),
        "sample_pca": (
            replicate_qc.sample_pca_report.to_dict()
            if replicate_qc is not None and replicate_qc.sample_pca_report is not None
            else None
        ),
        "condition_clustering": (
            replicate_qc.condition_clustering_report.to_dict()
            if replicate_qc is not None
            and replicate_qc.condition_clustering_report is not None
            else None
        ),
        "differential_abundance_multi_condition": (
            differential_multi_condition.to_dict()
            if differential_multi_condition is not None
            else None
        ),
        "multi_contrast_consistency": (
            multi_contrast_consistency.to_dict()
            if multi_contrast_consistency is not None
            else None
        ),
        "time_course_differential": (
            time_course_differential.to_dict()
            if time_course_differential is not None
            else None
        ),
        "differential_abundance": differential.to_dict()
        if differential is not None
        else None,
        "outputs": {
            "differential_tsv": (
                str(differential_tsv_out) if differential_tsv_out is not None else None
            ),
            "broken_pairs_tsv": (
                str(broken_pairs_tsv_out) if broken_pairs_tsv_out is not None else None
            ),
            "multi_contrast_consistency_tsv": (
                str(multi_contrast_consistency_tsv_out)
                if multi_contrast_consistency_tsv_out is not None
                else None
            ),
            "batch_effect_summary_tsv": (
                str(batch_effect_summary_tsv_out)
                if batch_effect_summary_tsv_out is not None
                else None
            ),
            "batch_effect_batches_tsv": (
                str(batch_effect_batches_tsv_out)
                if batch_effect_batches_tsv_out is not None
                else None
            ),
            "batch_effect_components_tsv": (
                str(batch_effect_components_tsv_out)
                if batch_effect_components_tsv_out is not None
                else None
            ),
            "time_course_tsv": (
                str(time_course_tsv_out) if time_course_tsv_out is not None else None
            ),
            "design_matrix_tsv": (
                str(design_matrix_tsv_out)
                if design_matrix_tsv_out is not None
                else None
            ),
            "design_coefficients_tsv": (
                str(design_coefficients_tsv_out)
                if design_coefficients_tsv_out is not None
                else None
            ),
            "design_contrasts_tsv": (
                str(design_contrasts_tsv_out)
                if design_contrasts_tsv_out is not None
                else None
            ),
            "limma_assay_tsv": (
                str(limma_assay_tsv_out) if limma_assay_tsv_out is not None else None
            ),
            "limma_samples_tsv": (
                str(limma_samples_tsv_out)
                if limma_samples_tsv_out is not None
                else None
            ),
            "limma_design_tsv": (
                str(limma_design_tsv_out) if limma_design_tsv_out is not None else None
            ),
            "limma_contrasts_tsv": (
                str(limma_contrasts_tsv_out)
                if limma_contrasts_tsv_out is not None
                else None
            ),
            "msstats_input_tsv": (
                str(msstats_input_tsv_out)
                if msstats_input_tsv_out is not None
                else None
            ),
            "json_report": str(report_out or out_path)
            if (report_out or out_path) is not None
            else None,
        },
    }
    _emit_json(payload, out_path=report_out or out_path)


__all__ = ["run_quantify_command"]
