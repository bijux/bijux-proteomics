# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.quantification import (
    CompositionalBiasRisk,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    detect_compositional_bias,
    render_compositional_bias_tsv,
)


def _table():
    return build_label_free_intensity_table(
        (
            Ms1FeatureRecord(
                feature_id="comp-001",
                sample_id="balanced-1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=100.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="comp-002",
                sample_id="balanced-1",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=95.0,
                protein_refs=("P002",),
            ),
            Ms1FeatureRecord(
                feature_id="comp-003",
                sample_id="balanced-1",
                peptide="PEPC",
                canonical_peptide="PEPC",
                intensity=90.0,
                protein_refs=("P003",),
            ),
            Ms1FeatureRecord(
                feature_id="comp-004",
                sample_id="balanced-1",
                peptide="PEPD",
                canonical_peptide="PEPD",
                intensity=85.0,
                protein_refs=("P004",),
            ),
            Ms1FeatureRecord(
                feature_id="comp-005",
                sample_id="balanced-2",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=110.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="comp-006",
                sample_id="balanced-2",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=100.0,
                protein_refs=("P002",),
            ),
            Ms1FeatureRecord(
                feature_id="comp-007",
                sample_id="balanced-2",
                peptide="PEPC",
                canonical_peptide="PEPC",
                intensity=92.0,
                protein_refs=("P003",),
            ),
            Ms1FeatureRecord(
                feature_id="comp-008",
                sample_id="balanced-2",
                peptide="PEPD",
                canonical_peptide="PEPD",
                intensity=88.0,
                protein_refs=("P004",),
            ),
            Ms1FeatureRecord(
                feature_id="comp-101",
                sample_id="dominated",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=1200.0,
                protein_refs=("PDOM",),
            ),
            Ms1FeatureRecord(
                feature_id="comp-102",
                sample_id="dominated",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=110.0,
                protein_refs=("P002",),
            ),
            Ms1FeatureRecord(
                feature_id="comp-103",
                sample_id="dominated",
                peptide="PEPC",
                canonical_peptide="PEPC",
                intensity=95.0,
                protein_refs=("P003",),
            ),
            Ms1FeatureRecord(
                feature_id="comp-104",
                sample_id="dominated",
                peptide="PEPD",
                canonical_peptide="PEPD",
                intensity=75.0,
                protein_refs=("P004",),
            ),
        ),
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )


def test_compositional_bias_flags_sample_dominated_by_few_proteins() -> None:
    report = detect_compositional_bias(_table())
    by_sample = {entry.sample_id: entry for entry in report.entries}

    assert by_sample["dominated"].normalization_risk is CompositionalBiasRisk.HIGH
    assert by_sample["dominated"].dominant_entity_fraction > 0.7
    assert by_sample["dominated"].total_signal_skew > 1.5
    assert by_sample["dominated"].dominant_entities[0] == "PDOM"
    assert by_sample["balanced-1"].normalization_risk is CompositionalBiasRisk.LOW


def test_compositional_bias_renders_required_tsv_surface() -> None:
    report = detect_compositional_bias(_table())
    rendered = render_compositional_bias_tsv(report)

    assert rendered.startswith(
        "sample_id\tdominant_entity_fraction\ttotal_signal_skew\tnormalization_risk\tdominant_entities\n"
    )
    assert "\ndominated\t" in rendered
