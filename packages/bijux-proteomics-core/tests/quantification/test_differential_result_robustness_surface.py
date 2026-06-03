# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    DifferentialResultRobustnessQcStatus,
    DifferentialResultRobustnessReasonCode,
    ImputationMethod,
    LabelFreeQuantTable,
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    bootstrap_effect_stability,
    build_differential_abundance_report,
    build_differential_abundance_robustness_report,
    build_label_free_intensity_table,
    impute_label_free_table,
)


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.mzml",
        ),
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
    )


def _table() -> LabelFreeQuantTable:
    records = (
        Ms1FeatureRecord(
            feature_id="rob-001",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("PSTRONG",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-002",
            sample_id="ctrl-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=120.0,
            protein_refs=("PSTRONG",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-003",
            sample_id="ctrl-1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=140.0,
            protein_refs=("PSTRONG",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-004",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=105.0,
            protein_refs=("PSTRONG",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-005",
            sample_id="ctrl-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=118.0,
            protein_refs=("PSTRONG",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-006",
            sample_id="ctrl-2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=145.0,
            protein_refs=("PSTRONG",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-007",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=280.0,
            protein_refs=("PSTRONG",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-008",
            sample_id="case-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=310.0,
            protein_refs=("PSTRONG",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-009",
            sample_id="case-1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=340.0,
            protein_refs=("PSTRONG",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-010",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=300.0,
            protein_refs=("PSTRONG",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-011",
            sample_id="case-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=320.0,
            protein_refs=("PSTRONG",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-012",
            sample_id="case-2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=360.0,
            protein_refs=("PSTRONG",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-101",
            sample_id="ctrl-1",
            peptide="PEPX",
            canonical_peptide="PEPX",
            intensity=80.0,
            protein_refs=("PWEAK",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-102",
            sample_id="ctrl-2",
            peptide="PEPX",
            canonical_peptide="PEPX",
            intensity=None,
            protein_refs=("PWEAK",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-103",
            sample_id="case-1",
            peptide="PEPX",
            canonical_peptide="PEPX",
            intensity=90.0,
            protein_refs=("PWEAK",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rob-104",
            sample_id="case-2",
            peptide="PEPX",
            canonical_peptide="PEPX",
            intensity=None,
            protein_refs=("PWEAK",),
            missing_value_kind=MissingValueKind.FILTERED,
        ),
    )
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    return impute_label_free_table(table, method=ImputationMethod.LOW_INTENSITY)


def test_differential_result_robustness_penalizes_missing_imputed_single_peptide_hits() -> (
    None
):
    table = _table()
    report = build_differential_abundance_report(
        table,
        _design(),
        condition_a="case",
        condition_b="control",
    )
    robustness = build_differential_abundance_robustness_report(
        report,
        table,
        _design(),
    )
    by_entity = {entry.entity_id: entry for entry in robustness.entries}
    by_result = {entry.entity_id: entry for entry in report.entries}

    assert by_entity["PSTRONG"].robustness_score > by_entity["PWEAK"].robustness_score
    assert (
        by_entity["PSTRONG"].qc_status is DifferentialResultRobustnessQcStatus.CAUTION
    )
    assert by_entity["PWEAK"].qc_status is DifferentialResultRobustnessQcStatus.CAUTION
    assert (
        DifferentialResultRobustnessReasonCode.HIGH_MISSINGNESS
        in by_entity["PWEAK"].reason_codes
    )
    assert (
        DifferentialResultRobustnessReasonCode.IMPUTATION_HEAVY
        in by_entity["PWEAK"].reason_codes
    )
    assert (
        DifferentialResultRobustnessReasonCode.LOW_PEPTIDE_SUPPORT
        in by_entity["PWEAK"].reason_codes
    )
    assert (
        DifferentialResultRobustnessReasonCode.CAUTION_QC
        in by_entity["PWEAK"].reason_codes
    )
    assert by_result["PWEAK"].robustness_score == by_entity["PWEAK"].robustness_score
    assert by_result["PWEAK"].robustness_reason_codes == by_entity["PWEAK"].reason_codes


def test_bootstrap_effect_stability_stays_stronger_for_supported_entities() -> None:
    report = bootstrap_effect_stability(
        _table(),
        _design(),
        condition_a="case",
        condition_b="control",
        n_resamples=80,
        random_seed=11,
    )
    by_entity = {entry.entity_id: entry for entry in report.entries}

    assert by_entity["PSTRONG"].sign_consistency >= by_entity["PWEAK"].sign_consistency
    assert abs(by_entity["PSTRONG"].median_log2fc) > abs(
        by_entity["PWEAK"].median_log2fc
    )
