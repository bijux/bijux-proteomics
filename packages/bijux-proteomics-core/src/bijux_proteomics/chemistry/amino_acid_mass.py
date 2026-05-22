# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Amino-acid mass calculations for unmodified peptide composition."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel

_MONOISOTOPIC_RESIDUE_MASS: dict[str, float] = {
    "A": 71.03711,
    "R": 156.10111,
    "N": 114.04293,
    "D": 115.02694,
    "C": 103.00919,
    "E": 129.04259,
    "Q": 128.05858,
    "G": 57.02146,
    "H": 137.05891,
    "I": 113.08406,
    "L": 113.08406,
    "K": 128.09496,
    "M": 131.04049,
    "F": 147.06841,
    "P": 97.05276,
    "S": 87.03203,
    "T": 101.04768,
    "W": 186.07931,
    "Y": 163.06333,
    "V": 99.06841,
}

_AVERAGE_RESIDUE_MASS: dict[str, float] = {
    "A": 71.0788,
    "R": 156.1875,
    "N": 114.1038,
    "D": 115.0886,
    "C": 103.1388,
    "E": 129.1155,
    "Q": 128.1307,
    "G": 57.0519,
    "H": 137.1411,
    "I": 113.1594,
    "L": 113.1594,
    "K": 128.1741,
    "M": 131.1926,
    "F": 147.1766,
    "P": 97.1167,
    "S": 87.0782,
    "T": 101.1051,
    "W": 186.2132,
    "Y": 163.176,
    "V": 99.1326,
}

_CANONICAL_RESIDUES = frozenset(_MONOISOTOPIC_RESIDUE_MASS)
_PROTON_MONOISOTOPIC_MASS = 1.007276466812
_PROTON_AVERAGE_MASS = 1.007276466812
_FREE_N_TERM_MONOISOTOPIC_MASS = 1.00782503223
_FREE_N_TERM_AVERAGE_MASS = 1.00794
_FREE_C_TERM_MONOISOTOPIC_MASS = 17.00273496777
_FREE_C_TERM_AVERAGE_MASS = 17.00734
_WATER_MONOISOTOPIC_MASS = (
    _FREE_N_TERM_MONOISOTOPIC_MASS + _FREE_C_TERM_MONOISOTOPIC_MASS
)
_WATER_AVERAGE_MASS = _FREE_N_TERM_AVERAGE_MASS + _FREE_C_TERM_AVERAGE_MASS

__all__ = [
    "AminoAcidMass",
    "PeptideMassReport",
    "PeptideTermini",
    "ResidueMassContribution",
    "amino_acid_masses",
    "build_peptide_mass_report",
    "calculate_sequence_average_mass",
    "calculate_sequence_monoisotopic_mass",
    "calculate_sequence_mz",
    "free_peptide_termini",
    "render_peptide_mass_contributions_tsv",
]


class AminoAcidMass(JsonModel):
    """One canonical residue mass entry."""

    model_config = ConfigDict(extra="forbid")

    residue: str = Field(..., min_length=1, max_length=1)
    monoisotopic_mass: float = Field(..., gt=0.0)
    average_mass: float = Field(..., gt=0.0)


class PeptideTermini(JsonModel):
    """Explicit terminal mass contributions for one peptide."""

    model_config = ConfigDict(extra="forbid")

    n_term_label: str = Field(default="free_n_term", min_length=1)
    c_term_label: str = Field(default="free_c_term", min_length=1)
    n_term_monoisotopic_mass: float = Field(
        default=_FREE_N_TERM_MONOISOTOPIC_MASS, ge=0.0
    )
    n_term_average_mass: float = Field(default=_FREE_N_TERM_AVERAGE_MASS, ge=0.0)
    c_term_monoisotopic_mass: float = Field(
        default=_FREE_C_TERM_MONOISOTOPIC_MASS, ge=0.0
    )
    c_term_average_mass: float = Field(default=_FREE_C_TERM_AVERAGE_MASS, ge=0.0)


class ResidueMassContribution(JsonModel):
    """One residue contribution inside a peptide mass calculation."""

    model_config = ConfigDict(extra="forbid")

    position: int = Field(..., ge=1)
    residue: str = Field(..., min_length=1, max_length=1)
    monoisotopic_mass: float = Field(..., gt=0.0)
    average_mass: float = Field(..., gt=0.0)


class PeptideMassReport(JsonModel):
    """Deterministic mass report for one unmodified peptide."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    termini: PeptideTermini
    residue_contributions: tuple[ResidueMassContribution, ...] = Field(
        default_factory=tuple
    )
    neutral_monoisotopic_mass: float = Field(..., gt=0.0)
    neutral_average_mass: float = Field(..., gt=0.0)
    mz_monoisotopic: float = Field(..., gt=0.0)
    mz_average: float = Field(..., gt=0.0)


def amino_acid_masses() -> tuple[AminoAcidMass, ...]:
    """Return the canonical residue mass table in residue order."""
    return tuple(
        AminoAcidMass(
            residue=residue,
            monoisotopic_mass=_MONOISOTOPIC_RESIDUE_MASS[residue],
            average_mass=_AVERAGE_RESIDUE_MASS[residue],
        )
        for residue in sorted(_CANONICAL_RESIDUES)
    )


def free_peptide_termini() -> PeptideTermini:
    """Return the default free peptide termini."""
    return PeptideTermini()


def calculate_sequence_monoisotopic_mass(
    sequence: str,
    *,
    termini: PeptideTermini | None = None,
) -> float:
    """Calculate the monoisotopic neutral mass for one unmodified peptide."""
    normalized = _normalize_sequence(sequence)
    resolved_termini = termini or free_peptide_termini()
    return (
        resolved_termini.n_term_monoisotopic_mass
        + resolved_termini.c_term_monoisotopic_mass
        + sum(_MONOISOTOPIC_RESIDUE_MASS[residue] for residue in normalized)
    )


def calculate_sequence_average_mass(
    sequence: str,
    *,
    termini: PeptideTermini | None = None,
) -> float:
    """Calculate the average neutral mass for one unmodified peptide."""
    normalized = _normalize_sequence(sequence)
    resolved_termini = termini or free_peptide_termini()
    return (
        resolved_termini.n_term_average_mass
        + resolved_termini.c_term_average_mass
        + sum(_AVERAGE_RESIDUE_MASS[residue] for residue in normalized)
    )


def calculate_sequence_mz(
    sequence: str,
    *,
    charge: int,
    termini: PeptideTermini | None = None,
    use_average_mass: bool = False,
) -> float:
    """Calculate precursor m/z for one unmodified peptide sequence."""
    if charge < 1:
        raise ValueError("charge must be at least 1")
    neutral_mass = (
        calculate_sequence_average_mass(sequence, termini=termini)
        if use_average_mass
        else calculate_sequence_monoisotopic_mass(sequence, termini=termini)
    )
    proton_mass = (
        _PROTON_AVERAGE_MASS if use_average_mass else _PROTON_MONOISOTOPIC_MASS
    )
    return (neutral_mass + (charge * proton_mass)) / charge


def build_peptide_mass_report(
    sequence: str,
    *,
    charge: int,
    termini: PeptideTermini | None = None,
) -> PeptideMassReport:
    """Build the full mass report for one unmodified peptide."""
    normalized = _normalize_sequence(sequence)
    resolved_termini = termini or free_peptide_termini()
    residue_contributions = tuple(
        ResidueMassContribution(
            position=index,
            residue=residue,
            monoisotopic_mass=_MONOISOTOPIC_RESIDUE_MASS[residue],
            average_mass=_AVERAGE_RESIDUE_MASS[residue],
        )
        for index, residue in enumerate(normalized, start=1)
    )
    return PeptideMassReport(
        sequence=normalized,
        charge=charge,
        termini=resolved_termini,
        residue_contributions=residue_contributions,
        neutral_monoisotopic_mass=calculate_sequence_monoisotopic_mass(
            normalized,
            termini=resolved_termini,
        ),
        neutral_average_mass=calculate_sequence_average_mass(
            normalized,
            termini=resolved_termini,
        ),
        mz_monoisotopic=calculate_sequence_mz(
            normalized,
            charge=charge,
            termini=resolved_termini,
        ),
        mz_average=calculate_sequence_mz(
            normalized,
            charge=charge,
            termini=resolved_termini,
            use_average_mass=True,
        ),
    )


def render_peptide_mass_contributions_tsv(report: PeptideMassReport) -> str:
    """Render the residue contribution table for one peptide mass report."""
    lines = ["position\tresidue\tmonoisotopic_mass\taverage_mass"]
    for contribution in report.residue_contributions:
        lines.append(
            "\t".join(
                (
                    str(contribution.position),
                    contribution.residue,
                    f"{contribution.monoisotopic_mass:.5f}",
                    f"{contribution.average_mass:.5f}",
                )
            )
        )
    return "\n".join(lines)


def _normalize_sequence(sequence: str) -> str:
    normalized = sequence.strip().upper()
    if not normalized:
        raise ValueError("peptide sequence cannot be empty")
    invalid_residues = [
        residue for residue in normalized if residue not in _CANONICAL_RESIDUES
    ]
    if invalid_residues:
        invalid_list = ", ".join(sorted(set(invalid_residues)))
        raise ValueError(
            "peptide sequence must use canonical uppercase amino-acid symbols: "
            f"{invalid_list}"
        )
    return normalized
