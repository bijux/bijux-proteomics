# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    ImputationMethod,
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_imputation_report,
    build_imputation_sensitivity_report,
    build_label_free_intensity_table,
    impute_label_free_table,
)


def _table():
    records = (
        Ms1FeatureRecord(
            feature_id="imp-001",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-002",
            sample_id="s2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=None,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
    )
    return build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )


def test_none_imputation_preserves_table_and_emits_empty_report() -> None:
    table = _table()
    imputed = impute_label_free_table(table, method=ImputationMethod.NONE)
    report = build_imputation_report(table, imputed)

    assert imputed.imputation_method is ImputationMethod.NONE
    assert report.method is ImputationMethod.NONE
    assert report.imputed_value_count == 0
    assert report.entries == ()


def test_low_intensity_imputation_fills_missing_abundances_and_preserves_ledger() -> (
    None
):
    records = (
        Ms1FeatureRecord(
            feature_id="imp-li-001",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-li-002",
            sample_id="s2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=400.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-li-003",
            sample_id="s1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=60.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-li-004",
            sample_id="s2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=None,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-li-005",
            sample_id="s1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=0.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.ZERO,
        ),
        Ms1FeatureRecord(
            feature_id="imp-li-006",
            sample_id="s2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=None,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.FILTERED,
        ),
    )
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )

    imputed = impute_label_free_table(table, method=ImputationMethod.LOW_INTENSITY)
    report = build_imputation_report(table, imputed)
    lookup = {(value.entity_id, value.sample_id): value for value in imputed.values}
    by_cell = {(entry.entity_id, entry.sample_id): entry for entry in report.entries}

    assert imputed.imputation_method is ImputationMethod.LOW_INTENSITY
    assert lookup[("PEPB", "s2")].abundance == 200.0
    assert lookup[("PEPC", "s2")].abundance == 200.0
    assert lookup[("PEPC", "s1")].abundance == 0.0
    assert report.method is ImputationMethod.LOW_INTENSITY
    assert report.imputed_value_count == 2
    assert by_cell[("PEPB", "s2")].original_missing_value_kind is (
        MissingValueKind.NOT_OBSERVED
    )
    assert by_cell[("PEPC", "s2")].original_missing_value_kind is (
        MissingValueKind.FILTERED
    )


def test_knn_imputation_uses_nearest_entity_profiles_and_reports_neighbors() -> None:
    records = (
        Ms1FeatureRecord(
            feature_id="imp-knn-001",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=10.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-knn-002",
            sample_id="s2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=20.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-knn-003",
            sample_id="s3",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=None,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-knn-004",
            sample_id="s1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=11.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-knn-005",
            sample_id="s2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=19.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-knn-006",
            sample_id="s3",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=30.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )

    imputed = impute_label_free_table(table, method=ImputationMethod.KNN)
    report = build_imputation_report(table, imputed)
    lookup = {(value.entity_id, value.sample_id): value for value in imputed.values}

    assert imputed.imputation_method is ImputationMethod.KNN
    assert lookup[("PEPA", "s3")].abundance == 30.0
    assert report.method is ImputationMethod.KNN
    assert report.imputed_value_count == 1
    assert report.entries[0].entity_id == "PEPA"
    assert report.entries[0].sample_id == "s3"
    assert report.entries[0].neighbor_entity_ids == ("PEPB",)


def test_imputation_sensitivity_report_compares_downstream_policies() -> None:
    records = (
        Ms1FeatureRecord(
            feature_id="imp-sens-001",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-sens-002",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=120.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-sens-003",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=None,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-sens-004",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=None,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-sens-005",
            sample_id="case-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=101.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-sens-006",
            sample_id="case-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=119.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-sens-007",
            sample_id="ctrl-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=30.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-sens-008",
            sample_id="ctrl-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=31.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-sens-009",
            sample_id="case-1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=80.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-sens-010",
            sample_id="case-2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=82.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-sens-011",
            sample_id="ctrl-1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=78.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="imp-sens-012",
            sample_id="ctrl-2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=79.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    design = (
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
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )

    report = build_imputation_sensitivity_report(
        table,
        design,
        condition_a="case",
        condition_b="ctrl",
    )
    by_method = {entry.method: entry for entry in report.entries}

    assert report.condition_a == "case"
    assert report.condition_b == "ctrl"
    assert tuple(by_method) == (
        ImputationMethod.NONE,
        ImputationMethod.LOW_INTENSITY,
        ImputationMethod.KNN,
    )
    assert by_method[ImputationMethod.NONE].supported is True
    assert by_method[ImputationMethod.NONE].imputed_value_count == 0
    assert by_method[ImputationMethod.LOW_INTENSITY].imputed_value_count == 2
    assert by_method[ImputationMethod.KNN].imputed_value_count == 2
    assert by_method[ImputationMethod.LOW_INTENSITY].top_entity_id is not None
    assert by_method[ImputationMethod.KNN].top_entity_id is not None
