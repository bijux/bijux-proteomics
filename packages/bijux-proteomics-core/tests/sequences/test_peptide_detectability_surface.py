# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from math import isclose

from bijux_proteomics.sequences import (
    PeptideDetectabilityTier,
    PeptideUniquenessClass,
    build_peptide_detectability_report,
    render_peptide_detectability_tsv,
)


def test_peptide_detectability_report_scores_balanced_unique_peptide_as_high() -> None:
    report = build_peptide_detectability_report(
        "AKTIDEK",
        charge=2,
        protease="trypsin",
        uniqueness_class=PeptideUniquenessClass.UNIQUE,
        observed_psm_count=5,
    )

    assert report.detectability_tier is PeptideDetectabilityTier.HIGH
    assert report.top_tier_length_mass_eligible is True
    assert report.chargeability_score == 1.0
    assert report.uniqueness_score == 1.0
    assert report.property_report.length == 7
    assert isclose(
        sum(
            (
                report.length_score * 0.15,
                report.mass_score * 0.15,
                report.chargeability_score * 0.15,
                report.hydrophobicity_score * 0.10,
                report.missed_cleavage_score * 0.10,
                report.uniqueness_score * 0.15,
                report.problematic_residue_score * 0.10,
                report.observed_evidence_score * 0.10,
            )
        ),
        report.detectability_score,
        rel_tol=0.0,
        abs_tol=1e-9,
    )


def test_peptide_detectability_report_blocks_top_tier_outside_valid_length_range() -> (
    None
):
    report = build_peptide_detectability_report(
        "PEPTI",
        charge=2,
        protease="trypsin",
        uniqueness_class=PeptideUniquenessClass.UNIQUE,
        observed_psm_count=10,
    )

    assert report.top_tier_length_mass_eligible is False
    assert report.detectability_tier is not PeptideDetectabilityTier.HIGH
    assert report.length_score < 1.0


def test_peptide_detectability_report_penalizes_problematic_residues_and_shared_peptides() -> (
    None
):
    report = build_peptide_detectability_report(
        "MNNQCKR",
        charge=2,
        protease="trypsin",
        uniqueness_class=PeptideUniquenessClass.SHARED,
        observed_psm_count=1,
    )
    rendered = render_peptide_detectability_tsv(report)

    assert report.problematic_residue_count == 5
    assert report.problematic_residues == ("M", "N", "N", "Q", "C")
    assert report.problematic_residue_score < 0.5
    assert report.uniqueness_score == 0.45
    assert "detectability_tier" in rendered
