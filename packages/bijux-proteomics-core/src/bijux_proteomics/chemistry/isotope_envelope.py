# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Elemental-composition peptide isotope envelope prediction."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.amino_acid_mass import _PROTON_MONOISOTOPIC_MASS
from bijux_proteomics.chemistry.contracts import (
    AppliedModification,
    ModificationRegistryDocument,
    ParsedModifiedPeptide,
    build_modified_peptide,
)
from bijux_proteomics.chemistry.modification_registry import (
    resolve_modification_definition,
)
from bijux_proteomics_foundation import JsonModel

_C13_NEUTRON_SHIFT = 1.0033548378
_SUPPORTED_ELEMENT_SYMBOLS = ("C", "H", "N", "O", "S", "P")
_PEPTIDE_TERMINI_COMPOSITION = {"H": 2, "O": 1}
_RESIDUE_ELEMENTAL_COMPOSITION: dict[str, dict[str, int]] = {
    "A": {"C": 3, "H": 5, "N": 1, "O": 1},
    "R": {"C": 6, "H": 12, "N": 4, "O": 1},
    "N": {"C": 4, "H": 6, "N": 2, "O": 2},
    "D": {"C": 4, "H": 5, "N": 1, "O": 3},
    "C": {"C": 3, "H": 5, "N": 1, "O": 1, "S": 1},
    "E": {"C": 5, "H": 7, "N": 1, "O": 3},
    "Q": {"C": 5, "H": 8, "N": 2, "O": 2},
    "G": {"C": 2, "H": 3, "N": 1, "O": 1},
    "H": {"C": 6, "H": 7, "N": 3, "O": 1},
    "I": {"C": 6, "H": 11, "N": 1, "O": 1},
    "L": {"C": 6, "H": 11, "N": 1, "O": 1},
    "K": {"C": 6, "H": 12, "N": 2, "O": 1},
    "M": {"C": 5, "H": 9, "N": 1, "O": 1, "S": 1},
    "F": {"C": 9, "H": 9, "N": 1, "O": 1},
    "P": {"C": 5, "H": 7, "N": 1, "O": 1},
    "S": {"C": 3, "H": 5, "N": 1, "O": 2},
    "T": {"C": 4, "H": 7, "N": 1, "O": 2},
    "W": {"C": 11, "H": 10, "N": 2, "O": 1},
    "Y": {"C": 9, "H": 9, "N": 1, "O": 2},
    "V": {"C": 5, "H": 9, "N": 1, "O": 1},
}
_MONOISOTOPIC_ATOMIC_MASS = {
    "C": 12.0,
    "H": 1.00782503223,
    "N": 14.00307400443,
    "O": 15.99491461957,
    "S": 31.9720711744,
    "P": 30.97376199842,
}
_NATURAL_ABUNDANCE_OFFSETS = {
    "C": ((0, 0.9893), (1, 0.0107)),
    "H": ((0, 0.999885), (1, 0.000115)),
    "N": ((0, 0.99632), (1, 0.00368)),
    "O": ((0, 0.99757), (1, 0.00038), (2, 0.00205)),
    "S": ((0, 0.9499), (1, 0.0075), (2, 0.0425), (4, 0.0001)),
    "P": ((0, 1.0),),
}

__all__ = [
    "ElementalComposition",
    "IsotopeEnvelopePeakPrediction",
    "PeptideIsotopeEnvelopePrediction",
    "build_peptide_elemental_composition",
    "predict_peptide_isotope_envelope",
    "predict_peptide_isotope_envelopes",
    "render_isotope_envelopes_tsv",
]


class ElementalComposition(JsonModel):
    """Canonical elemental composition for one peptide."""

    model_config = ConfigDict(extra="forbid")

    carbon: int = Field(default=0, ge=0)
    hydrogen: int = Field(default=0, ge=0)
    nitrogen: int = Field(default=0, ge=0)
    oxygen: int = Field(default=0, ge=0)
    sulfur: int = Field(default=0, ge=0)
    phosphorus: int = Field(default=0, ge=0)
    formula: str = Field(..., min_length=1)


class IsotopeEnvelopePeakPrediction(JsonModel):
    """One predicted isotope peak."""

    model_config = ConfigDict(extra="forbid")

    isotope_index: int = Field(..., ge=0)
    probability: float = Field(..., ge=0.0, le=1.0)
    mz: float = Field(..., gt=0.0)


class PeptideIsotopeEnvelopePrediction(JsonModel):
    """One peptide isotope envelope derived from elemental composition."""

    model_config = ConfigDict(extra="forbid")

    canonical_notation: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    composition: ElementalComposition
    max_isotope_index: int = Field(..., ge=0)
    neutral_monoisotopic_mass: float = Field(..., gt=0.0)
    monoisotopic_mz: float = Field(..., gt=0.0)
    peaks: tuple[IsotopeEnvelopePeakPrediction, ...] = Field(default_factory=tuple)


def build_peptide_elemental_composition(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> ElementalComposition:
    """Build elemental composition for one peptide under natural abundance."""
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    counts = {symbol: 0 for symbol in _SUPPORTED_ELEMENT_SYMBOLS}
    _apply_delta(counts, _PEPTIDE_TERMINI_COMPOSITION)
    for residue in parsed.sequence:
        _apply_delta(counts, _RESIDUE_ELEMENTAL_COMPOSITION[residue])
    for modification in parsed.modifications:
        _apply_delta(
            counts,
            _resolve_modification_elemental_delta(
                modification,
                peptide=parsed,
                registry=registry,
            ),
        )
    for symbol, count in counts.items():
        if count < 0:
            raise ValueError(
                f"elemental composition count for {symbol} became negative after modification application"
            )
    return ElementalComposition(
        carbon=counts["C"],
        hydrogen=counts["H"],
        nitrogen=counts["N"],
        oxygen=counts["O"],
        sulfur=counts["S"],
        phosphorus=counts["P"],
        formula=_format_formula(counts),
    )


def predict_peptide_isotope_envelope(
    peptide: str | ParsedModifiedPeptide,
    *,
    charge: int,
    max_isotope_index: int = 5,
    registry: ModificationRegistryDocument | None = None,
) -> PeptideIsotopeEnvelopePrediction:
    """Predict M+0 through M+n isotope probabilities from elemental composition."""
    if charge < 1:
        raise ValueError("charge must be at least 1")
    if max_isotope_index < 0:
        raise ValueError("max_isotope_index cannot be negative")
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    composition = build_peptide_elemental_composition(parsed, registry=registry)
    counts = _composition_counts(composition)
    neutral_mass = sum(
        counts[symbol] * _MONOISOTOPIC_ATOMIC_MASS[symbol]
        for symbol in _SUPPORTED_ELEMENT_SYMBOLS
    )
    monoisotopic_mz = (neutral_mass + (charge * _PROTON_MONOISOTOPIC_MASS)) / charge
    offset_distribution = [1.0] + [0.0] * max_isotope_index
    for symbol in _SUPPORTED_ELEMENT_SYMBOLS:
        atom_count = counts[symbol]
        if atom_count == 0:
            continue
        element_distribution = _distribution_power(
            _base_element_distribution(symbol, max_isotope_index),
            atom_count,
            max_isotope_index,
        )
        offset_distribution = _multiply_distributions(
            offset_distribution,
            element_distribution,
            max_isotope_index,
        )
    total_probability = sum(offset_distribution)
    if total_probability <= 0.0:
        raise ValueError("isotope distribution collapsed to zero probability")
    peaks = tuple(
        IsotopeEnvelopePeakPrediction(
            isotope_index=index,
            probability=probability / total_probability,
            mz=monoisotopic_mz + ((_C13_NEUTRON_SHIFT * index) / charge),
        )
        for index, probability in enumerate(offset_distribution)
    )
    return PeptideIsotopeEnvelopePrediction(
        canonical_notation=parsed.canonical_notation,
        charge=charge,
        composition=composition,
        max_isotope_index=max_isotope_index,
        neutral_monoisotopic_mass=neutral_mass,
        monoisotopic_mz=monoisotopic_mz,
        peaks=peaks,
    )


def predict_peptide_isotope_envelopes(
    peptide: str | ParsedModifiedPeptide,
    *,
    charges: Sequence[int],
    max_isotope_index: int = 5,
    registry: ModificationRegistryDocument | None = None,
) -> tuple[PeptideIsotopeEnvelopePrediction, ...]:
    """Predict isotope envelopes for one peptide across multiple charges."""
    return tuple(
        predict_peptide_isotope_envelope(
            peptide,
            charge=charge,
            max_isotope_index=max_isotope_index,
            registry=registry,
        )
        for charge in charges
    )


def render_isotope_envelopes_tsv(
    envelopes: Sequence[PeptideIsotopeEnvelopePrediction],
) -> str:
    """Render stable TSV rows for one or more predicted isotope envelopes."""
    lines = [
        "canonical_notation\tcharge\tformula\tisotope_index\tmz\tprobability"
    ]
    for envelope in envelopes:
        for peak in envelope.peaks:
            lines.append(
                "\t".join(
                    (
                        envelope.canonical_notation,
                        str(envelope.charge),
                        envelope.composition.formula,
                        str(peak.isotope_index),
                        f"{peak.mz:.12f}",
                        f"{peak.probability:.12f}",
                    )
                )
            )
    return "\n".join(lines) + "\n"


def _ensure_parsed_peptide(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None,
) -> ParsedModifiedPeptide:
    if isinstance(peptide, ParsedModifiedPeptide):
        return peptide
    return build_modified_peptide(peptide, registry=registry)


def _resolve_modification_elemental_delta(
    modification: AppliedModification,
    *,
    peptide: ParsedModifiedPeptide,
    registry: ModificationRegistryDocument | None,
) -> dict[str, int]:
    definition = resolve_modification_definition(
        token=modification.name,
        controlled_id=modification.controlled_id,
        site=modification.site,
        residue=modification.residue,
        at_protein_n_term=peptide.at_protein_n_term,
        at_protein_c_term=peptide.at_protein_c_term,
        registry=registry,
    )
    if definition.isotopic_label_family is not None:
        raise ValueError(
            f"isotope envelope prediction does not support explicit isotope-label modification {definition.name!r}"
        )
    if not definition.elemental_composition_delta:
        raise ValueError(
            f"modification {definition.name!r} does not declare an elemental composition delta"
        )
    return definition.elemental_composition_delta


def _apply_delta(counts: dict[str, int], delta: dict[str, int]) -> None:
    for symbol, value in delta.items():
        counts[symbol] = counts.get(symbol, 0) + value


def _composition_counts(composition: ElementalComposition) -> dict[str, int]:
    return {
        "C": composition.carbon,
        "H": composition.hydrogen,
        "N": composition.nitrogen,
        "O": composition.oxygen,
        "S": composition.sulfur,
        "P": composition.phosphorus,
    }


def _format_formula(counts: dict[str, int]) -> str:
    symbols = []
    for symbol in _SUPPORTED_ELEMENT_SYMBOLS:
        count = counts[symbol]
        if count == 0:
            continue
        symbols.append(f"{symbol}{count}")
    if not symbols:
        raise ValueError("elemental composition formula cannot be empty")
    return "".join(symbols)


def _base_element_distribution(
    symbol: str,
    max_isotope_index: int,
) -> tuple[float, ...]:
    distribution = [0.0] * (max_isotope_index + 1)
    for isotope_offset, abundance in _NATURAL_ABUNDANCE_OFFSETS[symbol]:
        if isotope_offset > max_isotope_index:
            continue
        distribution[isotope_offset] += abundance
    return tuple(distribution)


def _distribution_power(
    base: tuple[float, ...],
    exponent: int,
    max_isotope_index: int,
) -> list[float]:
    result = [1.0] + [0.0] * max_isotope_index
    factor = list(base)
    power = exponent
    while power > 0:
        if power % 2 == 1:
            result = _multiply_distributions(result, factor, max_isotope_index)
        power //= 2
        if power:
            factor = _multiply_distributions(factor, factor, max_isotope_index)
    return result


def _multiply_distributions(
    left: Sequence[float],
    right: Sequence[float],
    max_isotope_index: int,
) -> list[float]:
    product = [0.0] * (max_isotope_index + 1)
    for left_index, left_probability in enumerate(left):
        if left_probability == 0.0:
            continue
        for right_index, right_probability in enumerate(right):
            if right_probability == 0.0:
                continue
            offset = left_index + right_index
            if offset > max_isotope_index:
                continue
            product[offset] += left_probability * right_probability
    return product
