# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import math

import pytest

from bijux_proteomics.quantification import (
    Ms1FeatureRecord,
    build_peptide_intensity_matrix_from_features,
)
from bijux_proteomics.quantification.model_rollup import (
    PeptideToProteinEntry,
    fit_peptide_bias_model,
    render_peptide_bias_tsv,
    render_protein_abundance_tsv,
    render_rollup_residuals_tsv,
)


def test_fit_peptide_bias_model_learns_constant_peptide_offsets_without_distorting_sample_effect() -> (
    None
):
    peptide_matrix = build_peptide_intensity_matrix_from_features(
        (
            Ms1FeatureRecord(
                feature_id="f001",
                sample_id="control-1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=100.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="f002",
                sample_id="case-1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=400.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="f003",
                sample_id="control-1",
                peptide="PEPG",
                canonical_peptide="PEPG",
                intensity=400.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="f004",
                sample_id="case-1",
                peptide="PEPG",
                canonical_peptide="PEPG",
                intensity=1600.0,
                protein_refs=("P001",),
            ),
        )
    )

    report = fit_peptide_bias_model(
        peptide_matrix,
        (
            PeptideToProteinEntry(peptide_id="PEPA", protein_id="P001"),
            PeptideToProteinEntry(peptide_id="PEPG", protein_id="P001"),
        ),
    )

    abundance_lookup = {
        (entry.protein_id, entry.sample_id): entry for entry in report.protein_abundance
    }
    bias_lookup = {(entry.protein_id, entry.peptide_id): entry for entry in report.peptide_bias}

    assert len(report.protein_abundance) == 2
    assert len(report.peptide_bias) == 2
    assert len(report.residuals) == 4
    assert math.isclose(
        abundance_lookup[("P001", "case-1")].log2_abundance
        - abundance_lookup[("P001", "control-1")].log2_abundance,
        2.0,
        abs_tol=1e-6,
    )
    assert math.isclose(
        abundance_lookup[("P001", "control-1")].abundance,
        200.0,
        abs_tol=1e-6,
    )
    assert math.isclose(
        abundance_lookup[("P001", "case-1")].abundance,
        800.0,
        abs_tol=1e-6,
    )
    assert math.isclose(
        bias_lookup[("P001", "PEPA")].peptide_bias_log2,
        -1.0,
        abs_tol=1e-6,
    )
    assert math.isclose(bias_lookup[("P001", "PEPG")].peptide_bias_log2, 1.0, abs_tol=1e-6)
    assert all(abs(entry.residual_log2) <= 1e-6 for entry in report.residuals)
    assert "protein_id\tsample_id\tabundance\tlog2_abundance\tsupporting_peptide_count" in render_protein_abundance_tsv(report)
    assert "peptide_bias_log2" in render_peptide_bias_tsv(report)
    assert "residual_log2" in render_rollup_residuals_tsv(report)


def test_fit_peptide_bias_model_rejects_conflicting_peptide_assignments() -> None:
    peptide_matrix = build_peptide_intensity_matrix_from_features(
        (
            Ms1FeatureRecord(
                feature_id="conflict-001",
                sample_id="sample-1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=100.0,
                protein_refs=("P001",),
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="must assign each peptide to exactly one protein",
    ):
        fit_peptide_bias_model(
            peptide_matrix,
            (
                PeptideToProteinEntry(peptide_id="PEPA", protein_id="P001"),
                PeptideToProteinEntry(peptide_id="PEPA", protein_id="P002"),
            ),
        )
