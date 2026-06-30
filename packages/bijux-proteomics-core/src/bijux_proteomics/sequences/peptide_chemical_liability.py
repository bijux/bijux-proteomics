# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Peptide chemical liability scoring for assay choice and evidence review."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.modifications import ModificationRegistryDocument
from bijux_proteomics.sequences.digestion import ProteaseRule
from bijux_proteomics.sequences.peptide_detectability import (
    PeptideDetectabilityReport,
    build_peptide_detectability_report,
)
from bijux_proteomics_foundation import JsonModel

_OXIDATION_PRONE_RESIDUES = frozenset({"M", "W"})
_DEAMIDATION_PRONE_RESIDUES = frozenset({"N", "Q"})
_BASIC_RESIDUES = frozenset({"K", "R", "H"})
_INSTABILITY_MOTIFS = (
    "DG",
    "DP",
    "NG",
    "NS",
    "NT",
)


class PeptideChemicalLiabilityCode(StrEnum):
    """Stable chemical liability codes that should affect peptide trust."""

    OXIDATION_PRONE_RESIDUES = "oxidation_prone_residues"
    DEAMIDATION_PRONE_RESIDUES = "deamidation_prone_residues"
    MISSED_CLEAVAGE_RISK = "missed_cleavage_risk"
    EXTREME_HYDROPHOBICITY = "extreme_hydrophobicity"
    POOR_IONIZATION = "poor_ionization"
    INSTABILITY_MOTIF = "instability_motif"


class PeptideChemicalLiabilityTier(StrEnum):
    """Selection posture implied by chemical liability."""

    PREFERRED = "preferred"
    CAUTION = "caution"
    AVOID = "avoid"


class PeptideChemicalLiabilityReport(JsonModel):
    """One peptide-level chemical liability assessment with downstream-ready penalty."""

    model_config = ConfigDict(extra="forbid")

    detectability_report: PeptideDetectabilityReport
    oxidation_prone_residue_count: int = Field(..., ge=0)
    deamidation_prone_residue_count: int = Field(..., ge=0)
    basic_site_count: int = Field(..., ge=0)
    instability_motifs: tuple[str, ...] = Field(default_factory=tuple)
    liability_codes: tuple[PeptideChemicalLiabilityCode, ...] = Field(
        default_factory=tuple
    )
    liability_penalty: float = Field(..., ge=0.0, le=1.0)
    suitability_score: float = Field(..., ge=0.0, le=1.0)
    liability_tier: PeptideChemicalLiabilityTier


def build_peptide_chemical_liability_report(
    sequence: str,
    *,
    modification_assignments: tuple[str, ...] = (),
    charge: int = 2,
    protease: ProteaseRule | str = "trypsin",
    registry: ModificationRegistryDocument | None = None,
    observed_psm_count: int | None = None,
) -> PeptideChemicalLiabilityReport:
    """Score sequence-level chemical liabilities that should affect peptide trust."""
    detectability_report = build_peptide_detectability_report(
        sequence,
        modification_assignments=modification_assignments,
        charge=charge,
        protease=protease,
        registry=registry,
        observed_psm_count=observed_psm_count,
    )
    residue_sequence = detectability_report.property_report.residue_sequence
    oxidation_prone_residue_count = sum(
        1 for residue in residue_sequence if residue in _OXIDATION_PRONE_RESIDUES
    )
    deamidation_prone_residue_count = sum(
        1 for residue in residue_sequence if residue in _DEAMIDATION_PRONE_RESIDUES
    )
    basic_site_count = 1 + sum(
        1 for residue in residue_sequence if residue in _BASIC_RESIDUES
    )
    instability_motifs = tuple(
        motif for motif in _INSTABILITY_MOTIFS if motif in residue_sequence
    )

    oxidation_penalty = min(0.18 * oxidation_prone_residue_count, 0.54)
    deamidation_penalty = min(0.12 * deamidation_prone_residue_count, 0.48)
    missed_cleavage_penalty = _missed_cleavage_penalty(
        detectability_report.property_report.missed_cleavages
    )
    hydrophobicity_penalty = _hydrophobicity_penalty(
        detectability_report.property_report.hydrophobicity_proxy
    )
    ionization_penalty = _ionization_penalty(
        chargeability_score=detectability_report.chargeability_score,
        basic_site_count=basic_site_count,
    )
    instability_penalty = min(0.1 * len(instability_motifs), 0.3)

    liability_codes: list[PeptideChemicalLiabilityCode] = []
    if oxidation_prone_residue_count:
        liability_codes.append(PeptideChemicalLiabilityCode.OXIDATION_PRONE_RESIDUES)
    if deamidation_prone_residue_count:
        liability_codes.append(PeptideChemicalLiabilityCode.DEAMIDATION_PRONE_RESIDUES)
    if missed_cleavage_penalty > 0.0:
        liability_codes.append(PeptideChemicalLiabilityCode.MISSED_CLEAVAGE_RISK)
    if hydrophobicity_penalty > 0.0:
        liability_codes.append(PeptideChemicalLiabilityCode.EXTREME_HYDROPHOBICITY)
    if ionization_penalty > 0.0:
        liability_codes.append(PeptideChemicalLiabilityCode.POOR_IONIZATION)
    if instability_motifs:
        liability_codes.append(PeptideChemicalLiabilityCode.INSTABILITY_MOTIF)

    liability_penalty = min(
        oxidation_penalty
        + deamidation_penalty
        + missed_cleavage_penalty
        + hydrophobicity_penalty
        + ionization_penalty
        + instability_penalty,
        1.0,
    )
    suitability_score = max(0.0, 1.0 - liability_penalty)

    return PeptideChemicalLiabilityReport(
        detectability_report=detectability_report,
        oxidation_prone_residue_count=oxidation_prone_residue_count,
        deamidation_prone_residue_count=deamidation_prone_residue_count,
        basic_site_count=basic_site_count,
        instability_motifs=instability_motifs,
        liability_codes=tuple(liability_codes),
        liability_penalty=liability_penalty,
        suitability_score=suitability_score,
        liability_tier=_liability_tier(suitability_score),
    )


def render_peptide_chemical_liability_tsv(
    report: PeptideChemicalLiabilityReport,
) -> str:
    """Render a flat TSV row for chemical-liability review."""
    return (
        "canonical_notation\tresidue_sequence\tcharge\tmissed_cleavages\t"
        "hydrophobicity_proxy\tchargeability_score\toxidation_prone_residue_count\t"
        "deamidation_prone_residue_count\tbasic_site_count\tinstability_motifs\t"
        "liability_codes\tliability_penalty\tsuitability_score\tliability_tier\n"
        f"{report.detectability_report.property_report.canonical_notation}\t"
        f"{report.detectability_report.property_report.residue_sequence}\t"
        f"{report.detectability_report.property_report.charge}\t"
        f"{report.detectability_report.property_report.missed_cleavages}\t"
        f"{report.detectability_report.property_report.hydrophobicity_proxy:.6f}\t"
        f"{report.detectability_report.chargeability_score:.6f}\t"
        f"{report.oxidation_prone_residue_count}\t"
        f"{report.deamidation_prone_residue_count}\t"
        f"{report.basic_site_count}\t"
        f"{';'.join(report.instability_motifs)}\t"
        f"{';'.join(code.value for code in report.liability_codes)}\t"
        f"{report.liability_penalty:.6f}\t"
        f"{report.suitability_score:.6f}\t"
        f"{report.liability_tier.value}\n"
    )


def _missed_cleavage_penalty(missed_cleavages: int) -> float:
    if missed_cleavages <= 0:
        return 0.0
    if missed_cleavages == 1:
        return 0.12
    if missed_cleavages == 2:
        return 0.28
    return 0.45


def _hydrophobicity_penalty(hydrophobicity_proxy: float) -> float:
    magnitude = abs(hydrophobicity_proxy)
    if magnitude <= 1.5:
        return 0.0
    if magnitude <= 2.5:
        return 0.15
    return 0.35


def _ionization_penalty(*, chargeability_score: float, basic_site_count: int) -> float:
    if chargeability_score >= 0.7 and basic_site_count >= 2:
        return 0.0
    if chargeability_score >= 0.45 and basic_site_count >= 1:
        return 0.18
    return 0.35


def _liability_tier(suitability_score: float) -> PeptideChemicalLiabilityTier:
    if suitability_score >= 0.75:
        return PeptideChemicalLiabilityTier.PREFERRED
    if suitability_score >= 0.45:
        return PeptideChemicalLiabilityTier.CAUTION
    return PeptideChemicalLiabilityTier.AVOID
