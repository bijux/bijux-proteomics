# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Peptide mass, charge-state, and isotope-envelope projections."""

from __future__ import annotations

from bijux_proteomics.chemistry.amino_acid_mass import (
    _PROTON_AVERAGE_MASS,
    _PROTON_MONOISOTOPIC_MASS,
    calculate_sequence_average_mass,
    calculate_sequence_monoisotopic_mass,
)
from bijux_proteomics.chemistry.contracts.models import (
    AppliedModification,
    IsotopeEnvelopeStatus,
    IsotopePeak,
    MassType,
    ModificationPosition,
    ModificationRegistryDocument,
    ParsedModifiedPeptide,
    PeptideChargeState,
    PeptideIsotopeEnvelope,
    StaticModification,
)
from bijux_proteomics.chemistry.contracts.modified_peptides import (
    _ensure_parsed_peptide,
    canonicalize_modified_peptide,
)


def _mass_delta_for(
    mass_type: MassType,
    *,
    mono: float,
    average: float,
) -> float:
    return mono if mass_type is MassType.MONOISOTOPIC else average


def _matching_static_mass_delta(
    sequence: str,
    static_modifications: tuple[StaticModification, ...],
    mass_type: MassType,
    *,
    start: int = 1,
    end: int | None = None,
    include_n_term: bool = True,
    include_c_term: bool = True,
) -> float:
    finish = len(sequence) if end is None else end
    total = 0.0
    for modification in static_modifications:
        delta = _mass_delta_for(
            mass_type,
            mono=modification.mass_delta_monoisotopic,
            average=modification.mass_delta_average,
        )
        if modification.position is ModificationPosition.ANYWHERE:
            for residue in sequence[start - 1 : finish]:
                if residue in modification.residues:
                    total += delta
        elif (
            (
                modification.position is ModificationPosition.PEPTIDE_N_TERM
                or modification.position is ModificationPosition.PROTEIN_N_TERM
            )
            and include_n_term
            or (
                modification.position is ModificationPosition.PEPTIDE_C_TERM
                or modification.position is ModificationPosition.PROTEIN_C_TERM
            )
            and include_c_term
        ):
            total += delta
    return total


def _applied_modification_mass_delta(
    modifications: tuple[AppliedModification, ...],
    mass_type: MassType,
    *,
    start: int = 1,
    end: int | None = None,
    include_n_term: bool = True,
    include_c_term: bool = True,
) -> float:
    total = 0.0
    finish = end
    for modification in modifications:
        delta = _mass_delta_for(
            mass_type,
            mono=modification.mass_delta_monoisotopic,
            average=modification.mass_delta_average,
        )
        if modification.site is ModificationPosition.ANYWHERE:
            site_index = modification.site_index
            if site_index is None:
                raise ValueError(
                    "residue modification is missing a required site index"
                )
            if site_index >= start and (finish is None or site_index <= finish):
                total += delta
        elif (
            (
                modification.site is ModificationPosition.PEPTIDE_N_TERM
                or modification.site is ModificationPosition.PROTEIN_N_TERM
            )
            and include_n_term
            or (
                modification.site is ModificationPosition.PEPTIDE_C_TERM
                or modification.site is ModificationPosition.PROTEIN_C_TERM
            )
            and include_c_term
        ):
            total += delta
    return total


def calculate_monoisotopic_peptide_mass(
    peptide: str | ParsedModifiedPeptide,
    *,
    static_modifications: tuple[StaticModification, ...] = (),
    registry: ModificationRegistryDocument | None = None,
) -> float:
    """Calculate the monoisotopic neutral mass for one peptide."""
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    return (
        calculate_sequence_monoisotopic_mass(parsed.sequence)
        + _matching_static_mass_delta(
            parsed.sequence,
            static_modifications,
            MassType.MONOISOTOPIC,
        )
        + _applied_modification_mass_delta(parsed.modifications, MassType.MONOISOTOPIC)
    )


def calculate_average_peptide_mass(
    peptide: str | ParsedModifiedPeptide,
    *,
    static_modifications: tuple[StaticModification, ...] = (),
    registry: ModificationRegistryDocument | None = None,
) -> float:
    """Calculate the average neutral mass for one peptide."""
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    return (
        calculate_sequence_average_mass(parsed.sequence)
        + _matching_static_mass_delta(
            parsed.sequence,
            static_modifications,
            MassType.AVERAGE,
        )
        + _applied_modification_mass_delta(parsed.modifications, MassType.AVERAGE)
    )


def calculate_peptide_mz(
    peptide: str | ParsedModifiedPeptide,
    *,
    charge: int,
    mass_type: MassType = MassType.MONOISOTOPIC,
    static_modifications: tuple[StaticModification, ...] = (),
    registry: ModificationRegistryDocument | None = None,
) -> float:
    """Calculate peptide precursor m/z for one charge state."""
    if charge < 1:
        raise ValueError("charge must be at least 1")
    neutral_mass = (
        calculate_monoisotopic_peptide_mass(
            peptide,
            static_modifications=static_modifications,
            registry=registry,
        )
        if mass_type is MassType.MONOISOTOPIC
        else calculate_average_peptide_mass(
            peptide,
            static_modifications=static_modifications,
            registry=registry,
        )
    )
    proton_mass = (
        _PROTON_MONOISOTOPIC_MASS
        if mass_type is MassType.MONOISOTOPIC
        else _PROTON_AVERAGE_MASS
    )
    return (neutral_mass + (charge * proton_mass)) / charge


def calculate_modified_peptide_mass(
    peptide: str | ParsedModifiedPeptide,
    *,
    mass_type: MassType = MassType.MONOISOTOPIC,
    static_modifications: tuple[StaticModification, ...] = (),
    registry: ModificationRegistryDocument | None = None,
) -> float:
    """Calculate modified peptide neutral mass in the selected mass space."""
    if mass_type is MassType.MONOISOTOPIC:
        return calculate_monoisotopic_peptide_mass(
            peptide,
            static_modifications=static_modifications,
            registry=registry,
        )
    return calculate_average_peptide_mass(
        peptide,
        static_modifications=static_modifications,
        registry=registry,
    )


def build_peptide_charge_state(
    peptide: str | ParsedModifiedPeptide,
    *,
    charge: int,
    mass_type: MassType = MassType.MONOISOTOPIC,
    static_modifications: tuple[StaticModification, ...] = (),
    registry: ModificationRegistryDocument | None = None,
) -> PeptideChargeState:
    """Build a typed charge-state view for one peptide."""
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    canonical = canonicalize_modified_peptide(parsed, registry=registry)
    neutral_mass = calculate_modified_peptide_mass(
        parsed,
        mass_type=mass_type,
        static_modifications=static_modifications,
        registry=registry,
    )
    mz = calculate_peptide_mz(
        parsed,
        charge=charge,
        mass_type=mass_type,
        static_modifications=static_modifications,
        registry=registry,
    )
    return PeptideChargeState(
        canonical_notation=canonical,
        charge=charge,
        mass_type=mass_type,
        neutral_mass=neutral_mass,
        mz=mz,
    )


def approximate_peptide_isotope_envelope(
    peptide: str | ParsedModifiedPeptide,
    *,
    charge: int,
    peak_count: int = 6,
    registry: ModificationRegistryDocument | None = None,
) -> PeptideIsotopeEnvelope:
    """Compatibility wrapper over the elemental-composition isotope owner."""
    if peak_count < 1:
        raise ValueError("peak_count must be at least 1")
    from bijux_proteomics.chemistry.isotope_envelope import (
        predict_peptide_isotope_envelope,
    )

    prediction = predict_peptide_isotope_envelope(
        peptide,
        charge=charge,
        max_isotope_index=peak_count - 1,
        registry=registry,
    )
    peaks = tuple(
        IsotopePeak(
            isotope_index=peak.isotope_index,
            intensity=peak.probability,
            mz=peak.mz,
        )
        for peak in prediction.peaks
    )
    return PeptideIsotopeEnvelope(
        status=IsotopeEnvelopeStatus.PREDICTED,
        canonical_notation=prediction.canonical_notation,
        charge=charge,
        estimated_carbon_count=float(prediction.composition.carbon),
        monoisotopic_mz=prediction.monoisotopic_mz,
        peaks=peaks,
    )


__all__ = [
    "approximate_peptide_isotope_envelope",
    "build_peptide_charge_state",
    "calculate_average_peptide_mass",
    "calculate_modified_peptide_mass",
    "calculate_monoisotopic_peptide_mass",
    "calculate_peptide_mz",
]
