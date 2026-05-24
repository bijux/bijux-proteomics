# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.quantification import (
    Ms1FeatureRecord,
    build_peptide_intensity_matrix_from_features,
)
from bijux_proteomics.quantification.model_rollup import (
    PeptideToProteinEntry,
    fit_peptide_bias_model,
)
from bijux_proteomics.quantification.uncertainty import (
    ProteinUncertaintySource,
    estimate_protein_uncertainty,
    render_protein_uncertainty_tsv,
)


def test_estimate_protein_uncertainty_widens_single_peptide_intervals() -> None:
    rollup = fit_peptide_bias_model(
        build_peptide_intensity_matrix_from_features(
            (
                Ms1FeatureRecord(
                    feature_id="multi-001",
                    sample_id="sample-a",
                    peptide="PEPA",
                    canonical_peptide="PEPA",
                    intensity=100.0,
                    protein_refs=("P001",),
                ),
                Ms1FeatureRecord(
                    feature_id="multi-002",
                    sample_id="sample-b",
                    peptide="PEPA",
                    canonical_peptide="PEPA",
                    intensity=400.0,
                    protein_refs=("P001",),
                ),
                Ms1FeatureRecord(
                    feature_id="multi-003",
                    sample_id="sample-a",
                    peptide="PEPG",
                    canonical_peptide="PEPG",
                    intensity=400.0,
                    protein_refs=("P001",),
                ),
                Ms1FeatureRecord(
                    feature_id="multi-004",
                    sample_id="sample-b",
                    peptide="PEPG",
                    canonical_peptide="PEPG",
                    intensity=1600.0,
                    protein_refs=("P001",),
                ),
                Ms1FeatureRecord(
                    feature_id="single-001",
                    sample_id="sample-a",
                    peptide="QLTK",
                    canonical_peptide="QLTK",
                    intensity=220.0,
                    protein_refs=("P002",),
                ),
                Ms1FeatureRecord(
                    feature_id="single-002",
                    sample_id="sample-b",
                    peptide="QLTK",
                    canonical_peptide="QLTK",
                    intensity=880.0,
                    protein_refs=("P002",),
                ),
            )
        ),
        (
            PeptideToProteinEntry(peptide_id="PEPA", protein_id="P001"),
            PeptideToProteinEntry(peptide_id="PEPG", protein_id="P001"),
            PeptideToProteinEntry(peptide_id="QLTK", protein_id="P002"),
        ),
    )

    report = estimate_protein_uncertainty(rollup)
    rendered = render_protein_uncertainty_tsv(report)

    lookup = {(entry.protein_id, entry.sample_id): entry for entry in report.entries}
    multi_width = (
        lookup[("P001", "sample-a")].upper_ci - lookup[("P001", "sample-a")].lower_ci
    )
    single_width = (
        lookup[("P002", "sample-a")].upper_ci - lookup[("P002", "sample-a")].lower_ci
    )

    assert single_width > multi_width
    assert lookup[("P001", "sample-a")].uncertainty_source is ProteinUncertaintySource.MULTI_PEPTIDE_SUPPORT
    assert lookup[("P002", "sample-a")].uncertainty_source is ProteinUncertaintySource.SINGLE_PEPTIDE_SUPPORT
    assert lookup[("P002", "sample-a")].supporting_peptide_count == 1
    assert "uncertainty_source" in rendered
    assert "supporting_peptide_count" in rendered


def test_estimate_protein_uncertainty_widens_residual_disagreement_intervals() -> None:
    clean_rollup = fit_peptide_bias_model(
        build_peptide_intensity_matrix_from_features(
            (
                Ms1FeatureRecord(
                    feature_id="clean-001",
                    sample_id="sample-a",
                    peptide="AAAK",
                    canonical_peptide="AAAK",
                    intensity=100.0,
                    protein_refs=("P010",),
                ),
                Ms1FeatureRecord(
                    feature_id="clean-002",
                    sample_id="sample-b",
                    peptide="AAAK",
                    canonical_peptide="AAAK",
                    intensity=200.0,
                    protein_refs=("P010",),
                ),
                Ms1FeatureRecord(
                    feature_id="clean-003",
                    sample_id="sample-a",
                    peptide="GGGK",
                    canonical_peptide="GGGK",
                    intensity=200.0,
                    protein_refs=("P010",),
                ),
                Ms1FeatureRecord(
                    feature_id="clean-004",
                    sample_id="sample-b",
                    peptide="GGGK",
                    canonical_peptide="GGGK",
                    intensity=400.0,
                    protein_refs=("P010",),
                ),
            )
        ),
        (
            PeptideToProteinEntry(peptide_id="AAAK", protein_id="P010"),
            PeptideToProteinEntry(peptide_id="GGGK", protein_id="P010"),
        ),
    )
    noisy_rollup = fit_peptide_bias_model(
        build_peptide_intensity_matrix_from_features(
            (
                Ms1FeatureRecord(
                    feature_id="noisy-001",
                    sample_id="sample-a",
                    peptide="AAAK",
                    canonical_peptide="AAAK",
                    intensity=100.0,
                    protein_refs=("P020",),
                ),
                Ms1FeatureRecord(
                    feature_id="noisy-002",
                    sample_id="sample-b",
                    peptide="AAAK",
                    canonical_peptide="AAAK",
                    intensity=200.0,
                    protein_refs=("P020",),
                ),
                Ms1FeatureRecord(
                    feature_id="noisy-003",
                    sample_id="sample-a",
                    peptide="GGGK",
                    canonical_peptide="GGGK",
                    intensity=200.0,
                    protein_refs=("P020",),
                ),
                Ms1FeatureRecord(
                    feature_id="noisy-004",
                    sample_id="sample-b",
                    peptide="GGGK",
                    canonical_peptide="GGGK",
                    intensity=700.0,
                    protein_refs=("P020",),
                ),
            )
        ),
        (
            PeptideToProteinEntry(peptide_id="AAAK", protein_id="P020"),
            PeptideToProteinEntry(peptide_id="GGGK", protein_id="P020"),
        ),
    )

    clean = estimate_protein_uncertainty(clean_rollup)
    noisy = estimate_protein_uncertainty(noisy_rollup)
    clean_entry = next(
        entry
        for entry in clean.entries
        if entry.protein_id == "P010" and entry.sample_id == "sample-b"
    )
    noisy_entry = next(
        entry
        for entry in noisy.entries
        if entry.protein_id == "P020" and entry.sample_id == "sample-b"
    )

    clean_width = clean_entry.upper_ci - clean_entry.lower_ci
    noisy_width = noisy_entry.upper_ci - noisy_entry.lower_ci

    assert noisy_width > clean_width
    assert noisy_entry.uncertainty_source is ProteinUncertaintySource.RESIDUAL_DISPERSION
