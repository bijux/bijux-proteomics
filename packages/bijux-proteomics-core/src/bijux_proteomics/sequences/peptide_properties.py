# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Peptide property calculations for review and filtering."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.mass import (
    calculate_average_peptide_mass,
    calculate_monoisotopic_peptide_mass,
    calculate_peptide_mz,
)
from bijux_proteomics.chemistry.modifications import (
    ModificationRegistryDocument,
    build_modified_peptide,
    canonicalize_modified_peptide,
)
from bijux_proteomics.sequences.digestion import (
    ProteaseRule,
    count_missed_cleavages,
    resolve_protease_rule,
)
from bijux_proteomics_foundation import JsonModel

_KYTE_DOOLITTLE_HYDROPHOBICITY = {
    "A": 1.8,
    "C": 2.5,
    "D": -3.5,
    "E": -3.5,
    "F": 2.8,
    "G": -0.4,
    "H": -3.2,
    "I": 4.5,
    "K": -3.9,
    "L": 3.8,
    "M": 1.9,
    "N": -3.5,
    "P": -1.6,
    "Q": -3.5,
    "R": -4.5,
    "S": -0.8,
    "T": -0.7,
    "V": 4.2,
    "W": -0.9,
    "Y": -1.3,
}
_SHORT_PEPTIDE_LENGTH = 7
_LONG_PEPTIDE_LENGTH = 40
_HIGH_MISSED_CLEAVAGE_COUNT = 2
_HIGH_HYDROPHOBICITY_PROXY = 1.5


class PeptideProblemFlag(StrEnum):
    """Heuristic peptide issues worth reviewer attention."""

    SHORT_LENGTH = "short_length"
    LONG_LENGTH = "long_length"
    HIGH_MISSED_CLEAVAGES = "high_missed_cleavages"
    HIGH_HYDROPHOBICITY_PROXY = "high_hydrophobicity_proxy"


class PeptidePropertyReport(JsonModel):
    """One peptide property report for search-space review."""

    model_config = ConfigDict(extra="forbid")

    canonical_notation: str = Field(..., min_length=1)
    residue_sequence: str = Field(..., min_length=1)
    protease: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    length: int = Field(..., ge=1)
    monoisotopic_mass: float = Field(..., gt=0.0)
    average_mass: float = Field(..., gt=0.0)
    mz_monoisotopic: float = Field(..., gt=0.0)
    missed_cleavages: int = Field(..., ge=0)
    hydrophobicity_proxy: float
    problem_flags: tuple[PeptideProblemFlag, ...] = Field(default_factory=tuple)
    flagged_problematic: bool = False


def calculate_peptide_hydrophobicity_proxy(sequence: str) -> float:
    """Return the average Kyte-Doolittle hydrophobicity for one peptide."""
    residues = sequence.strip().upper()
    if not residues:
        raise ValueError("peptide sequence cannot be empty")
    try:
        return sum(_KYTE_DOOLITTLE_HYDROPHOBICITY[aa] for aa in residues) / len(
            residues
        )
    except KeyError as exc:
        raise ValueError(
            f"hydrophobicity proxy requires standard amino acids, got {exc.args[0]!r}"
        ) from exc


def build_peptide_property_report(
    sequence: str,
    *,
    modification_assignments: tuple[str, ...] = (),
    charge: int = 2,
    protease: ProteaseRule | str = "trypsin",
    registry: ModificationRegistryDocument | None = None,
) -> PeptidePropertyReport:
    """Build a peptide property report for filtering and review."""
    parsed = build_modified_peptide(
        sequence,
        assignments=modification_assignments,
        registry=registry,
    )
    protease_rule = (
        resolve_protease_rule(protease) if isinstance(protease, str) else protease
    )
    hydrophobicity_proxy = calculate_peptide_hydrophobicity_proxy(parsed.sequence)
    missed_cleavages = count_missed_cleavages(parsed.sequence, protease_rule)
    problem_flags = _build_problem_flags(
        sequence=parsed.sequence,
        hydrophobicity_proxy=hydrophobicity_proxy,
        missed_cleavages=missed_cleavages,
    )
    return PeptidePropertyReport(
        canonical_notation=canonicalize_modified_peptide(parsed, registry=registry),
        residue_sequence=parsed.sequence,
        protease=protease_rule.name,
        charge=charge,
        length=len(parsed.sequence),
        monoisotopic_mass=calculate_monoisotopic_peptide_mass(
            parsed, registry=registry
        ),
        average_mass=calculate_average_peptide_mass(parsed, registry=registry),
        mz_monoisotopic=calculate_peptide_mz(parsed, charge=charge, registry=registry),
        missed_cleavages=missed_cleavages,
        hydrophobicity_proxy=hydrophobicity_proxy,
        problem_flags=problem_flags,
        flagged_problematic=bool(problem_flags),
    )


def _build_problem_flags(
    *,
    sequence: str,
    hydrophobicity_proxy: float,
    missed_cleavages: int,
) -> tuple[PeptideProblemFlag, ...]:
    flags: list[PeptideProblemFlag] = []
    if len(sequence) < _SHORT_PEPTIDE_LENGTH:
        flags.append(PeptideProblemFlag.SHORT_LENGTH)
    if len(sequence) > _LONG_PEPTIDE_LENGTH:
        flags.append(PeptideProblemFlag.LONG_LENGTH)
    if missed_cleavages >= _HIGH_MISSED_CLEAVAGE_COUNT:
        flags.append(PeptideProblemFlag.HIGH_MISSED_CLEAVAGES)
    if hydrophobicity_proxy >= _HIGH_HYDROPHOBICITY_PROXY:
        flags.append(PeptideProblemFlag.HIGH_HYDROPHOBICITY_PROXY)
    return tuple(flags)
