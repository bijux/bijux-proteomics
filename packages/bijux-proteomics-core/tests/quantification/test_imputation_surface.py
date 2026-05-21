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
