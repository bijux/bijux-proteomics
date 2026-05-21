# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.quantification import (
    ImputationMethod,
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_imputation_report,
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
