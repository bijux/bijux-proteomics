# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Peptide detectability scoring for observability and assay suitability."""

from __future__ import annotations

from enum import StrEnum
from math import isclose

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.modifications import ModificationRegistryDocument
from bijux_proteomics.sequences.digestion import ProteaseRule
from bijux_proteomics.sequences.peptide_properties import (
    PeptidePropertyReport,
    build_peptide_property_report,
)
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    PeptideUniquenessClass,
)
from bijux_proteomics_foundation import JsonModel

_TOP_TIER_MIN_LENGTH = 7
_TOP_TIER_MAX_LENGTH = 25
_TOP_TIER_MIN_MONOISOTOPIC_MASS = 700.0
_TOP_TIER_MAX_MONOISOTOPIC_MASS = 3000.0
_PROBLEMATIC_RESIDUES = frozenset({"C", "M", "N", "Q"})


class PeptideDetectabilityTier(StrEnum):
    """Stable detectability tiers for peptide observability."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PeptideDetectabilityReport(JsonModel):
    """One peptide detectability report with score components and tier."""

    model_config = ConfigDict(extra="forbid")

    property_report: PeptidePropertyReport
    uniqueness_class: PeptideUniquenessClass | None = None
    uniqueness_score: float = Field(..., ge=0.0, le=1.0)
    observed_psm_count: int | None = Field(default=None, ge=0)
    observed_evidence_score: float = Field(..., ge=0.0, le=1.0)
    chargeability_score: float = Field(..., ge=0.0, le=1.0)
    length_score: float = Field(..., ge=0.0, le=1.0)
    mass_score: float = Field(..., ge=0.0, le=1.0)
    hydrophobicity_score: float = Field(..., ge=0.0, le=1.0)
    missed_cleavage_score: float = Field(..., ge=0.0, le=1.0)
    problematic_residue_score: float = Field(..., ge=0.0, le=1.0)
    problematic_residue_count: int = Field(..., ge=0)
    problematic_residues: tuple[str, ...] = Field(default_factory=tuple)
    detectability_score: float = Field(..., ge=0.0, le=1.0)
    detectability_tier: PeptideDetectabilityTier
    top_tier_length_mass_eligible: bool = False


def build_peptide_detectability_report(
    sequence: str,
    *,
    modification_assignments: tuple[str, ...] = (),
    charge: int = 2,
    protease: ProteaseRule | str = "trypsin",
    registry: ModificationRegistryDocument | None = None,
    uniqueness_class: PeptideUniquenessClass | str | None = None,
    uniqueness_score: float | None = None,
    observed_psm_count: int | None = None,
) -> PeptideDetectabilityReport:
    """Build a peptide detectability report from owned sequence and chemistry semantics."""
    property_report = build_peptide_property_report(
        sequence,
        modification_assignments=modification_assignments,
        charge=charge,
        protease=protease,
        registry=registry,
    )
    resolved_uniqueness_class = (
        PeptideUniquenessClass(uniqueness_class)
        if isinstance(uniqueness_class, str)
        else uniqueness_class
    )
    resolved_uniqueness_score = _resolve_uniqueness_score(
        uniqueness_class=resolved_uniqueness_class,
        uniqueness_score=uniqueness_score,
    )
    observed_evidence_score = _observed_evidence_score(observed_psm_count)
    chargeability_score = _chargeability_score(
        sequence=property_report.residue_sequence,
        charge=property_report.charge,
    )
    length_score = _length_score(property_report.length)
    mass_score = _mass_score(property_report.monoisotopic_mass)
    hydrophobicity_score = _hydrophobicity_score(property_report.hydrophobicity_proxy)
    missed_cleavage_score = _missed_cleavage_score(property_report.missed_cleavages)
    problematic_residues = _problematic_residues(property_report.residue_sequence)
    problematic_residue_score = _problematic_residue_score(len(problematic_residues))
    top_tier_length_mass_eligible = _top_tier_length_mass_eligible(
        length=property_report.length,
        monoisotopic_mass=property_report.monoisotopic_mass,
    )
    detectability_score = _bounded_score(
        (length_score * 0.15)
        + (mass_score * 0.15)
        + (chargeability_score * 0.15)
        + (hydrophobicity_score * 0.10)
        + (missed_cleavage_score * 0.10)
        + (resolved_uniqueness_score * 0.15)
        + (problematic_residue_score * 0.10)
        + (observed_evidence_score * 0.10)
    )
    detectability_tier = _detectability_tier(
        detectability_score=detectability_score,
        top_tier_length_mass_eligible=top_tier_length_mass_eligible,
        chargeability_score=chargeability_score,
        resolved_uniqueness_score=resolved_uniqueness_score,
    )
    return PeptideDetectabilityReport(
        property_report=property_report,
        uniqueness_class=resolved_uniqueness_class,
        uniqueness_score=resolved_uniqueness_score,
        observed_psm_count=observed_psm_count,
        observed_evidence_score=observed_evidence_score,
        chargeability_score=chargeability_score,
        length_score=length_score,
        mass_score=mass_score,
        hydrophobicity_score=hydrophobicity_score,
        missed_cleavage_score=missed_cleavage_score,
        problematic_residue_score=problematic_residue_score,
        problematic_residue_count=len(problematic_residues),
        problematic_residues=problematic_residues,
        detectability_score=detectability_score,
        detectability_tier=detectability_tier,
        top_tier_length_mass_eligible=top_tier_length_mass_eligible,
    )


def render_peptide_detectability_tsv(report: PeptideDetectabilityReport) -> str:
    """Render one stable TSV row for peptide detectability review."""
    values = (
        report.property_report.canonical_notation,
        report.property_report.residue_sequence,
        report.property_report.protease,
        str(report.property_report.charge),
        str(report.property_report.length),
        f"{report.property_report.monoisotopic_mass:.6f}",
        f"{report.property_report.mz_monoisotopic:.6f}",
        str(report.property_report.missed_cleavages),
        f"{report.property_report.hydrophobicity_proxy:.6f}",
        report.uniqueness_class.value if report.uniqueness_class else "",
        f"{report.uniqueness_score:.6f}",
        "" if report.observed_psm_count is None else str(report.observed_psm_count),
        f"{report.observed_evidence_score:.6f}",
        f"{report.chargeability_score:.6f}",
        f"{report.length_score:.6f}",
        f"{report.mass_score:.6f}",
        f"{report.hydrophobicity_score:.6f}",
        f"{report.missed_cleavage_score:.6f}",
        f"{report.problematic_residue_score:.6f}",
        str(report.problematic_residue_count),
        ";".join(report.problematic_residues),
        f"{report.detectability_score:.6f}",
        report.detectability_tier.value,
        "true" if report.top_tier_length_mass_eligible else "false",
    )
    header = (
        "canonical_notation\tresidue_sequence\tprotease\tcharge\tlength\t"
        "monoisotopic_mass\tmz_monoisotopic\tmissed_cleavages\t"
        "hydrophobicity_proxy\tuniqueness_class\tuniqueness_score\t"
        "observed_psm_count\tobserved_evidence_score\tchargeability_score\t"
        "length_score\tmass_score\thydrophobicity_score\t"
        "missed_cleavage_score\tproblematic_residue_score\t"
        "problematic_residue_count\tproblematic_residues\t"
        "detectability_score\tdetectability_tier\t"
        "top_tier_length_mass_eligible"
    )
    return header + "\n" + "\t".join(values) + "\n"


def _resolve_uniqueness_score(
    *,
    uniqueness_class: PeptideUniquenessClass | None,
    uniqueness_score: float | None,
) -> float:
    if uniqueness_score is not None:
        return _bounded_score(uniqueness_score)
    if uniqueness_class is None:
        return 0.5
    return {
        PeptideUniquenessClass.UNIQUE: 1.0,
        PeptideUniquenessClass.ISOFORM_SHARED: 0.75,
        PeptideUniquenessClass.FAMILY_SHARED: 0.6,
        PeptideUniquenessClass.SHARED: 0.45,
        PeptideUniquenessClass.CONTAMINANT: 0.1,
        PeptideUniquenessClass.DECOY: 0.1,
        PeptideUniquenessClass.MIXED: 0.1,
    }[uniqueness_class]


def _observed_evidence_score(observed_psm_count: int | None) -> float:
    if observed_psm_count is None:
        return 0.5
    if observed_psm_count == 0:
        return 0.0
    return _bounded_score(observed_psm_count / 5.0)


def _chargeability_score(*, sequence: str, charge: int) -> float:
    basic_site_count = 1 + sum(1 for residue in sequence if residue in {"K", "R", "H"})
    if charge > basic_site_count:
        return 0.25
    if charge in {2, 3}:
        return 1.0
    if charge in {1, 4}:
        return 0.7
    return 0.45


def _length_score(length: int) -> float:
    if _TOP_TIER_MIN_LENGTH <= length <= _TOP_TIER_MAX_LENGTH:
        return 1.0
    if 5 <= length < _TOP_TIER_MIN_LENGTH:
        return 0.45
    if _TOP_TIER_MAX_LENGTH < length <= 35:
        return 0.55
    return 0.15


def _mass_score(monoisotopic_mass: float) -> float:
    if (
        _TOP_TIER_MIN_MONOISOTOPIC_MASS
        <= monoisotopic_mass
        <= _TOP_TIER_MAX_MONOISOTOPIC_MASS
    ):
        return 1.0
    if 550.0 <= monoisotopic_mass < _TOP_TIER_MIN_MONOISOTOPIC_MASS:
        return 0.45
    if _TOP_TIER_MAX_MONOISOTOPIC_MASS < monoisotopic_mass <= 4000.0:
        return 0.55
    return 0.15


def _hydrophobicity_score(hydrophobicity_proxy: float) -> float:
    if -1.5 <= hydrophobicity_proxy <= 1.5:
        return 1.0
    if -2.5 <= hydrophobicity_proxy < -1.5 or 1.5 < hydrophobicity_proxy <= 2.5:
        return 0.65
    return 0.35


def _missed_cleavage_score(missed_cleavages: int) -> float:
    if missed_cleavages == 0:
        return 1.0
    if missed_cleavages == 1:
        return 0.75
    if missed_cleavages == 2:
        return 0.45
    return 0.15


def _problematic_residues(sequence: str) -> tuple[str, ...]:
    return tuple(residue for residue in sequence if residue in _PROBLEMATIC_RESIDUES)


def _problematic_residue_score(problematic_residue_count: int) -> float:
    return _bounded_score(1.0 - (problematic_residue_count * 0.15))


def _top_tier_length_mass_eligible(*, length: int, monoisotopic_mass: float) -> bool:
    return (
        _TOP_TIER_MIN_LENGTH <= length <= _TOP_TIER_MAX_LENGTH
        and _TOP_TIER_MIN_MONOISOTOPIC_MASS
        <= monoisotopic_mass
        <= _TOP_TIER_MAX_MONOISOTOPIC_MASS
    )


def _detectability_tier(
    *,
    detectability_score: float,
    top_tier_length_mass_eligible: bool,
    chargeability_score: float,
    resolved_uniqueness_score: float,
) -> PeptideDetectabilityTier:
    if (
        detectability_score >= 0.78
        and top_tier_length_mass_eligible
        and chargeability_score >= 0.7
        and resolved_uniqueness_score >= 0.45
    ):
        return PeptideDetectabilityTier.HIGH
    if detectability_score >= 0.5:
        return PeptideDetectabilityTier.MEDIUM
    return PeptideDetectabilityTier.LOW


def _bounded_score(value: float) -> float:
    if isclose(value, 0.0, rel_tol=0.0, abs_tol=1e-12):
        return 0.0
    if isclose(value, 1.0, rel_tol=0.0, abs_tol=1e-12):
        return 1.0
    return max(0.0, min(1.0, value))
