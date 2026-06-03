# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.sequences import (
    PeptideChemicalLiabilityCode,
    PeptideChemicalLiabilityTier,
    build_peptide_chemical_liability_report,
    render_peptide_chemical_liability_tsv,
)


def test_peptide_chemical_liability_report_marks_balanced_tryptic_peptide_as_preferred() -> (
    None
):
    report = build_peptide_chemical_liability_report(
        "ATIDEAR",
        charge=2,
        protease="trypsin",
        observed_psm_count=5,
    )

    assert report.liability_codes == ()
    assert report.liability_penalty == 0.0
    assert report.suitability_score == 1.0
    assert report.liability_tier is PeptideChemicalLiabilityTier.PREFERRED


def test_peptide_chemical_liability_report_flags_multiple_chemical_risks() -> None:
    report = build_peptide_chemical_liability_report(
        "MNNQVVVVVVILKKDG",
        charge=4,
        protease="trypsin",
        observed_psm_count=0,
    )
    rendered = render_peptide_chemical_liability_tsv(report)

    assert report.oxidation_prone_residue_count == 1
    assert report.deamidation_prone_residue_count == 3
    assert report.basic_site_count == 3
    assert report.instability_motifs == ("DG",)
    assert report.liability_codes == (
        PeptideChemicalLiabilityCode.OXIDATION_PRONE_RESIDUES,
        PeptideChemicalLiabilityCode.DEAMIDATION_PRONE_RESIDUES,
        PeptideChemicalLiabilityCode.MISSED_CLEAVAGE_RISK,
        PeptideChemicalLiabilityCode.POOR_IONIZATION,
        PeptideChemicalLiabilityCode.INSTABILITY_MOTIF,
    )
    assert report.liability_penalty == 1.0
    assert report.suitability_score == 0.0
    assert report.liability_tier is PeptideChemicalLiabilityTier.AVOID
    assert "liability_penalty" in rendered
    assert "oxidation_prone_residues" in rendered


def test_peptide_chemical_liability_report_flags_extreme_hydrophobicity() -> None:
    report = build_peptide_chemical_liability_report(
        "VVVVVIIILLLLAAAK",
        charge=2,
        protease="trypsin",
    )

    assert PeptideChemicalLiabilityCode.EXTREME_HYDROPHOBICITY in report.liability_codes
    assert report.detectability_report.property_report.hydrophobicity_proxy > 2.5
