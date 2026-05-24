# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.quantification import (
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
)
from bijux_proteomics.quantification.variance_model import (
    fit_mean_variance_trend,
    render_mean_variance_trend_tsv,
)


def test_fit_mean_variance_trend_lowers_confidence_for_low_intensity_noisy_entities() -> (
    None
):
    table = build_label_free_intensity_table(
        (
            Ms1FeatureRecord(
                feature_id="low-noisy-001",
                sample_id="s1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=5.0,
                protein_refs=("P_LOW_NOISY",),
            ),
            Ms1FeatureRecord(
                feature_id="low-noisy-002",
                sample_id="s2",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=40.0,
                protein_refs=("P_LOW_NOISY",),
            ),
            Ms1FeatureRecord(
                feature_id="low-noisy-003",
                sample_id="s3",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=6.0,
                protein_refs=("P_LOW_NOISY",),
            ),
            Ms1FeatureRecord(
                feature_id="low-noisy-004",
                sample_id="s4",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=38.0,
                protein_refs=("P_LOW_NOISY",),
            ),
            Ms1FeatureRecord(
                feature_id="low-stable-001",
                sample_id="s1",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=18.0,
                protein_refs=("P_LOW_STABLE",),
            ),
            Ms1FeatureRecord(
                feature_id="low-stable-002",
                sample_id="s2",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=20.0,
                protein_refs=("P_LOW_STABLE",),
            ),
            Ms1FeatureRecord(
                feature_id="low-stable-003",
                sample_id="s3",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=19.0,
                protein_refs=("P_LOW_STABLE",),
            ),
            Ms1FeatureRecord(
                feature_id="low-stable-004",
                sample_id="s4",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=21.0,
                protein_refs=("P_LOW_STABLE",),
            ),
            Ms1FeatureRecord(
                feature_id="high-stable-001",
                sample_id="s1",
                peptide="PEPC",
                canonical_peptide="PEPC",
                intensity=980.0,
                protein_refs=("P_HIGH_STABLE",),
            ),
            Ms1FeatureRecord(
                feature_id="high-stable-002",
                sample_id="s2",
                peptide="PEPC",
                canonical_peptide="PEPC",
                intensity=1000.0,
                protein_refs=("P_HIGH_STABLE",),
            ),
            Ms1FeatureRecord(
                feature_id="high-stable-003",
                sample_id="s3",
                peptide="PEPC",
                canonical_peptide="PEPC",
                intensity=1020.0,
                protein_refs=("P_HIGH_STABLE",),
            ),
            Ms1FeatureRecord(
                feature_id="high-stable-004",
                sample_id="s4",
                peptide="PEPC",
                canonical_peptide="PEPC",
                intensity=1040.0,
                protein_refs=("P_HIGH_STABLE",),
            ),
        ),
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    report = fit_mean_variance_trend(table)
    rendered = render_mean_variance_trend_tsv(report)
    entry_lookup = {entry.entity_id: entry for entry in report.entries}

    low_noisy = entry_lookup["P_LOW_NOISY"]
    low_stable = entry_lookup["P_LOW_STABLE"]
    high_stable = entry_lookup["P_HIGH_STABLE"]

    assert low_noisy.mean_intensity < high_stable.mean_intensity
    assert low_noisy.observed_variance > low_stable.observed_variance
    assert low_noisy.expected_variance >= high_stable.expected_variance
    assert low_noisy.variance_residual > 0.0
    assert low_noisy.quantitative_confidence < low_stable.quantitative_confidence
    assert low_noisy.quantitative_confidence < high_stable.quantitative_confidence
    assert high_stable.quantitative_confidence > 0.8
    assert (
        "entity_id\tmean_intensity\tobserved_variance\texpected_variance\tvariance_residual"
        in rendered
    )


def test_fit_mean_variance_trend_accepts_canonical_quant_matrix() -> None:
    table = build_label_free_intensity_table(
        (
            Ms1FeatureRecord(
                feature_id="canonical-001",
                sample_id="s1",
                peptide="PEPD",
                canonical_peptide="PEPD",
                intensity=100.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="canonical-002",
                sample_id="s2",
                peptide="PEPD",
                canonical_peptide="PEPD",
                intensity=120.0,
                protein_refs=("P001",),
            ),
        ),
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    report = fit_mean_variance_trend(table.to_quant_matrix())

    assert len(report.entries) == 1
    assert report.entries[0].entity_id == "P001"
    assert report.entries[0].observed_sample_count == 2
