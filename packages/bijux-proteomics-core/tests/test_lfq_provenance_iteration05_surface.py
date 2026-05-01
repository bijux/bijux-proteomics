# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    NormalizationMethod,
    QuantRollupMethod,
)
from bijux_proteomics.quantification_iteration05 import (
    build_lfq_feature_peptide_protein_provenance_report,
)


def _records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="f-001",
            sample_id="s1",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            intensity=1000.0,
            protein_refs=("P11111",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="f-002",
            sample_id="s2",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            intensity=900.0,
            protein_refs=("P11111",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="f-003",
            sample_id="s1",
            peptide="PEPTIDER",
            canonical_peptide="PEPTIDER",
            intensity=600.0,
            protein_refs=("P22222", "P33333"),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="f-004",
            sample_id="s2",
            peptide="PEPTIDER",
            canonical_peptide="PEPTIDER",
            intensity=None,
            protein_refs=("P22222", "P33333"),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
    )


def test_lfq_feature_peptide_protein_provenance_report_preserves_provenance_and_missingness() -> None:
    report = build_lfq_feature_peptide_protein_provenance_report(
        _records(),
        aggregation_method=QuantRollupMethod.SUM,
        normalization_method=NormalizationMethod.MEDIAN,
    )

    assert report.feature_entry_count == 4
    assert report.peptide_entry_count == 4
    assert report.protein_entry_count == 6
    assert report.normalization_method is NormalizationMethod.MEDIAN
    assert report.peptide_missingness.entries[0].observed_count >= 1
    assert len(report.note) > 20
