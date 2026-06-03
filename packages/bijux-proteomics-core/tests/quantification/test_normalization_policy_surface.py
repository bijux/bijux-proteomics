# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
)
from bijux_proteomics.quantification.review import (
    QuantNormalizationPolicyKind,
    build_normalization_policy_comparison_matrix_report,
)


def _records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="nrm-001",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="nrm-002",
            sample_id="s2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=200.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="nrm-003",
            sample_id="s1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=300.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="nrm-004",
            sample_id="s2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=250.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def test_normalization_policy_comparison_matrix_reports_supported_and_gaps() -> None:
    table = build_label_free_intensity_table(
        _records(),
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )
    report = build_normalization_policy_comparison_matrix_report(table)

    by_policy = {entry.policy: entry for entry in report.entries}
    log2_median_centering = by_policy[
        QuantNormalizationPolicyKind.LOG2_MEDIAN_CENTERING
    ]
    vsn_like = by_policy[QuantNormalizationPolicyKind.VSN_LIKE]

    assert by_policy[QuantNormalizationPolicyKind.MEDIAN].supported is True
    assert log2_median_centering.supported is True
    assert log2_median_centering.mapped_method is not None
    assert log2_median_centering.mapped_method.value == "log2_median_centering"
    assert vsn_like.supported is True
    assert vsn_like.mapped_method is not None
    assert vsn_like.mapped_method.value == "vsn_like"
    assert by_policy[QuantNormalizationPolicyKind.REFERENCE_CHANNEL].supported is False
    assert report.recommended_supported_policy is not None
