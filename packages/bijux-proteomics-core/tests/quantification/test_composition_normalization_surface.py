# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    Ms1FeatureRecord,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    build_normalization_strategy_comparison_report,
)


def _dominated_table() -> LabelFreeQuantTable:
    return build_label_free_intensity_table(
        (
            Ms1FeatureRecord(
                feature_id="norm-comp-001",
                sample_id="sample-a",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=100.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="norm-comp-002",
                sample_id="sample-a",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=96.0,
                protein_refs=("P002",),
            ),
            Ms1FeatureRecord(
                feature_id="norm-comp-003",
                sample_id="sample-a",
                peptide="PEPC",
                canonical_peptide="PEPC",
                intensity=92.0,
                protein_refs=("P003",),
            ),
            Ms1FeatureRecord(
                feature_id="norm-comp-004",
                sample_id="sample-b",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=105.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="norm-comp-005",
                sample_id="sample-b",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=98.0,
                protein_refs=("P002",),
            ),
            Ms1FeatureRecord(
                feature_id="norm-comp-006",
                sample_id="sample-b",
                peptide="PEPC",
                canonical_peptide="PEPC",
                intensity=95.0,
                protein_refs=("P003",),
            ),
            Ms1FeatureRecord(
                feature_id="norm-comp-007",
                sample_id="sample-c",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=900.0,
                protein_refs=("PDOM",),
            ),
            Ms1FeatureRecord(
                feature_id="norm-comp-008",
                sample_id="sample-c",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=90.0,
                protein_refs=("P002",),
            ),
            Ms1FeatureRecord(
                feature_id="norm-comp-009",
                sample_id="sample-c",
                peptide="PEPC",
                canonical_peptide="PEPC",
                intensity=82.0,
                protein_refs=("P003",),
            ),
        ),
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )


def test_normalization_strategy_downgrades_tic_under_compositional_bias() -> None:
    report = build_normalization_strategy_comparison_report(
        _dominated_table(),
        methods=(
            NormalizationMethod.TIC,
            NormalizationMethod.MEDIAN,
            NormalizationMethod.NONE,
        ),
    )
    by_method = {entry.method: entry for entry in report.entries}

    assert report.recommended_method is not NormalizationMethod.TIC
    assert (
        by_method[NormalizationMethod.TIC].balance_score
        > by_method[NormalizationMethod.MEDIAN].balance_score
    )
