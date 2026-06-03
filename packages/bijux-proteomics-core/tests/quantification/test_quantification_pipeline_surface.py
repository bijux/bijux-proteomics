# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import numpy as np

from bijux_proteomics.domain import MissingValueState, QuantEntityKind
from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    parse_experimental_design_table,
)
from bijux_proteomics.quantification import (
    DifferentialReplicatePolicy,
    ImputationMethod,
    LabelBasedChannelPolicyEntry,
    LabelBasedChannelRole,
    LabelBasedQuantBundle,
    LabelBasedQuantPolicy,
    LabelFreeProvenanceBundle,
    LabelFreeQuantTable,
    MissingChannelPolicy,
    MissingDataMechanism,
    MissingDataMechanismReport,
    MissingValueCorrectionPolicy,
    MissingValueKind,
    MissingValueSummaryPolicy,
    Ms1FeatureRecord,
    MultiplexChannelBalanceReport,
    MultiplexNormalizationPolicy,
    NormalizationMethod,
    NormalizationStrategyComparisonReport,
    ProteinQuantAssignmentPolicy,
    ProteinQuantPolicyComparisonReport,
    QuantArtifactBundle,
    QuantAssessmentDisposition,
    QuantEntityLevel,
    QuantReproducibilityManifest,
    QuantRollupMethod,
    QuantValueOrigin,
    StudyScaleBatchEffectReport,
    StudyScaleReplicateCorrelationReport,
    apply_benjamini_hochberg,
    build_batch_effect_advisory,
    build_batch_effect_estimator_report,
    build_differential_abundance_report,
    build_imputation_report,
    build_imputation_sensitivity_report,
    build_label_based_quant_bundle,
    build_label_free_intensity_table,
    build_label_free_provenance_bundle,
    build_limma_compatible_quant_package,
    build_missing_data_mechanism_report,
    build_missingness_classifier_report,
    build_missingness_condition_summary_report,
    build_missingness_entity_summary_report,
    build_missingness_intensity_dependence_report,
    build_msstats_compatible_input_report,
    build_multi_condition_differential_abundance_report,
    build_multiplex_channel_balance_report,
    build_normalization_comparison_report,
    build_normalization_strategy_comparison_report,
    build_protein_quant_policy_comparison_report,
    build_protein_quant_rollup_evidence,
    build_quant_artifact_bundle,
    build_quant_design_matrix_report,
    build_quant_matrix_export,
    build_quant_reproducibility_manifest,
    build_replicate_and_batch_qc_report,
    build_replicate_correlation_report,
    build_spectral_count_table,
    build_study_scale_batch_effect_report,
    build_study_scale_replicate_correlation_report,
    build_time_course_differential_report,
    export_label_free_provenance_bundle,
    export_quant_artifact_bundle,
    export_quant_matrix_tsv,
    export_quant_reproducibility_manifest,
    fit_quant_design_matrix_model,
    impute_label_free_table,
    normalize_label_free_table,
    normalize_multiplex_quant_table,
    parse_ms1_feature_table,
    summarize_missing_values,
)


def _quant_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def test_ms1_feature_parser_accepts_quant_fixture_and_preserves_missing_states() -> (
    None
):
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))

    assert report.total_rows == 32
    assert len(report.accepted_records) == 32
    zero_feature = next(
        record for record in report.accepted_records if record.feature_id == "f008"
    )
    filtered_feature = next(
        record for record in report.accepted_records if record.feature_id == "f006"
    )
    missing_feature = next(
        record for record in report.accepted_records if record.feature_id == "f007"
    )

    assert zero_feature.missing_value_kind.value == "zero"
    assert filtered_feature.missing_value_kind.value == "filtered"
    assert missing_feature.missing_value_kind.value == "missing_not_observed"


def test_ms1_feature_parser_rejects_invalid_rows() -> None:
    report = parse_ms1_feature_table(_quant_fixture("malformed_ms1_features.tsv"))

    assert len(report.accepted_records) == 0
    assert len(report.rejected_rows) == 4
    codes = {issue.code for row in report.rejected_rows for issue in row.issues}
    assert {
        "missing_sample_id",
        "negative_intensity",
        "invalid_intensity",
        "invalid_charge",
    } <= codes


def test_label_free_intensity_rollups_cover_sum_median_and_top_n() -> None:
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))

    summed = build_label_free_intensity_table(
        report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    median = build_label_free_intensity_table(
        report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.MEDIAN,
    )
    top_n = build_label_free_intensity_table(
        report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.TOP_N,
        top_n=2,
    )
    lookup_sum = {(value.entity_id, value.sample_id): value for value in summed.values}
    lookup_median = {
        (value.entity_id, value.sample_id): value for value in median.values
    }
    lookup_top_n = {(value.entity_id, value.sample_id): value for value in top_n.values}

    assert lookup_sum[("P001", "C1")].abundance == 2200.0
    assert lookup_median[("P001", "C1")].abundance == 900.0
    assert lookup_top_n[("P001", "C1")].abundance == 1900.0


def test_label_free_intensity_table_binds_canonical_quant_matrix() -> None:
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))

    table = build_label_free_intensity_table(
        report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    matrix = table.to_quant_matrix()

    assert matrix.entity_kind is QuantEntityKind.PROTEIN
    assert matrix.matrix_id == "matrix:protein:intensity:sum:none:none"
    assert matrix.entity_ids == table.entity_ids
    assert matrix.sample_ids == table.sample_ids
    assert matrix.values[0][0] is not None
    assert matrix.support_counts[0][0] >= 1
    assert any(
        state is MissingValueState.NOT_OBSERVED
        for row in matrix.missing_value_states
        for state in row
    )


def test_normalization_and_imputation_keep_canonical_quant_matrix_in_sync() -> None:
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))

    normalized = normalize_label_free_table(
        build_label_free_intensity_table(
            report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        method=NormalizationMethod.NONE,
    )
    imputed = impute_label_free_table(normalized, method=ImputationMethod.LOW_INTENSITY)

    normalized_matrix = normalized.to_quant_matrix()
    imputed_matrix = imputed.to_quant_matrix()

    assert normalized_matrix.metadata["normalization_method"] == "none"
    assert normalized_matrix.matrix_id == "matrix:protein:intensity:sum:none:none"
    assert normalized_matrix.transformation_history[-1] == "normalization:none"
    assert imputed_matrix.metadata["imputation_method"] == "low_intensity"
    assert imputed_matrix.matrix_id == "matrix:protein:intensity:sum:none:low_intensity"
    assert imputed_matrix.transformation_history[-1] == "imputation:low_intensity"


def test_spectral_count_table_and_missing_summary_distinguish_zero_filtered_and_missing() -> (
    None
):
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    table = build_spectral_count_table(
        report.accepted_records,
        entity_level=QuantEntityLevel.PEPTIDE,
    )
    summary = summarize_missing_values(table)
    lookup = {(value.entity_id, value.sample_id): value for value in table.values}
    summary_lookup = {entry.sample_id: entry for entry in summary.entries}

    assert lookup[("ZEROPEP", "C1")].abundance == 1.0
    assert lookup[("FILTERPEP", "C1")].abundance is None
    assert lookup[("MISSPEP", "C1")].abundance is None
    assert summary_lookup["C1"].zero_count == 1
    assert summary_lookup["C1"].filtered_count == 1
    assert summary_lookup["C1"].not_observed_count == 1


def test_quant_matrix_export_preserves_sample_metadata_missingness_and_provenance() -> (
    None
):
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    design = parse_experimental_design_table(_quant_fixture("quant.design.tsv"))
    table = normalize_label_free_table(
        build_label_free_intensity_table(
            report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        method=NormalizationMethod.MEDIAN,
    )
    matrix_export = build_quant_matrix_export(
        table,
        design_entries=design.accepted_entries,
    )

    assert matrix_export.normalization_provenance.normalization_method.value == "median"
    row = next(
        row
        for row in matrix_export.rows
        if row.entity_id == "P001" and row.sample_metadata.sample_id == "C1"
    )
    assert row.sample_metadata.condition == "control"
    assert row.sample_metadata.batch == "batch-a"
    assert row.missing_value_kind.value == "observed"
    assert row.value_provenance is not None
    assert row.value_provenance.value_origin is QuantValueOrigin.OBSERVED
    assert row.value_provenance.source_feature_ids == ("f001", "f002", "f005")
    assert row.value_provenance.source_peptides == (
        "APEPTIDE",
        "APEPTIDER",
        "SHAREDK",
    )
    missing_row = next(
        row
        for row in matrix_export.rows
        if row.entity_id == "P004" and row.sample_metadata.sample_id == "C1"
    )
    assert missing_row.missing_value_kind.value == "missing_not_observed"
    assert missing_row.value_provenance is not None
    assert missing_row.value_provenance.value_origin is QuantValueOrigin.MISSING

    output_path = _quant_fixture("quant_matrix.tsv")
    try:
        export_quant_matrix_tsv(matrix_export, output_path)
        header = output_path.read_text().splitlines()[0]
        assert header.startswith("sample_id\tcondition\treplicate")
        assert "value_origin" in header
        assert "source_feature_ids" in header
        assert "source_peptides" in header
    finally:
        output_path.unlink(missing_ok=True)


def test_quant_matrix_export_preserves_per_cell_imputation_provenance() -> None:
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    design = parse_experimental_design_table(_quant_fixture("quant.design.tsv"))
    normalized = normalize_label_free_table(
        build_label_free_intensity_table(
            report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        method=NormalizationMethod.MEDIAN,
    )
    imputed = impute_label_free_table(
        normalized,
        method=ImputationMethod.GROUP_AWARE_LOW_INTENSITY,
        design_entries=design.accepted_entries,
    )
    matrix_export = build_quant_matrix_export(
        imputed,
        design_entries=design.accepted_entries,
    )

    row = next(
        row
        for row in matrix_export.rows
        if row.entity_id == "P004" and row.sample_metadata.sample_id == "C1"
    )
    assert row.imputation_provenance is not None
    assert (
        row.imputation_provenance.method is ImputationMethod.GROUP_AWARE_LOW_INTENSITY
    )
    assert row.imputation_provenance.reference_group == "control"
    assert row.value_provenance is not None
    assert row.value_provenance.value_origin is QuantValueOrigin.IMPUTED
    assert matrix_export.imputation_provenance.imputed_value_count > 0

    output_path = _quant_fixture("quant_matrix_imputed.tsv")
    try:
        export_quant_matrix_tsv(matrix_export, output_path)
        header = output_path.read_text().splitlines()[0].split("\t")
        assert "imputation_method" in header
        assert "imputation_strategy" in header
        assert "excluded_contributor_ids" in header
        assert "exclusion_reason_codes" in header
        first_imputed_row = next(
            line
            for line in output_path.read_text().splitlines()[1:]
            if "\tP004\t" in line
        )
        assert "group_aware_low_intensity" in first_imputed_row
    finally:
        output_path.unlink(missing_ok=True)


def test_label_free_intensity_table_preserves_per_value_provenance_and_exclusions() -> (
    None
):
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))

    table = build_label_free_intensity_table(
        report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.TOP_N,
        top_n=2,
    )
    value = next(
        value
        for value in table.values
        if value.entity_id == "P001" and value.sample_id == "C1"
    )
    assert value.value_provenance is not None
    assert value.value_provenance.aggregation_method is QuantRollupMethod.TOP_N
    assert value.value_provenance.value_origin is QuantValueOrigin.OBSERVED
    assert value.value_provenance.source_feature_ids == ("f001", "f002")
    assert value.value_provenance.source_peptides == ("APEPTIDE", "APEPTIDER")
    assert tuple(
        excluded.contributor.contributor_id
        for excluded in value.value_provenance.excluded_contributors
    ) == ("f005",)
    assert tuple(
        excluded.reason_code
        for excluded in value.value_provenance.excluded_contributors
    ) == ("excluded_by_top_n_rollup",)

    missing_value = next(
        value
        for value in table.values
        if value.entity_id == "P003" and value.sample_id == "C1"
    )
    assert missing_value.value_provenance is not None
    assert missing_value.value_provenance.value_origin is QuantValueOrigin.MISSING
    assert tuple(
        excluded.reason_code
        for excluded in missing_value.value_provenance.excluded_contributors
    ) == ("missing_value_filtered",)


def test_protein_quant_rollup_evidence_lists_contributing_features_and_peptides() -> (
    None
):
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))

    evidence = build_protein_quant_rollup_evidence(
        report.accepted_records,
        aggregation_method=QuantRollupMethod.TOP_N,
        top_n=2,
    )

    entry = next(
        entry
        for entry in evidence
        if entry.protein_ref == "P001" and entry.sample_id == "C1"
    )
    assert entry.abundance == 1900.0
    assert entry.contributing_feature_ids == ("f001", "f002")
    assert entry.contributing_peptides == ("APEPTIDE", "APEPTIDER")


def test_label_free_provenance_bundle_preserves_feature_and_peptide_lineage() -> None:
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))

    bundle = build_label_free_provenance_bundle(
        report.accepted_records,
        aggregation_method=QuantRollupMethod.TOP_N,
        normalization_method=NormalizationMethod.MEDIAN,
        top_n=2,
    )

    assert isinstance(bundle, LabelFreeProvenanceBundle)
    assert bundle.document_schema.document_kind == "label_free_provenance_bundle"
    peptide = next(
        entry
        for entry in bundle.peptide_entries
        if entry.canonical_peptide == "APEPTIDE" and entry.sample_id == "C1"
    )
    protein = next(
        entry
        for entry in bundle.protein_entries
        if entry.protein_ref == "P001" and entry.sample_id == "C1"
    )
    assert peptide.contributing_feature_ids == ("f001",)
    assert protein.contributing_feature_ids == ("f001", "f002")

    output_path = _quant_fixture("lfq_provenance.json")
    try:
        export_label_free_provenance_bundle(bundle, output_path)
        assert "label_free_provenance_bundle" in output_path.read_text()
    finally:
        output_path.unlink(missing_ok=True)


def test_normalization_methods_align_sample_totals_medians_and_rank_profiles() -> None:
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    table = build_label_free_intensity_table(
        report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    tic = normalize_label_free_table(table, method=NormalizationMethod.TIC)
    median = normalize_label_free_table(table, method=NormalizationMethod.MEDIAN)
    quantile = normalize_label_free_table(table, method=NormalizationMethod.QUANTILE)
    log2_centered = normalize_label_free_table(
        table,
        method=NormalizationMethod.LOG2_MEDIAN_CENTERING,
    )
    vsn_like = normalize_label_free_table(table, method=NormalizationMethod.VSN_LIKE)

    def sample_values(active_table: LabelFreeQuantTable, sample_id: str) -> np.ndarray:
        values = [
            value.abundance
            for value in active_table.values
            if value.sample_id == sample_id and value.abundance is not None
        ]
        return np.array(values, dtype=float)

    tic_totals = [
        float(np.sum(sample_values(tic, sample_id))) for sample_id in tic.sample_ids
    ]
    assert max(tic_totals) - min(tic_totals) < 1e-6

    median_values = [
        float(np.median(sample_values(median, sample_id)))
        for sample_id in median.sample_ids
    ]
    assert max(median_values) - min(median_values) < 1e-6

    quantile_sorted = [
        tuple(np.round(np.sort(sample_values(quantile, sample_id)), 6))
        for sample_id in quantile.sample_ids
    ]
    assert len(set(quantile_sorted)) == 1

    vsn_log_medians = [
        float(np.median(np.log2(sample_values(vsn_like, sample_id) + 1.0)))
        for sample_id in vsn_like.sample_ids
    ]
    assert max(vsn_log_medians) - min(vsn_log_medians) < 1e-6

    log2_centered_medians = [
        float(
            np.median(
                np.log2(
                    sample_values(log2_centered, sample_id)[
                        sample_values(log2_centered, sample_id) > 0.0
                    ]
                )
            )
        )
        for sample_id in log2_centered.sample_ids
    ]
    assert max(log2_centered_medians) - min(log2_centered_medians) < 1e-6

    comparison = build_normalization_comparison_report(table, median)
    before_totals = [entry.total_abundance for entry in comparison.before]
    after_medians = [entry.median_abundance for entry in comparison.after]
    assert comparison.method.value == "median"
    assert max(before_totals) - min(before_totals) > 0.0
    assert max(after_medians) - min(after_medians) < 1e-6
    assert comparison.before_distributions
    assert comparison.after_distributions
    assert comparison.log_transform_preparation == ()


def test_log_transform_normalization_reports_nonpositive_handling_explicitly() -> None:
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    table = build_label_free_intensity_table(
        report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    log2_centered = normalize_label_free_table(
        table,
        method=NormalizationMethod.LOG2_MEDIAN_CENTERING,
    )
    vsn_like = normalize_label_free_table(table, method=NormalizationMethod.VSN_LIKE)

    log2_comparison = build_normalization_comparison_report(table, log2_centered)
    vsn_comparison = build_normalization_comparison_report(table, vsn_like)

    assert log2_comparison.method is NormalizationMethod.LOG2_MEDIAN_CENTERING
    assert vsn_comparison.method is NormalizationMethod.VSN_LIKE
    zero_before = {
        entry.sample_id: entry.zero_count
        for entry in log2_comparison.before_distributions
    }
    assert zero_before["C1"] == 1
    assert zero_before["C2"] == 1
    assert zero_before["T1"] == 1
    assert zero_before["T2"] == 1
    assert all(
        entry.negative_count == 0 for entry in log2_comparison.before_distributions
    )
    assert all(
        entry.negative_count == 0 for entry in vsn_comparison.before_distributions
    )
    assert {
        entry.handling_strategy for entry in log2_comparison.log_transform_preparation
    } == {"exclude_nonpositive_values_before_log2_centering"}
    assert {
        entry.handling_strategy for entry in vsn_comparison.log_transform_preparation
    } == {"floor_nonpositive_values_then_add_pseudocount"}
    assert all(
        entry.pseudocount is None for entry in log2_comparison.log_transform_preparation
    )
    assert all(
        entry.pseudocount is not None and entry.pseudocount > 0.0
        for entry in vsn_comparison.log_transform_preparation
    )
    log2_zero_after = {
        entry.sample_id: entry.zero_count
        for entry in log2_comparison.after_distributions
    }
    assert log2_zero_after["C1"] == 1
    assert log2_zero_after["C2"] == 1
    assert log2_zero_after["T1"] == 1
    assert log2_zero_after["T2"] == 1


def test_batch_effect_and_replicate_correlation_reports_are_stable() -> None:
    feature_report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    design_report = parse_experimental_design_table(_quant_fixture("quant.design.tsv"))
    table = normalize_label_free_table(
        build_label_free_intensity_table(
            feature_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        method=NormalizationMethod.MEDIAN,
    )

    batch_report = build_batch_effect_advisory(table, design_report.accepted_entries)
    replicate_report = build_replicate_correlation_report(
        table, design_report.accepted_entries
    )

    assert batch_report.disposition.value == "ADVISORY"
    assert len(batch_report.batches) == 2
    assert {entry.batch_id for entry in batch_report.batches} == {"batch-a", "batch-b"}
    assert batch_report.batch_variance_proxy >= 0.0
    assert batch_report.batch_associated_component_count >= 0
    assert batch_report.batch_correction_blocked is False
    assert replicate_report.within_condition_mean is not None
    assert len(replicate_report.entries) >= 2
    assert all(entry.shared_entity_count >= 2 for entry in replicate_report.entries)


def test_differential_abundance_and_bh_correction_surface_signal() -> None:
    feature_report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    design_report = parse_experimental_design_table(_quant_fixture("quant.design.tsv"))
    table = normalize_label_free_table(
        build_label_free_intensity_table(
            feature_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.TOP_N,
            top_n=2,
        ),
        method=NormalizationMethod.MEDIAN,
    )

    differential = build_differential_abundance_report(
        table,
        design_report.accepted_entries,
        condition_a="control",
        condition_b="treatment",
    )
    first = differential.entries[0]
    p001 = next(entry for entry in differential.entries if entry.entity_id == "P001")
    p002 = next(entry for entry in differential.entries if entry.entity_id == "P002")

    assert first.adjusted_p_value is not None
    assert all(entry.adjusted_p_value is not None for entry in differential.entries)
    assert differential.assumption_report.test_type == "welch_t_test"
    assert (
        differential.assumption_report.multiple_testing_scope
        == "benjamini_hochberg_report_wide_entities"
    )
    assert p001.log2_fold_change > 0
    assert p002.log2_fold_change < 0
    assert p001.standard_error is not None
    assert p001.confidence_interval_low is not None
    assert p001.confidence_interval_high is not None
    assert p001.effect_size_cohens_d is not None


def test_differential_abundance_respects_minimum_replicate_policy() -> None:
    feature_report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    design_report = parse_experimental_design_table(_quant_fixture("quant.design.tsv"))
    table = normalize_label_free_table(
        build_label_free_intensity_table(
            feature_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.TOP_N,
            top_n=2,
        ),
        method=NormalizationMethod.MEDIAN,
    )
    one_vs_two_design = tuple(
        entry
        for entry in design_report.accepted_entries
        if entry.sample_id in {"C1", "T1", "T2"}
    )

    try:
        build_differential_abundance_report(
            table,
            one_vs_two_design,
            condition_a="control",
            condition_b="treatment",
            replicate_policy=DifferentialReplicatePolicy(
                min_replicates_per_condition=2,
                disposition=QuantAssessmentDisposition.ENFORCED,
            ),
        )
    except ValueError as exc:
        assert "minimum replicate policy" in str(exc)
    else:
        raise AssertionError("expected enforced replicate policy failure")


def test_label_based_quant_bundle_preserves_channel_roles_and_missing_channel_policy() -> (
    None
):
    feature_report = parse_ms1_feature_table(
        _quant_fixture("multiplex_ms1_features.tsv")
    )
    design_report = parse_experimental_design_table(
        _quant_fixture("multiplex.design.tsv")
    )
    table = build_label_free_intensity_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    bundle = build_label_based_quant_bundle(
        table,
        design_entries=design_report.accepted_entries,
        policy=LabelBasedQuantPolicy(
            missing_channel_policy=MissingChannelPolicy.PRESERVE,
            channel_entries=(
                LabelBasedChannelPolicyEntry(
                    multiplex_group="plex-a",
                    multiplex_channel="126",
                    channel_role=LabelBasedChannelRole.SAMPLE,
                ),
                LabelBasedChannelPolicyEntry(
                    multiplex_group="plex-a",
                    multiplex_channel="127N",
                    channel_role=LabelBasedChannelRole.SAMPLE,
                ),
                LabelBasedChannelPolicyEntry(
                    multiplex_group="plex-a",
                    multiplex_channel="128N",
                    channel_role=LabelBasedChannelRole.CARRIER,
                ),
                LabelBasedChannelPolicyEntry(
                    multiplex_group="plex-a",
                    multiplex_channel="129N",
                    channel_role=LabelBasedChannelRole.REFERENCE,
                ),
                LabelBasedChannelPolicyEntry(
                    multiplex_group="plex-b",
                    multiplex_channel="126",
                    channel_role=LabelBasedChannelRole.SAMPLE,
                ),
                LabelBasedChannelPolicyEntry(
                    multiplex_group="plex-b",
                    multiplex_channel="127N",
                    channel_role=LabelBasedChannelRole.SAMPLE,
                ),
                LabelBasedChannelPolicyEntry(
                    multiplex_group="plex-b",
                    multiplex_channel="128N",
                    channel_role=LabelBasedChannelRole.CARRIER,
                ),
            ),
        ),
    )

    assert isinstance(bundle, LabelBasedQuantBundle)
    assert bundle.document_schema.document_kind == "label_based_quant_bundle"
    carrier = next(
        entry
        for entry in bundle.channels
        if entry.multiplex_group == "plex-a" and entry.multiplex_channel == "128N"
    )
    missing = next(
        entry
        for entry in bundle.missing_channels
        if entry.multiplex_group == "plex-a" and entry.multiplex_channel == "129N"
    )

    assert carrier.channel_role is LabelBasedChannelRole.CARRIER
    assert carrier.present_in_table is True
    assert missing.policy is MissingChannelPolicy.PRESERVE
    assert missing.expected_role is LabelBasedChannelRole.REFERENCE


def test_multiplex_normalization_and_channel_balance_follow_group_policy() -> None:
    feature_report = parse_ms1_feature_table(
        _quant_fixture("multiplex_ms1_features.tsv")
    )
    design_report = parse_experimental_design_table(
        _quant_fixture("multiplex.design.tsv")
    )
    table = build_label_free_intensity_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    normalized = normalize_multiplex_quant_table(
        table,
        design_entries=design_report.accepted_entries,
        policy=MultiplexNormalizationPolicy(method=NormalizationMethod.MEDIAN),
    )
    balance = build_multiplex_channel_balance_report(
        table,
        design_entries=design_report.accepted_entries,
        policy=MultiplexNormalizationPolicy(
            method=NormalizationMethod.MEDIAN,
            balance_ratio_threshold=1.5,
        ),
    )

    assert normalized.normalization_method is NormalizationMethod.MEDIAN
    assert isinstance(balance, MultiplexChannelBalanceReport)
    plex_a_values = [
        value.abundance
        for value in normalized.values
        if value.sample_id in {"plex_a_126", "plex_a_127N", "plex_a_128N"}
        and value.abundance is not None
    ]
    assert min(plex_a_values) > 0.0
    carrier = next(
        entry for entry in balance.entries if entry.sample_id == "plex_a_128N"
    )
    control = next(
        entry for entry in balance.entries if entry.sample_id == "plex_a_126"
    )
    assert carrier.flagged is True
    assert carrier.channel_role is LabelBasedChannelRole.REFERENCE
    assert control.flagged is False


def test_protein_quant_policy_comparison_makes_shared_peptide_assumptions_explicit() -> (
    None
):
    feature_report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))

    comparison = build_protein_quant_policy_comparison_report(
        feature_report.accepted_records
    )

    assert isinstance(comparison, ProteinQuantPolicyComparisonReport)
    p001_c1 = next(
        entry
        for entry in comparison.entries
        if entry.protein_ref == "P001" and entry.sample_id == "C1"
    )
    values = {
        value.assignment_policy: value.abundance for value in p001_c1.policy_values
    }

    assert values[ProteinQuantAssignmentPolicy.INFERENCE_INCLUSIVE] == 2200.0
    assert values[ProteinQuantAssignmentPolicy.QUANT_UNIQUE_ONLY] == 1900.0
    assert values[ProteinQuantAssignmentPolicy.QUANT_SPLIT_SHARED] == 2050.0
    assert p001_c1.max_abundance_difference == 300.0


def test_study_scale_quant_reports_summarize_large_designs_compactly() -> None:
    feature_report = parse_ms1_feature_table(
        _quant_fixture("study_scale_ms1_features.tsv")
    )
    design_report = parse_experimental_design_table(
        _quant_fixture("study_scale.design.tsv")
    )
    table = build_label_free_intensity_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    replicate_summary = build_study_scale_replicate_correlation_report(
        table,
        design_report.accepted_entries,
        top_pair_count=2,
    )
    batch_summary = build_study_scale_batch_effect_report(
        table,
        design_report.accepted_entries,
        shift_threshold=0.1,
    )

    assert isinstance(replicate_summary, StudyScaleReplicateCorrelationReport)
    assert len(replicate_summary.sample_summaries) == 8
    c1 = next(
        entry for entry in replicate_summary.sample_summaries if entry.sample_id == "C1"
    )
    assert c1.within_condition_pairs == 3
    assert len(replicate_summary.weakest_within_condition_pairs) == 2
    assert isinstance(batch_summary, StudyScaleBatchEffectReport)
    assert batch_summary.flagged_batch_count == 2
    assert batch_summary.batch_variance_proxy >= 0.0
    assert batch_summary.batch_correction_blocked is False


def test_batch_effect_estimator_honors_custom_batch_field_metadata() -> None:
    feature_report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    design_report = parse_experimental_design_table(_quant_fixture("quant.design.tsv"))
    design_entries = tuple(
        entry.model_copy(
            update={
                "batch": None,
                "metadata": {
                    **entry.metadata,
                    "instrument_run": "run-a"
                    if entry.sample_id in {"C1", "T1"}
                    else "run-b",
                },
            }
        )
        for entry in design_report.accepted_entries
    )
    table = normalize_label_free_table(
        build_label_free_intensity_table(
            feature_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        method=NormalizationMethod.MEDIAN,
    )

    report = build_batch_effect_estimator_report(
        table,
        design_entries,
        batch_field="instrument_run",
    )

    assert report.batch_field == "instrument_run"
    assert {entry.batch_id for entry in report.batches} == {"run-a", "run-b"}
    assert report.batch_correction_blocked is False


def test_quant_reproducibility_manifest_matches_stable_fixture() -> None:
    feature_report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    table = normalize_label_free_table(
        build_label_free_intensity_table(
            feature_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.TOP_N,
            top_n=2,
        ),
        method=NormalizationMethod.MEDIAN,
    )

    manifest = build_quant_reproducibility_manifest(table)
    assert isinstance(manifest, QuantReproducibilityManifest)

    output_path = _quant_fixture("quant_reproducibility_manifest.actual.json")
    fixture_path = _quant_fixture("quant_reproducibility_manifest.json")
    try:
        export_quant_reproducibility_manifest(manifest, output_path)
        assert output_path.read_text(encoding="utf-8") == fixture_path.read_text(
            encoding="utf-8"
        )
    finally:
        output_path.unlink(missing_ok=True)


def test_normalization_strategy_comparison_reports_rank_methods_explicitly() -> None:
    feature_report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    table = build_label_free_intensity_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    comparison = build_normalization_strategy_comparison_report(table)

    assert isinstance(comparison, NormalizationStrategyComparisonReport)
    assert len(comparison.entries) == 6
    assert any(
        entry.method is NormalizationMethod.LOG2_MEDIAN_CENTERING
        for entry in comparison.entries
    )
    assert any(
        entry.method is NormalizationMethod.VSN_LIKE for entry in comparison.entries
    )
    assert comparison.entries[0].balance_score <= comparison.entries[-1].balance_score
    assert comparison.recommended_method is comparison.entries[0].method


def test_missing_data_mechanism_report_distinguishes_biology_from_failure() -> None:
    feature_report = parse_ms1_feature_table(
        _quant_fixture("missing_mechanism_ms1_features.tsv")
    )
    design_report = parse_experimental_design_table(_quant_fixture("quant.design.tsv"))
    table = build_label_free_intensity_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    report = build_missing_data_mechanism_report(
        table,
        design_report.accepted_entries,
    )

    assert isinstance(report, MissingDataMechanismReport)
    pbio = next(entry for entry in report.entries if entry.entity_id == "PBIO")
    ptech = next(entry for entry in report.entries if entry.entity_id == "PTECH")
    pmix = next(entry for entry in report.entries if entry.entity_id == "PMIX")

    assert pbio.mechanism is MissingDataMechanism.CONDITION_SPECIFIC_ABSENCE
    assert pbio.missing_conditions == ("treatment",)
    assert ptech.mechanism is MissingDataMechanism.LIKELY_TECHNICAL_FAILURE
    assert pmix.mechanism is MissingDataMechanism.MISSING_COMPLETELY_AT_RANDOM


def test_missingness_classifier_report_bundles_owned_tables_and_mechanisms() -> None:
    feature_report = parse_ms1_feature_table(
        _quant_fixture("missing_mechanism_ms1_features.tsv")
    )
    design_report = parse_experimental_design_table(_quant_fixture("quant.design.tsv"))
    table = build_label_free_intensity_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    report = build_missingness_classifier_report(
        table,
        design_entries=design_report.accepted_entries,
    )

    assert report.sample_summary.entries
    assert report.entity_summary.entries
    assert report.condition_summary.entries
    assert report.intensity_dependence.plot_points
    assert (
        report.mechanism_report.summary_counts[
            MissingDataMechanism.CONDITION_SPECIFIC_ABSENCE
        ]
        == 1
    )


def test_quant_artifact_bundle_preserves_reviewable_quant_outputs() -> None:
    feature_report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    design_report = parse_experimental_design_table(_quant_fixture("quant.design.tsv"))
    table = normalize_label_free_table(
        build_label_free_intensity_table(
            feature_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.TOP_N,
            top_n=2,
        ),
        method=NormalizationMethod.MEDIAN,
    )
    differential = apply_benjamini_hochberg(
        build_differential_abundance_report(
            table,
            design_report.accepted_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )
    strategy = build_normalization_strategy_comparison_report(
        build_label_free_intensity_table(
            feature_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.TOP_N,
            top_n=2,
        )
    )
    missingness_entity_summary = build_missingness_entity_summary_report(table)
    missingness_condition_summary = build_missingness_condition_summary_report(
        table,
        design_entries=design_report.accepted_entries,
    )
    missingness_intensity_dependence = build_missingness_intensity_dependence_report(
        table
    )
    missingness_mechanism_report = build_missing_data_mechanism_report(
        table,
        design_entries=design_report.accepted_entries,
    )
    comparison = build_normalization_comparison_report(
        build_label_free_intensity_table(
            feature_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.TOP_N,
            top_n=2,
        ),
        table,
    )
    imputed_table = impute_label_free_table(
        table,
        method=ImputationMethod.LOW_INTENSITY,
    )
    imputation_report = build_imputation_report(table, imputed_table)
    imputation_sensitivity = build_imputation_sensitivity_report(
        table,
        design_report.accepted_entries,
        condition_a="control",
        condition_b="treatment",
    )
    differential = apply_benjamini_hochberg(
        build_differential_abundance_report(
            imputed_table,
            design_report.accepted_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )
    replicate_qc = build_replicate_and_batch_qc_report(
        imputed_table,
        design_entries=design_report.accepted_entries,
    )
    design_matrix = build_quant_design_matrix_report(
        design_report.accepted_entries,
        batch_field="batch",
    )
    design_model_fit = fit_quant_design_matrix_model(
        imputed_table,
        design_matrix,
    )
    limma_package = build_limma_compatible_quant_package(
        imputed_table,
        design_report.accepted_entries,
        batch_field="batch",
    )
    msstats_input_report = build_msstats_compatible_input_report(
        feature_report.accepted_records,
        design_report.accepted_entries,
    )

    bundle = build_quant_artifact_bundle(
        imputed_table,
        design_entries=design_report.accepted_entries,
        imputation_report=imputation_report,
        imputation_sensitivity_report=imputation_sensitivity,
        missingness_entity_summary=missingness_entity_summary,
        missingness_condition_summary=missingness_condition_summary,
        missingness_intensity_dependence=missingness_intensity_dependence,
        missingness_mechanism_report=missingness_mechanism_report,
        replicate_qc_report=replicate_qc,
        normalization_comparison_report=comparison,
        limma_compatible_package=limma_package,
        msstats_compatible_input_report=msstats_input_report,
        design_matrix_report=design_matrix,
        design_model_fit_report=design_model_fit,
        differential_abundance_report=differential,
        normalization_strategy_report=strategy,
    )

    assert isinstance(bundle, QuantArtifactBundle)
    assert bundle.document_schema.document_kind == "quant_artifact_bundle"
    assert bundle.matrix_export.rows
    assert bundle.reproducibility_manifest.reproducibility_hash
    assert bundle.imputation_report is not None
    assert bundle.imputation_report.imputed_value_count > 0
    assert bundle.imputation_sensitivity_report is not None
    assert bundle.imputation_sensitivity_report.overlap_entries
    assert bundle.imputation_sensitivity_report.changed_significance_entries
    assert bundle.imputation_sensitivity_report.imputation_dependent_hits
    assert bundle.normalization_comparison_report is not None
    assert bundle.missingness_entity_summary is not None
    assert bundle.missingness_condition_summary is not None
    assert bundle.missingness_intensity_dependence is not None
    assert bundle.missingness_mechanism_report is not None
    assert bundle.replicate_qc_report is not None
    assert bundle.replicate_qc_report.replicate_correlation_report.entries
    assert bundle.replicate_qc_report.replicate_cv_report.entries
    assert bundle.replicate_qc_report.sample_pca_report is not None
    assert bundle.replicate_qc_report.condition_clustering_report is not None
    assert bundle.limma_compatible_package is not None
    assert bundle.limma_compatible_package.sample_annotations
    assert bundle.msstats_compatible_input_report is not None
    assert bundle.msstats_compatible_input_report.rows
    assert bundle.design_matrix_report is not None
    assert bundle.design_matrix_report.contrasts
    assert bundle.design_model_fit_report is not None
    assert bundle.design_model_fit_report.coefficient_entries

    output_path = _quant_fixture("quant_artifact_bundle.json")
    try:
        export_quant_artifact_bundle(bundle, output_path)
        assert "quant_artifact_bundle" in output_path.read_text(encoding="utf-8")
    finally:
        output_path.unlink(missing_ok=True)


def test_quant_artifact_bundle_accepts_multi_condition_differential_report() -> None:
    records = (
        Ms1FeatureRecord(
            feature_id="mda-001",
            sample_id="c1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mda-002",
            sample_id="c2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mda-003",
            sample_id="t1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=400.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mda-004",
            sample_id="t2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=420.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mda-005",
            sample_id="r1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=250.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mda-006",
            sample_id="r2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=260.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="c1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="c2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="t1",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="t2",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="t2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="r1",
            condition="rescue",
            replicate=1,
            fraction=1,
            spectra_file="r1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="r2",
            condition="rescue",
            replicate=2,
            fraction=1,
            spectra_file="r2.mzml",
        ),
    )
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    multi_condition = build_multi_condition_differential_abundance_report(
        table,
        design,
    )

    bundle = build_quant_artifact_bundle(
        table,
        design_entries=design,
        differential_abundance_multi_condition_report=multi_condition,
    )

    assert bundle.differential_abundance_report is None
    assert bundle.differential_abundance_multi_condition_report is not None
    assert len(bundle.differential_abundance_multi_condition_report.reports) == 3


def test_quant_artifact_bundle_accepts_time_course_differential_report() -> None:
    records = (
        Ms1FeatureRecord(
            feature_id="tca-001",
            sample_id="c0",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="tca-002",
            sample_id="c1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=130.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="tca-003",
            sample_id="t0",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="tca-004",
            sample_id="t1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=400.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="c0",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c0.mzml",
            metadata={"timepoint": "0"},
        ),
        ExperimentalDesignEntry(
            sample_id="c1",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c1.mzml",
            metadata={"timepoint": "1"},
        ),
        ExperimentalDesignEntry(
            sample_id="t0",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t0.mzml",
            metadata={"timepoint": "0"},
        ),
        ExperimentalDesignEntry(
            sample_id="t1",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="t1.mzml",
            metadata={"timepoint": "1"},
        ),
    )
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    time_course = build_time_course_differential_report(
        table,
        design,
    )

    bundle = build_quant_artifact_bundle(
        table,
        design_entries=design,
        time_course_differential_report=time_course,
    )

    assert bundle.time_course_differential_report is not None
    assert bundle.time_course_differential_report.ordered_timepoints == ("0", "1")


def test_quant_edge_case_fixture_covers_sparse_missing_channels_and_asymmetric_replication() -> (
    None
):
    feature_report = parse_ms1_feature_table(
        _quant_fixture("edge_case_ms1_features.tsv")
    )
    design_report = parse_experimental_design_table(
        _quant_fixture("edge_case.design.tsv")
    )
    peptide_table = build_label_free_intensity_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PEPTIDE,
    )
    summary = summarize_missing_values(peptide_table)
    lookup = {
        (value.entity_id, value.sample_id): value for value in peptide_table.values
    }
    summary_lookup = {entry.sample_id: entry for entry in summary.entries}

    assert feature_report.total_rows == 20
    assert len(feature_report.accepted_records) == 20
    assert (
        len(
            [
                entry
                for entry in design_report.accepted_entries
                if entry.condition == "control"
            ]
        )
        == 3
    )
    assert (
        len(
            [
                entry
                for entry in design_report.accepted_entries
                if entry.condition == "treatment"
            ]
        )
        == 2
    )
    assert lookup[("SPARSEPEP", "T1")].abundance == 400.0
    assert (
        lookup[("SPARSEPEP", "C1")].missing_value_kind.value == "missing_not_observed"
    )
    assert lookup[("FILTERPEP", "C1")].missing_value_kind.value == "filtered"
    assert lookup[("ZEROPEP", "C1")].missing_value_kind.value == "zero"
    assert summary_lookup["C1"].filtered_count == 1
    assert summary_lookup["T2"].not_observed_count >= 2

    differential = build_differential_abundance_report(
        build_label_free_intensity_table(
            feature_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
        ),
        design_report.accepted_entries,
        condition_a="control",
        condition_b="treatment",
    )
    core = next(entry for entry in differential.entries if entry.entity_id == "P100")
    assert core.observations_a == 3
    assert core.observations_b == 2
    assert core.not_observed_values_b == 0


def test_missing_value_summary_policy_applies_deterministic_correction_and_filtering() -> (
    None
):
    feature_report = parse_ms1_feature_table(
        _quant_fixture("edge_case_ms1_features.tsv")
    )
    peptide_table = build_label_free_intensity_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PEPTIDE,
    )

    summary = summarize_missing_values(
        peptide_table,
        policy=MissingValueSummaryPolicy(
            zero_policy=MissingValueCorrectionPolicy.TREAT_AS_NOT_OBSERVED,
            filtered_policy=MissingValueCorrectionPolicy.TREAT_AS_NOT_OBSERVED,
            min_observed_samples_per_entity=2,
        ),
    )
    summary_lookup = {entry.sample_id: entry for entry in summary.entries}

    assert summary.policy.zero_policy.value == "treat_as_not_observed"
    assert summary.policy.filtered_policy.value == "treat_as_not_observed"
    assert summary.included_entity_ids == ("COREPEP", "FILTERPEP")
    assert summary.excluded_entity_ids == ("SPARSEPEP", "ZEROPEP")
    assert summary_lookup["C1"].observed_count == 1
    assert summary_lookup["C1"].zero_count == 0
    assert summary_lookup["C1"].filtered_count == 0
    assert summary_lookup["C1"].not_observed_count == 1
    assert summary_lookup["T2"].observed_count == 2
    assert summary_lookup["T2"].not_observed_count == 0
