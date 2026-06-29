# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Peptide chemistry and modification contracts."""

from __future__ import annotations

from bijux_proteomics.chemistry.amino_acid_mass import (
    _AVERAGE_RESIDUE_MASS,
    _MONOISOTOPIC_RESIDUE_MASS,
    _PROTON_AVERAGE_MASS,
    _PROTON_MONOISOTOPIC_MASS,
    _WATER_AVERAGE_MASS,
    _WATER_MONOISOTOPIC_MASS,
    calculate_sequence_average_mass,
    calculate_sequence_monoisotopic_mass,
)
from bijux_proteomics.chemistry.contracts.models import (
    AppliedModification,
    FragmentIon,
    FragmentIonSeries,
    FragmentIonShiftValidationEntry,
    FragmentIonShiftValidationReport,
    IsotopeEnvelopeStatus,
    IsotopePeak,
    IsotopicLabelingPolicy as IsotopicLabelingPolicy,
    MassType,
    ModificationLocalizationAdvisory as ModificationLocalizationAdvisory,
    ModificationLocalizationCandidate as ModificationLocalizationCandidate,
    ModificationLocalizationState as ModificationLocalizationState,
    ModificationLocalizationStatus as ModificationLocalizationStatus,
    ModificationPosition,
    ModificationProvenance as ModificationProvenance,
    ModificationRegistryDocument,
    ModificationRegistryValidationIssue as ModificationRegistryValidationIssue,
    ModificationRegistryValidationReport as ModificationRegistryValidationReport,
    ModificationSiteValidationIssue as ModificationSiteValidationIssue,
    ModificationSiteValidationReport as ModificationSiteValidationReport,
    ModifiedPeptideExportRecord as ModifiedPeptideExportRecord,
    NeutralLoss,
    ParsedModifiedPeptide,
    PeptideChargeState,
    PeptideIsotopeEnvelope,
    StaticModification,
    VariableModification as VariableModification,
    VariableModificationEnumerationEntry as VariableModificationEnumerationEntry,
    VariableModificationEnumerationReport as VariableModificationEnumerationReport,
)
from bijux_proteomics.chemistry.contracts.modified_peptides import (
    _ensure_parsed_peptide,
    build_modified_peptide as build_modified_peptide,
    build_modified_peptide_export_record as build_modified_peptide_export_record,
    build_modification_localization_advisory as build_modification_localization_advisory,
    canonicalize_modified_peptide as canonicalize_modified_peptide,
    enumerate_variable_modifications as enumerate_variable_modifications,
    export_modified_peptides_jsonl as export_modified_peptides_jsonl,
    export_modified_peptides_tsv as export_modified_peptides_tsv,
    parse_modified_peptide as parse_modified_peptide,
    validate_modified_peptide_sites as validate_modified_peptide_sites,
)
from bijux_proteomics.chemistry.contracts.registry_access import (
    build_modification_registry as build_modification_registry,
    get_modification as get_modification,
    load_modification_registry as load_modification_registry,
    modification_registry as modification_registry,
    validate_modification_registry as validate_modification_registry,
)

_AMMONIA_MONOISOTOPIC_MASS = 17.026549
_AMMONIA_AVERAGE_MASS = 17.03052
_PHOSPHORIC_ACID_MONOISOTOPIC_MASS = 97.976896
_PHOSPHORIC_ACID_AVERAGE_MASS = 97.9952
_CARBON_MONOISOTOPIC_MASS = 12.0
_CARBON_AVERAGE_MASS = 12.0107
_OXYGEN_MONOISOTOPIC_MASS = 15.99491461957
_OXYGEN_AVERAGE_MASS = 15.9994
_CARBON_MONOXIDE_MONOISOTOPIC_MASS = (
    _CARBON_MONOISOTOPIC_MASS + _OXYGEN_MONOISOTOPIC_MASS
)
_CARBON_MONOXIDE_AVERAGE_MASS = _CARBON_AVERAGE_MASS + _OXYGEN_AVERAGE_MASS
_C13_NEUTRON_SHIFT = 1.0033548378


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


def _residue_neutral_losses(fragment_sequence: str) -> tuple[NeutralLoss, ...]:
    losses: list[NeutralLoss] = []
    if any(residue in {"S", "T", "E", "D"} for residue in fragment_sequence):
        losses.append(
            NeutralLoss(
                name="water",
                monoisotopic_mass=_WATER_MONOISOTOPIC_MASS,
                average_mass=_WATER_AVERAGE_MASS,
            )
        )
    if any(residue in {"K", "Q", "R", "N"} for residue in fragment_sequence):
        losses.append(
            NeutralLoss(
                name="ammonia",
                monoisotopic_mass=_AMMONIA_MONOISOTOPIC_MASS,
                average_mass=_AMMONIA_AVERAGE_MASS,
            )
        )
    return tuple(losses)


def _fragment_modifications(
    peptide: ParsedModifiedPeptide,
    *,
    series: FragmentIonSeries,
    ordinal: int,
) -> tuple[AppliedModification, ...]:
    sequence_length = len(peptide.sequence)
    selected: list[AppliedModification] = []
    for modification in peptide.modifications:
        if (
            modification.site is ModificationPosition.PEPTIDE_N_TERM
            or modification.site is ModificationPosition.PROTEIN_N_TERM
        ):
            if series in {FragmentIonSeries.A, FragmentIonSeries.B}:
                selected.append(modification)
        elif (
            modification.site is ModificationPosition.PEPTIDE_C_TERM
            or modification.site is ModificationPosition.PROTEIN_C_TERM
        ):
            if series is FragmentIonSeries.Y:
                selected.append(modification)
        else:
            site_index = modification.site_index
            if site_index is None:
                raise ValueError(
                    "residue modification is missing a required site index"
                )
            if (
                series in {FragmentIonSeries.A, FragmentIonSeries.B}
                and site_index <= ordinal
            ):
                selected.append(modification)
            if series is FragmentIonSeries.Y and site_index > sequence_length - ordinal:
                selected.append(modification)
    return tuple(selected)


def calculate_fragment_ions(
    peptide: str | ParsedModifiedPeptide,
    *,
    charges: tuple[int, ...] = (1,),
    series: tuple[FragmentIonSeries, ...] = (FragmentIonSeries.B, FragmentIonSeries.Y),
    static_modifications: tuple[StaticModification, ...] = (),
    include_neutral_losses: bool = False,
    registry: ModificationRegistryDocument | None = None,
) -> tuple[FragmentIon, ...]:
    """Calculate theoretical a/b/y fragment ions for one peptide."""
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    if len(parsed.sequence) < 2:
        return ()
    invalid_charges = [charge for charge in charges if charge < 1]
    if invalid_charges:
        raise ValueError("fragment charges must all be at least 1")

    ions: list[FragmentIon] = []
    for fragment_series in series:
        for ordinal in range(1, len(parsed.sequence)):
            if fragment_series in {FragmentIonSeries.A, FragmentIonSeries.B}:
                fragment_sequence = parsed.sequence[:ordinal]
                span_start = 1
                span_end = ordinal
                mono_neutral = sum(
                    _MONOISOTOPIC_RESIDUE_MASS[residue] for residue in fragment_sequence
                )
                average_neutral = sum(
                    _AVERAGE_RESIDUE_MASS[residue] for residue in fragment_sequence
                )
                mono_neutral += _matching_static_mass_delta(
                    parsed.sequence,
                    static_modifications,
                    MassType.MONOISOTOPIC,
                    start=1,
                    end=ordinal,
                    include_n_term=True,
                    include_c_term=False,
                )
                average_neutral += _matching_static_mass_delta(
                    parsed.sequence,
                    static_modifications,
                    MassType.AVERAGE,
                    start=1,
                    end=ordinal,
                    include_n_term=True,
                    include_c_term=False,
                )
                if fragment_series is FragmentIonSeries.A:
                    mono_neutral -= _CARBON_MONOXIDE_MONOISOTOPIC_MASS
                    average_neutral -= _CARBON_MONOXIDE_AVERAGE_MASS
            else:
                fragment_sequence = parsed.sequence[-ordinal:]
                span_start = len(parsed.sequence) - ordinal + 1
                span_end = len(parsed.sequence)
                mono_neutral = _WATER_MONOISOTOPIC_MASS + sum(
                    _MONOISOTOPIC_RESIDUE_MASS[residue] for residue in fragment_sequence
                )
                average_neutral = _WATER_AVERAGE_MASS + sum(
                    _AVERAGE_RESIDUE_MASS[residue] for residue in fragment_sequence
                )
                mono_neutral += _matching_static_mass_delta(
                    parsed.sequence,
                    static_modifications,
                    MassType.MONOISOTOPIC,
                    start=span_start,
                    end=len(parsed.sequence),
                    include_n_term=False,
                    include_c_term=True,
                )
                average_neutral += _matching_static_mass_delta(
                    parsed.sequence,
                    static_modifications,
                    MassType.AVERAGE,
                    start=span_start,
                    end=len(parsed.sequence),
                    include_n_term=False,
                    include_c_term=True,
                )

            included_modifications = _fragment_modifications(
                parsed,
                series=fragment_series,
                ordinal=ordinal,
            )
            mono_neutral += _applied_modification_mass_delta(
                included_modifications,
                MassType.MONOISOTOPIC,
            )
            average_neutral += _applied_modification_mass_delta(
                included_modifications,
                MassType.AVERAGE,
            )

            neutral_losses = {}
            if include_neutral_losses:
                for neutral_loss in _residue_neutral_losses(fragment_sequence):
                    neutral_losses[neutral_loss.name] = neutral_loss
                for modification in included_modifications:
                    for neutral_loss in modification.neutral_losses:
                        neutral_losses[neutral_loss.name] = neutral_loss

            def append_ion(
                *,
                series: FragmentIonSeries,
                ion_ordinal: int,
                ion_span_start: int,
                ion_span_end: int,
                ion_sequence: str,
                neutral_mass_monoisotopic: float,
                neutral_mass_average: float,
                neutral_loss_name: str | None = None,
            ) -> None:
                for charge in charges:
                    ions.append(
                        FragmentIon(
                            series=series,
                            ordinal=ion_ordinal,
                            charge=charge,
                            span_start=ion_span_start,
                            span_end=ion_span_end,
                            sequence=ion_sequence,
                            neutral_loss=neutral_loss_name,
                            neutral_mass_monoisotopic=neutral_mass_monoisotopic,
                            neutral_mass_average=neutral_mass_average,
                            mz_monoisotopic=(
                                neutral_mass_monoisotopic
                                + (charge * _PROTON_MONOISOTOPIC_MASS)
                            )
                            / charge,
                            mz_average=(
                                neutral_mass_average + (charge * _PROTON_AVERAGE_MASS)
                            )
                            / charge,
                        )
                    )

            append_ion(
                series=fragment_series,
                ion_ordinal=ordinal,
                ion_span_start=span_start,
                ion_span_end=span_end,
                ion_sequence=fragment_sequence,
                neutral_mass_monoisotopic=mono_neutral,
                neutral_mass_average=average_neutral,
            )
            for neutral_loss in neutral_losses.values():
                append_ion(
                    series=fragment_series,
                    ion_ordinal=ordinal,
                    ion_span_start=span_start,
                    ion_span_end=span_end,
                    ion_sequence=fragment_sequence,
                    neutral_mass_monoisotopic=mono_neutral
                    - neutral_loss.monoisotopic_mass,
                    neutral_mass_average=average_neutral - neutral_loss.average_mass,
                    neutral_loss_name=neutral_loss.name,
                )

    return tuple(ions)


def validate_modified_peptide_fragment_ions(
    peptide: str | ParsedModifiedPeptide,
    *,
    charges: tuple[int, ...] = (1,),
    series: tuple[FragmentIonSeries, ...] = (FragmentIonSeries.B, FragmentIonSeries.Y),
    static_modifications: tuple[StaticModification, ...] = (),
    include_neutral_losses: bool = False,
    registry: ModificationRegistryDocument | None = None,
) -> FragmentIonShiftValidationReport:
    """Audit whether fragment-ion mass shifts match the modifications carried by each ion."""
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    modified_ions = calculate_fragment_ions(
        parsed,
        charges=charges,
        series=series,
        static_modifications=static_modifications,
        include_neutral_losses=include_neutral_losses,
        registry=registry,
    )
    baseline = parsed.model_copy(
        update={"modifications": (), "canonical_notation": parsed.sequence}
    )
    baseline_ions = calculate_fragment_ions(
        baseline,
        charges=charges,
        series=series,
        static_modifications=static_modifications,
        include_neutral_losses=include_neutral_losses,
        registry=registry,
    )
    baseline_by_key = {
        (ion.series, ion.ordinal, ion.charge, ion.neutral_loss): ion
        for ion in baseline_ions
    }
    entries: list[FragmentIonShiftValidationEntry] = []
    for ion in modified_ions:
        key = (ion.series, ion.ordinal, ion.charge, ion.neutral_loss)
        baseline_ion = baseline_by_key[key]
        included_modifications = _fragment_modifications(
            parsed,
            series=ion.series,
            ordinal=ion.ordinal,
        )
        expected_shift_monoisotopic = (
            _applied_modification_mass_delta(
                included_modifications,
                MassType.MONOISOTOPIC,
            )
            / ion.charge
        )
        expected_shift_average = (
            _applied_modification_mass_delta(
                included_modifications,
                MassType.AVERAGE,
            )
            / ion.charge
        )
        observed_shift_monoisotopic = ion.mz_monoisotopic - baseline_ion.mz_monoisotopic
        observed_shift_average = ion.mz_average - baseline_ion.mz_average
        valid = (
            abs(observed_shift_monoisotopic - expected_shift_monoisotopic) <= 1e-9
            and abs(observed_shift_average - expected_shift_average) <= 1e-9
        )
        entries.append(
            FragmentIonShiftValidationEntry(
                series=ion.series,
                ordinal=ion.ordinal,
                charge=ion.charge,
                neutral_loss=ion.neutral_loss,
                expected_shift_monoisotopic=expected_shift_monoisotopic,
                observed_shift_monoisotopic=observed_shift_monoisotopic,
                expected_shift_average=expected_shift_average,
                observed_shift_average=observed_shift_average,
                shifted=abs(observed_shift_monoisotopic) > 1e-12,
                valid=valid,
                included_modifications=included_modifications,
            )
        )
    return FragmentIonShiftValidationReport(
        canonical_notation=canonicalize_modified_peptide(parsed, registry=registry),
        valid=all(entry.valid for entry in entries),
        entries=tuple(entries),
    )
