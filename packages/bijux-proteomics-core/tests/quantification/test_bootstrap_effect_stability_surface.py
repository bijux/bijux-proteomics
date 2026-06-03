# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    BootstrapEffectRobustnessTier,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    bootstrap_effect_stability,
    build_label_free_intensity_table,
    render_bootstrap_effect_stability_tsv,
)


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="control-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="control-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="control-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="control-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="control-3",
            condition="control",
            replicate=3,
            fraction=1,
            spectra_file="control-3.mzml",
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
        ExperimentalDesignEntry(
            sample_id="case-3",
            condition="case",
            replicate=3,
            fraction=1,
            spectra_file="case-3.mzml",
        ),
    )


def _table():
    return build_label_free_intensity_table(
        (
            Ms1FeatureRecord(
                feature_id="bootstrap-001",
                sample_id="control-1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=100.0,
                protein_refs=("PSTABLE",),
            ),
            Ms1FeatureRecord(
                feature_id="bootstrap-002",
                sample_id="control-2",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=104.0,
                protein_refs=("PSTABLE",),
            ),
            Ms1FeatureRecord(
                feature_id="bootstrap-003",
                sample_id="control-3",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=108.0,
                protein_refs=("PSTABLE",),
            ),
            Ms1FeatureRecord(
                feature_id="bootstrap-004",
                sample_id="case-1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=198.0,
                protein_refs=("PSTABLE",),
            ),
            Ms1FeatureRecord(
                feature_id="bootstrap-005",
                sample_id="case-2",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=205.0,
                protein_refs=("PSTABLE",),
            ),
            Ms1FeatureRecord(
                feature_id="bootstrap-006",
                sample_id="case-3",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=212.0,
                protein_refs=("PSTABLE",),
            ),
            Ms1FeatureRecord(
                feature_id="bootstrap-101",
                sample_id="control-1",
                peptide="PEPX",
                canonical_peptide="PEPX",
                intensity=80.0,
                protein_refs=("PSWING",),
            ),
            Ms1FeatureRecord(
                feature_id="bootstrap-102",
                sample_id="control-2",
                peptide="PEPX",
                canonical_peptide="PEPX",
                intensity=82.0,
                protein_refs=("PSWING",),
            ),
            Ms1FeatureRecord(
                feature_id="bootstrap-103",
                sample_id="control-3",
                peptide="PEPX",
                canonical_peptide="PEPX",
                intensity=320.0,
                protein_refs=("PSWING",),
            ),
            Ms1FeatureRecord(
                feature_id="bootstrap-104",
                sample_id="case-1",
                peptide="PEPX",
                canonical_peptide="PEPX",
                intensity=60.0,
                protein_refs=("PSWING",),
            ),
            Ms1FeatureRecord(
                feature_id="bootstrap-105",
                sample_id="case-2",
                peptide="PEPX",
                canonical_peptide="PEPX",
                intensity=170.0,
                protein_refs=("PSWING",),
            ),
            Ms1FeatureRecord(
                feature_id="bootstrap-106",
                sample_id="case-3",
                peptide="PEPX",
                canonical_peptide="PEPX",
                intensity=175.0,
                protein_refs=("PSWING",),
            ),
        ),
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )


def test_bootstrap_effect_stability_marks_direction_switching_entity_unstable() -> None:
    report = bootstrap_effect_stability(
        _table(),
        _design(),
        condition_a="control",
        condition_b="case",
        n_resamples=120,
        random_seed=17,
    )
    by_entity = {entry.entity_id: entry for entry in report.entries}

    assert by_entity["PSTABLE"].robustness_tier is BootstrapEffectRobustnessTier.STABLE
    assert by_entity["PSTABLE"].sign_consistency > 0.95
    assert by_entity["PSWING"].robustness_tier is BootstrapEffectRobustnessTier.UNSTABLE
    assert by_entity["PSWING"].sign_consistency < 0.75


def test_bootstrap_effect_stability_surfaces_q_value_stability_and_tsv_columns() -> (
    None
):
    report = bootstrap_effect_stability(
        _table(),
        _design(),
        condition_a="control",
        condition_b="case",
        n_resamples=120,
        random_seed=17,
    )
    by_entity = {entry.entity_id: entry for entry in report.entries}
    rendered = render_bootstrap_effect_stability_tsv(report)

    assert (
        by_entity["PSTABLE"].q_value_stability > by_entity["PSWING"].q_value_stability
    )
    assert rendered.startswith(
        "entity_id\tmedian_log2fc\tsign_consistency\tq_value_stability\trobustness_tier\n"
    )
    assert "\nPSWING\t" in rendered
