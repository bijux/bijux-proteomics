# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    DifferentialImputationSignificanceChangeReason,
    DifferentialResultRobustnessReasonCode,
    ImputationMethod,
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    annotate_differential_abundance_report_imputation_dependence,
    build_differential_abundance_report,
    build_differential_imputation_dependence_report,
    build_label_free_intensity_table,
    build_no_impute_reference_table,
    impute_label_free_table,
)


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.mzml",
        ),
    )


def _table():
    return build_label_free_intensity_table(
        (
            Ms1FeatureRecord(
                feature_id="imp-dep-001",
                sample_id="case-1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=100.0,
                protein_refs=("P1",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="imp-dep-002",
                sample_id="case-2",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=120.0,
                protein_refs=("P1",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="imp-dep-003",
                sample_id="ctrl-1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=None,
                protein_refs=("P1",),
                missing_value_kind=MissingValueKind.NOT_OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="imp-dep-004",
                sample_id="ctrl-2",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=None,
                protein_refs=("P1",),
                missing_value_kind=MissingValueKind.NOT_OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="imp-dep-005",
                sample_id="case-1",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=101.0,
                protein_refs=("P2",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="imp-dep-006",
                sample_id="case-2",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=119.0,
                protein_refs=("P2",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="imp-dep-007",
                sample_id="ctrl-1",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=30.0,
                protein_refs=("P2",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="imp-dep-008",
                sample_id="ctrl-2",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=31.0,
                protein_refs=("P2",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
        ),
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )


def test_differential_imputation_dependence_report_labels_hits_that_need_imputation() -> (
    None
):
    table = _table()
    imputed_table = impute_label_free_table(
        table,
        method=ImputationMethod.LOW_INTENSITY,
    )
    no_impute_report = build_differential_abundance_report(
        table,
        _design(),
        condition_a="case",
        condition_b="ctrl",
    )
    imputed_report = build_differential_abundance_report(
        imputed_table,
        _design(),
        condition_a="case",
        condition_b="ctrl",
    )

    dependence = build_differential_imputation_dependence_report(
        no_impute_report,
        imputed_report,
    )
    by_entity = {entry.entity_id: entry for entry in dependence.entries}
    restored = build_no_impute_reference_table(imputed_table)

    assert restored.imputation_method is ImputationMethod.NONE
    assert by_entity["PEPA"].significance_change_reason is (
        DifferentialImputationSignificanceChangeReason.SIGNIFICANT_ONLY_AFTER_IMPUTATION
    )
    assert by_entity["PEPA"].imputation_dependent_hit is True
    assert by_entity["PEPA"].no_impute_adjusted_p_value == next(
        entry.adjusted_p_value
        for entry in no_impute_report.entries
        if entry.entity_id == "PEPA"
    )
    assert by_entity["PEPA"].imputed_adjusted_p_value == next(
        entry.adjusted_p_value
        for entry in imputed_report.entries
        if entry.entity_id == "PEPA"
    )
    assert dependence.imputation_dependent_hit_count >= 1
    assert dependence.imputation_dependent_hit_count == sum(
        entry.imputation_dependent_hit for entry in dependence.entries
    )


def test_differential_abundance_report_preserves_imputation_dependence_fields() -> None:
    table = _table()
    imputed_table = impute_label_free_table(
        table,
        method=ImputationMethod.LOW_INTENSITY,
    )
    baseline_table = build_no_impute_reference_table(imputed_table)
    baseline_report = build_differential_abundance_report(
        baseline_table,
        _design(),
        condition_a="case",
        condition_b="ctrl",
    )
    report = build_differential_abundance_report(
        imputed_table,
        _design(),
        condition_a="case",
        condition_b="ctrl",
    )
    annotated = annotate_differential_abundance_report_imputation_dependence(
        report,
        no_impute_report=baseline_report,
    )
    by_entity = {entry.entity_id: entry for entry in annotated.entries}

    assert by_entity["PEPA"].imputation_significance_change_reason is (
        DifferentialImputationSignificanceChangeReason.SIGNIFICANT_ONLY_AFTER_IMPUTATION
    )
    assert by_entity["PEPA"].imputation_dependent_hit is True
    assert by_entity["PEPA"].no_impute_adjusted_p_value is not None
    assert by_entity["PEPA"].imputed_adjusted_p_value == by_entity["PEPA"].adjusted_p_value
    assert (
        DifferentialResultRobustnessReasonCode.IMPUTATION_DEPENDENT_SIGNIFICANCE
        in by_entity["PEPA"].robustness_reason_codes
    )
