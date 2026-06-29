# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Peptide chemistry and modification contracts."""

from __future__ import annotations

import json
from pathlib import Path
import re

from bijux_proteomics.chemistry.amino_acid_mass import (
    _AVERAGE_RESIDUE_MASS,
    _CANONICAL_RESIDUES,
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
    IsotopicLabelingPolicy,
    MassType,
    ModificationLocalizationAdvisory,
    ModificationLocalizationCandidate,
    ModificationLocalizationState,
    ModificationLocalizationStatus as ModificationLocalizationStatus,
    ModificationPosition,
    ModificationProvenance,
    ModificationRegistryDocument,
    ModificationRegistryValidationIssue as ModificationRegistryValidationIssue,
    ModificationRegistryValidationReport as ModificationRegistryValidationReport,
    ModificationSiteValidationIssue,
    ModificationSiteValidationReport,
    ModifiedPeptideExportRecord,
    NeutralLoss,
    ParsedModifiedPeptide,
    PeptideChargeState,
    PeptideIsotopeEnvelope,
    StaticModification,
    VariableModification,
    VariableModificationEnumerationEntry,
    VariableModificationEnumerationReport,
    _RESIDUE_TOKEN_RE,
)
from bijux_proteomics.chemistry.contracts.registry_access import (
    build_modification_registry as build_modification_registry,
    get_modification,
    load_modification_registry as load_modification_registry,
    modification_registry,
    registry_lookup,
    resolve_modification_definition,
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
_DELTA_TOKEN_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d+)?|\.\d+)$")


def _format_mass_delta(delta: float) -> str:
    rendered = f"{delta:+.6f}".rstrip("0").rstrip(".")
    return rendered if "." in rendered else f"{rendered}.0"


def _build_applied_modification(
    *,
    token: str,
    site: ModificationPosition,
    site_index: int | None,
    sequence: str,
    registry: ModificationRegistryDocument | None,
    at_protein_n_term: bool = False,
    at_protein_c_term: bool = False,
    labeling_policy: IsotopicLabelingPolicy | None = None,
) -> AppliedModification:
    stripped_token = token.strip()
    definition = None
    if not _DELTA_TOKEN_RE.fullmatch(stripped_token):
        definition = resolve_modification_definition(
            token=stripped_token,
            site=site,
            residue=sequence[site_index - 1]
            if site is ModificationPosition.ANYWHERE and site_index is not None
            else None,
            at_protein_n_term=at_protein_n_term,
            at_protein_c_term=at_protein_c_term,
            registry=registry,
        )
    _validate_isotopic_label_policy(definition, labeling_policy=labeling_policy)
    residue = (
        sequence[site_index - 1]
        if site is ModificationPosition.ANYWHERE and site_index is not None
        else None
    )
    if definition is None:
        name, mono, average, losses, controlled_id, source = _resolve_token(
            stripped_token,
            registry=registry,
        )
    else:
        name = definition.name
        mono = definition.mass_delta_monoisotopic
        average = definition.mass_delta_average
        losses = definition.neutral_losses
        controlled_id = definition.controlled_id
        source = "registry"
    return AppliedModification(
        name=name,
        token=definition.name if definition is not None else _format_mass_delta(mono),
        site=site,
        site_index=site_index,
        residue=residue,
        mass_delta_monoisotopic=mono,
        mass_delta_average=average,
        neutral_losses=losses,
        controlled_id=controlled_id,
        source=source,
        provenance=_build_modification_provenance(
            token=stripped_token,
            source=source,
            resolved_name=name,
            definition=definition,
            controlled_id=controlled_id,
        ),
    )


def _candidate_definition_for_delta(
    *,
    delta: float,
    site: ModificationPosition,
    residue: str | None,
    registry: ModificationRegistryDocument | None,
    tolerance: float = 1e-6,
) -> StaticModification | VariableModification | None:
    for definition in registry_lookup(registry).values():
        if abs(definition.mass_delta_monoisotopic - delta) > tolerance:
            continue
        if definition.position is not site:
            continue
        if (
            site is ModificationPosition.ANYWHERE
            and residue is not None
            and definition.residues
            and residue not in definition.residues
        ):
            continue
        return definition
    return None


def _build_modification_provenance(
    *,
    token: str,
    source: str,
    resolved_name: str,
    definition: StaticModification | VariableModification | None,
    controlled_id: str | None,
) -> ModificationProvenance:
    if definition is not None:
        return ModificationProvenance(
            source=source,
            assignment_token=token,
            rule_path=(
                "modification_registry",
                definition.application,
                definition.name,
            ),
            resolved_name=resolved_name,
            controlled_id=controlled_id,
        )
    return ModificationProvenance(
        source=source,
        assignment_token=token,
        rule_path=("explicit_delta", _format_mass_delta(float(token))),
        resolved_name=resolved_name,
        controlled_id=controlled_id,
    )


def _validate_isotopic_label_policy(
    definition: StaticModification | VariableModification | None,
    *,
    labeling_policy: IsotopicLabelingPolicy | None,
) -> None:
    if definition is None or definition.isotopic_label_family is None:
        return
    if labeling_policy is None or not labeling_policy.allow_isotopic_labels:
        raise ValueError(
            f"isotopic label modification {definition.name!r} requires an explicit labeling policy"
        )
    if (
        labeling_policy.allowed_label_families
        and definition.isotopic_label_family
        not in labeling_policy.allowed_label_families
    ):
        raise ValueError(
            f"isotopic label family {definition.isotopic_label_family!r} is not allowed by the active labeling policy"
        )


def _coerce_sequence(peptide: str | ParsedModifiedPeptide) -> str:
    sequence = (
        peptide.sequence if isinstance(peptide, ParsedModifiedPeptide) else peptide
    )
    normalized = sequence.strip().upper()
    if not _RESIDUE_TOKEN_RE.fullmatch(normalized):
        raise ValueError(
            "peptide sequence must use canonical uppercase amino-acid symbols"
        )
    return normalized


def _ensure_parsed_peptide(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> ParsedModifiedPeptide:
    if isinstance(peptide, ParsedModifiedPeptide):
        return peptide
    if "[" in peptide:
        return parse_modified_peptide(peptide, registry=registry)
    normalized = _coerce_sequence(peptide)
    return ParsedModifiedPeptide(
        sequence=normalized,
        modifications=(),
        at_protein_n_term=False,
        at_protein_c_term=False,
        canonical_notation=normalized,
    )


def _normalize_terminal_token(
    token: str,
    *,
    default_site: ModificationPosition,
) -> tuple[str, ModificationPosition]:
    name, separator, site_token = token.partition("@")
    if not separator:
        return token, default_site
    site_label = site_token.strip().lower()
    if site_label in {"protein-n-term", "protein_n_term", "protein-nterm"}:
        return name, ModificationPosition.PROTEIN_N_TERM
    if site_label in {"protein-c-term", "protein_c_term", "protein-cterm"}:
        return name, ModificationPosition.PROTEIN_C_TERM
    raise ValueError(f"unsupported terminal modification site {site_token!r}")


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


def build_modification_localization_advisory(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> ModificationLocalizationAdvisory:
    """Emit an advisory-only localization summary until scored localization exists."""
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    mapping = registry_lookup(registry)
    try:
        canonical_notation = canonicalize_modified_peptide(parsed, registry=registry)
    except ValueError:
        canonical_notation = parsed.canonical_notation
    candidates: list[ModificationLocalizationCandidate] = []
    for modification in parsed.modifications:
        residue_scope: tuple[str, ...] = ()
        candidate_site_indices: tuple[int, ...] = ()
        if modification.source == "registry":
            definition = mapping.get(modification.name.strip().lower())
            if definition is not None:
                residue_scope = definition.residues
                if definition.position is ModificationPosition.ANYWHERE:
                    candidate_site_indices = tuple(
                        index
                        for index, residue in enumerate(parsed.sequence, start=1)
                        if residue in definition.residues
                    )
        elif modification.residue is not None and modification.site_index is not None:
            residue_scope = (modification.residue,)
            candidate_site_indices = tuple(
                index
                for index, residue in enumerate(parsed.sequence, start=1)
                if residue == modification.residue
            )

        candidates.append(
            ModificationLocalizationCandidate(
                modification_name=modification.name,
                assigned_site=modification.site,
                assigned_site_index=modification.site_index,
                candidate_site_indices=candidate_site_indices,
                residue_scope=residue_scope,
                localization_state=_classify_modification_localization_state(
                    modification=modification,
                    candidate_site_indices=candidate_site_indices,
                ),
                ambiguous=len(candidate_site_indices) > 1,
            )
        )
    return ModificationLocalizationAdvisory(
        canonical_notation=canonical_notation,
        note="localization is advisory only; site scores and probability models are not implemented yet",
        candidates=tuple(candidates),
    )


def _classify_modification_localization_state(
    *,
    modification: AppliedModification,
    candidate_site_indices: tuple[int, ...],
) -> ModificationLocalizationState:
    if modification.site is not ModificationPosition.ANYWHERE:
        return ModificationLocalizationState.LOCALIZED
    if not candidate_site_indices:
        return (
            ModificationLocalizationState.CONFLICTING
            if modification.site_index is not None
            else ModificationLocalizationState.UNSUPPORTED
        )
    if modification.site_index is None:
        return ModificationLocalizationState.UNLOCALIZED
    if modification.site_index not in candidate_site_indices:
        return ModificationLocalizationState.CONFLICTING
    if len(candidate_site_indices) > 1:
        return ModificationLocalizationState.AMBIGUOUS
    return ModificationLocalizationState.LOCALIZED


def enumerate_variable_modifications(
    peptide: str | ParsedModifiedPeptide,
    *,
    variable_modifications: tuple[VariableModification, ...] = (),
    registry: ModificationRegistryDocument | None = None,
    labeling_policy: IsotopicLabelingPolicy | None = None,
    max_variants: int = 128,
) -> VariableModificationEnumerationReport:
    """Enumerate deterministic modified-peptide variants within a hard bound."""
    if max_variants < 1:
        raise ValueError("max_variants must be at least 1")
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    definitions = (
        variable_modifications
        if variable_modifications
        else (registry or modification_registry()).variable_modifications
    )
    candidate_groups = [
        _enumeration_candidates_for_definition(
            parsed,
            definition=definition,
            registry=registry,
            labeling_policy=labeling_policy,
        )
        for definition in definitions
    ]
    base_site_keys: set[tuple[str, int | None]] = set()
    for modification in parsed.modifications:
        site_key = _physical_site_key(modification)
        if site_key is not None:
            base_site_keys.add(site_key)
    variants: list[VariableModificationEnumerationEntry] = []
    truncated = False

    def visit(
        index: int,
        selected: list[AppliedModification],
        occupied_site_keys: set[tuple[str, int | None]],
    ) -> None:
        nonlocal truncated
        if truncated:
            return
        if index == len(candidate_groups):
            combined = tuple(
                sorted(
                    (*parsed.modifications, *selected),
                    key=lambda modification: (
                        0
                        if modification.site
                        in {
                            ModificationPosition.PEPTIDE_N_TERM,
                            ModificationPosition.PROTEIN_N_TERM,
                        }
                        else 1,
                        modification.site_index or 0,
                        2
                        if modification.site
                        in {
                            ModificationPosition.PEPTIDE_C_TERM,
                            ModificationPosition.PROTEIN_C_TERM,
                        }
                        else 1,
                        modification.token,
                    ),
                )
            )
            variants.append(
                VariableModificationEnumerationEntry(
                    canonical_notation=_render_modified_peptide(
                        parsed.sequence,
                        combined,
                    ),
                    modification_count=len(combined),
                    modifications=combined,
                )
            )
            if len(variants) >= max_variants:
                truncated = True
            return

        definition, candidates = candidate_groups[index]
        definition_limit = definition.max_occurrences or len(candidates)
        candidate_choices: list[tuple[AppliedModification, ...]] = [()]
        for count in range(1, min(definition_limit, len(candidates)) + 1):
            candidate_choices.extend(combinations(candidates, count))

        for choice in candidate_choices:
            choice_site_keys = {
                _physical_site_key(modification) for modification in choice
            }
            if None in choice_site_keys:
                continue
            typed_choice_site_keys: set[tuple[str, int | None]] = {
                site_key for site_key in choice_site_keys if site_key is not None
            }
            if occupied_site_keys & typed_choice_site_keys:
                continue
            visit(
                index + 1,
                [*selected, *choice],
                occupied_site_keys | typed_choice_site_keys,
            )

    from itertools import combinations

    visit(0, [], set(base_site_keys))
    return VariableModificationEnumerationReport(
        sequence=parsed.sequence,
        at_protein_n_term=parsed.at_protein_n_term,
        at_protein_c_term=parsed.at_protein_c_term,
        base_modification_count=len(parsed.modifications),
        candidate_site_count=sum(
            len(candidates) for _definition, candidates in candidate_groups
        ),
        generated_variant_count=len(variants),
        max_variants=max_variants,
        truncated=truncated,
        variants=tuple(variants),
    )


def _resolve_token(
    token: str,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> tuple[str, float, float, tuple[NeutralLoss, ...], str | None, str]:
    normalized = token.strip()
    if _DELTA_TOKEN_RE.fullmatch(normalized):
        delta = float(normalized)
        return (
            f"delta:{_format_mass_delta(delta)}",
            delta,
            delta,
            (),
            None,
            "delta",
        )

    definition = get_modification(normalized, registry=registry)
    return (
        definition.name,
        definition.mass_delta_monoisotopic,
        definition.mass_delta_average,
        definition.neutral_losses,
        definition.controlled_id,
        "registry",
    )


def _validate_definition_site(
    *,
    definition: StaticModification | VariableModification | None,
    sequence: str,
    site: ModificationPosition,
    site_index: int | None,
    at_protein_n_term: bool = False,
    at_protein_c_term: bool = False,
) -> str | None:
    if definition is None:
        return sequence[site_index - 1] if site_index is not None else None
    allowed_sites = {definition.position}
    if definition.position is ModificationPosition.PEPTIDE_N_TERM:
        allowed_sites.add(ModificationPosition.PROTEIN_N_TERM)
    if definition.position is ModificationPosition.PEPTIDE_C_TERM:
        allowed_sites.add(ModificationPosition.PROTEIN_C_TERM)
    if site not in allowed_sites:
        raise ValueError(
            f"modification {definition.name!r} requires site {definition.position.value}, got {site.value}"
        )
    if site is ModificationPosition.ANYWHERE:
        if site_index is None:
            raise ValueError(
                f"modification {definition.name!r} requires a residue site index"
            )
        residue = sequence[site_index - 1]
        if definition.residues and residue not in definition.residues:
            allowed = ",".join(definition.residues)
            raise ValueError(
                f"modification {definition.name!r} is not valid on residue {residue} at position {site_index}; expected one of {allowed}"
            )
        return residue
    if site is ModificationPosition.PROTEIN_N_TERM and not at_protein_n_term:
        raise ValueError(
            f"modification {definition.name!r} requires a peptide at the protein N-terminus"
        )
    if site is ModificationPosition.PROTEIN_C_TERM and not at_protein_c_term:
        raise ValueError(
            f"modification {definition.name!r} requires a peptide at the protein C-terminus"
        )
    return None


def _enumeration_candidates_for_definition(
    peptide: ParsedModifiedPeptide,
    *,
    definition: VariableModification,
    registry: ModificationRegistryDocument | None,
    labeling_policy: IsotopicLabelingPolicy | None,
) -> tuple[VariableModification, tuple[AppliedModification, ...]]:
    sequence = peptide.sequence
    candidates: list[AppliedModification] = []
    if definition.position is ModificationPosition.ANYWHERE:
        for site_index, residue in enumerate(sequence, start=1):
            if residue not in definition.residues:
                continue
            candidates.append(
                _build_applied_modification(
                    token=definition.name,
                    site=ModificationPosition.ANYWHERE,
                    site_index=site_index,
                    sequence=sequence,
                    registry=registry,
                    at_protein_n_term=peptide.at_protein_n_term,
                    at_protein_c_term=peptide.at_protein_c_term,
                    labeling_policy=labeling_policy,
                )
            )
    elif definition.position is ModificationPosition.PEPTIDE_N_TERM:
        candidates.append(
            _build_applied_modification(
                token=definition.name,
                site=ModificationPosition.PEPTIDE_N_TERM,
                site_index=None,
                sequence=sequence,
                registry=registry,
                at_protein_n_term=peptide.at_protein_n_term,
                at_protein_c_term=peptide.at_protein_c_term,
                labeling_policy=labeling_policy,
            )
        )
    elif definition.position is ModificationPosition.PEPTIDE_C_TERM:
        candidates.append(
            _build_applied_modification(
                token=definition.name,
                site=ModificationPosition.PEPTIDE_C_TERM,
                site_index=None,
                sequence=sequence,
                registry=registry,
                at_protein_n_term=peptide.at_protein_n_term,
                at_protein_c_term=peptide.at_protein_c_term,
                labeling_policy=labeling_policy,
            )
        )
    elif definition.position is ModificationPosition.PROTEIN_N_TERM:
        if peptide.at_protein_n_term:
            candidates.append(
                _build_applied_modification(
                    token=definition.name,
                    site=ModificationPosition.PROTEIN_N_TERM,
                    site_index=None,
                    sequence=sequence,
                    registry=registry,
                    at_protein_n_term=peptide.at_protein_n_term,
                    at_protein_c_term=peptide.at_protein_c_term,
                    labeling_policy=labeling_policy,
                )
            )
    elif (
        definition.position is ModificationPosition.PROTEIN_C_TERM
        and peptide.at_protein_c_term
    ):
        candidates.append(
            _build_applied_modification(
                token=definition.name,
                site=ModificationPosition.PROTEIN_C_TERM,
                site_index=None,
                sequence=sequence,
                registry=registry,
                at_protein_n_term=peptide.at_protein_n_term,
                at_protein_c_term=peptide.at_protein_c_term,
                labeling_policy=labeling_policy,
            )
        )
    return definition, tuple(candidates)


def _physical_site_key(
    modification: AppliedModification,
) -> tuple[str, int | None] | None:
    if modification.site is ModificationPosition.ANYWHERE:
        return ("residue", modification.site_index)
    if modification.site in {
        ModificationPosition.PEPTIDE_N_TERM,
        ModificationPosition.PROTEIN_N_TERM,
    }:
        return ("n_term", None)
    if modification.site in {
        ModificationPosition.PEPTIDE_C_TERM,
        ModificationPosition.PROTEIN_C_TERM,
    }:
        return ("c_term", None)
    return None


def _raise_on_impossible_modification_combination(
    modifications: tuple[AppliedModification, ...],
) -> None:
    by_site: dict[tuple[str, int | None], list[AppliedModification]] = {}
    for modification in modifications:
        site_key = _physical_site_key(modification)
        if site_key is None:
            continue
        by_site.setdefault(site_key, []).append(modification)

    conflicting_sites = [
        (site_key, site_modifications)
        for site_key, site_modifications in by_site.items()
        if len(site_modifications) > 1
    ]
    if not conflicting_sites:
        return

    site_key, site_modifications = conflicting_sites[0]
    site_label = (
        f"residue {site_key[1]}"
        if site_key[0] == "residue"
        else "peptide N-terminus"
        if site_key[0] == "n_term"
        else "peptide C-terminus"
    )
    tokens = ", ".join(modification.token for modification in site_modifications)
    raise ValueError(
        f"chemically incompatible modifications occupy the same physical site ({site_label}): {tokens}"
    )


def parse_modified_peptide(
    notation: str,
    *,
    registry: ModificationRegistryDocument | None = None,
    at_protein_n_term: bool = False,
    at_protein_c_term: bool = False,
    labeling_policy: IsotopicLabelingPolicy | None = None,
) -> ParsedModifiedPeptide:
    """Parse modified peptide bracket notation into a stable contract."""
    text = notation.strip()
    modifications: list[AppliedModification] = []

    index = 0
    residues: list[str] = []

    if text.startswith("["):
        close = text.find("]")
        if close == -1 or close + 1 >= len(text) or text[close + 1] != "-":
            raise ValueError(
                "N-terminal modifications must use [token]-PEPTIDE notation"
            )
        token = text[1:close]
        token, parsed_site = _normalize_terminal_token(
            token,
            default_site=ModificationPosition.PEPTIDE_N_TERM,
        )
        modifications.append(
            _build_applied_modification(
                token=token,
                site=parsed_site,
                site_index=None,
                sequence="",
                registry=registry,
                at_protein_n_term=at_protein_n_term,
                at_protein_c_term=at_protein_c_term,
                labeling_policy=labeling_policy,
            )
        )
        index = close + 2

    while index < len(text):
        character = text[index]
        if character == "-":
            break
        if character not in _CANONICAL_RESIDUES:
            raise ValueError(f"invalid peptide notation character {character!r}")
        residues.append(character)
        index += 1
        if index < len(text) and text[index] == "[":
            close = text.find("]", index)
            if close == -1:
                raise ValueError("unterminated modification token")
            token = text[index + 1 : close]
            sequence = "".join(residues)
            modifications.append(
                _build_applied_modification(
                    token=token,
                    site=ModificationPosition.ANYWHERE,
                    site_index=len(sequence),
                    sequence=sequence,
                    registry=registry,
                    at_protein_n_term=at_protein_n_term,
                    at_protein_c_term=at_protein_c_term,
                    labeling_policy=labeling_policy,
                )
            )
            index = close + 1

    sequence = "".join(residues)
    if not sequence:
        raise ValueError("modified peptide notation must contain at least one residue")

    if index < len(text):
        if not text[index:].startswith("-[") or not text.endswith("]"):
            raise ValueError(
                "C-terminal modifications must use PEPTIDE-[token] notation"
            )
        token = text[index + 2 : -1]
        token, parsed_site = _normalize_terminal_token(
            token,
            default_site=ModificationPosition.PEPTIDE_C_TERM,
        )
        modifications.append(
            _build_applied_modification(
                token=token,
                site=parsed_site,
                site_index=None,
                sequence=sequence,
                registry=registry,
                at_protein_n_term=at_protein_n_term,
                at_protein_c_term=at_protein_c_term,
                labeling_policy=labeling_policy,
            )
        )

    _raise_on_impossible_modification_combination(tuple(modifications))
    return ParsedModifiedPeptide(
        sequence=sequence,
        modifications=tuple(modifications),
        at_protein_n_term=at_protein_n_term,
        at_protein_c_term=at_protein_c_term,
        canonical_notation=_render_modified_peptide(sequence, tuple(modifications)),
    )


def build_modified_peptide(
    sequence: str,
    *,
    assignments: tuple[str, ...] = (),
    registry: ModificationRegistryDocument | None = None,
    at_protein_n_term: bool = False,
    at_protein_c_term: bool = False,
    labeling_policy: IsotopicLabelingPolicy | None = None,
) -> ParsedModifiedPeptide:
    """Build a modified peptide from site-assignment strings."""
    normalized = _coerce_sequence(sequence)
    modifications: list[AppliedModification] = []
    for assignment in assignments:
        token, separator, site_token = assignment.partition("@")
        if not separator:
            raise ValueError(
                "modification assignments must use token@site syntax such as Oxidation@3 or Acetyl@n-term"
            )
        site_label = site_token.strip().lower()
        if site_label in {"n-term", "nterm", "peptide_n_term"}:
            site = ModificationPosition.PEPTIDE_N_TERM
            site_index = None
        elif site_label in {"protein-n-term", "protein_n_term", "protein-nterm"}:
            site = ModificationPosition.PROTEIN_N_TERM
            site_index = None
        elif site_label in {"c-term", "cterm", "peptide_c_term"}:
            site = ModificationPosition.PEPTIDE_C_TERM
            site_index = None
        elif site_label in {"protein-c-term", "protein_c_term", "protein-cterm"}:
            site = ModificationPosition.PROTEIN_C_TERM
            site_index = None
        else:
            try:
                site_index = int(site_label)
            except ValueError as exc:
                raise ValueError(f"invalid modification site {site_token!r}") from exc
            if site_index < 1 or site_index > len(normalized):
                raise ValueError(
                    f"modification site {site_index} is outside peptide length {len(normalized)}"
                )
            site = ModificationPosition.ANYWHERE
        modifications.append(
            _build_applied_modification(
                token=token,
                site=site,
                site_index=site_index,
                sequence=normalized
                if site is ModificationPosition.ANYWHERE
                else normalized,
                registry=registry,
                at_protein_n_term=at_protein_n_term,
                at_protein_c_term=at_protein_c_term,
                labeling_policy=labeling_policy,
            )
        )
    _raise_on_impossible_modification_combination(tuple(modifications))
    ordered = tuple(
        sorted(
            modifications,
            key=lambda modification: (
                0 if modification.site is ModificationPosition.PEPTIDE_N_TERM else 1,
                modification.site_index or 0,
                2 if modification.site is ModificationPosition.PEPTIDE_C_TERM else 1,
                modification.token,
            ),
        )
    )
    return ParsedModifiedPeptide(
        sequence=normalized,
        modifications=ordered,
        at_protein_n_term=at_protein_n_term,
        at_protein_c_term=at_protein_c_term,
        canonical_notation=_render_modified_peptide(normalized, ordered),
    )


def canonicalize_modified_peptide(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> str:
    """Return a stable canonical notation for one modified peptide."""
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    canonicalized: list[AppliedModification] = []
    for modification in parsed.modifications:
        if modification.source == "delta":
            definition = _candidate_definition_for_delta(
                delta=modification.mass_delta_monoisotopic,
                site=modification.site,
                residue=modification.residue,
                registry=registry,
            )
            if definition is not None:
                canonicalized.append(
                    modification.model_copy(
                        update={
                            "name": definition.name,
                            "token": definition.name,
                            "controlled_id": definition.controlled_id,
                            "neutral_losses": definition.neutral_losses,
                        }
                    )
                )
                continue
        elif modification.source == "registry":
            canonicalized.append(
                modification.model_copy(update={"token": modification.name})
            )
            continue
        canonicalized.append(
            modification.model_copy(
                update={
                    "token": _format_mass_delta(modification.mass_delta_monoisotopic)
                }
            )
        )
    ordered = tuple(
        sorted(
            canonicalized,
            key=lambda modification: (
                0 if modification.site is ModificationPosition.PEPTIDE_N_TERM else 1,
                modification.site_index or 0,
                2 if modification.site is ModificationPosition.PEPTIDE_C_TERM else 1,
                modification.token,
            ),
        )
    )
    return _render_modified_peptide(parsed.sequence, ordered)


def build_modified_peptide_export_record(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> ModifiedPeptideExportRecord:
    """Build one stable export record for a canonical modified peptide."""
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    canonical = canonicalize_modified_peptide(parsed, registry=registry)
    ordered = tuple(
        sorted(
            parsed.modifications,
            key=lambda modification: (
                0
                if modification.site
                in {
                    ModificationPosition.PEPTIDE_N_TERM,
                    ModificationPosition.PROTEIN_N_TERM,
                }
                else 1,
                modification.site_index or 0,
                2
                if modification.site
                in {
                    ModificationPosition.PEPTIDE_C_TERM,
                    ModificationPosition.PROTEIN_C_TERM,
                }
                else 1,
                modification.token,
            ),
        )
    )
    return ModifiedPeptideExportRecord(
        canonical_notation=canonical,
        sequence=parsed.sequence,
        modification_count=len(ordered),
        modification_sites=tuple(
            _render_modification_site(modification) for modification in ordered
        ),
        modifications=ordered,
    )


def export_modified_peptides_jsonl(
    peptides: tuple[str | ParsedModifiedPeptide, ...],
    path: Path,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> Path:
    """Write stable JSONL export rows for canonical modified peptides."""
    rows = [
        build_modified_peptide_export_record(peptide, registry=registry).to_dict()
        for peptide in peptides
    ]
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n")
    return path


def export_modified_peptides_tsv(
    peptides: tuple[str | ParsedModifiedPeptide, ...],
    path: Path,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> Path:
    """Write stable TSV export rows for canonical modified peptides."""
    header = "\t".join(
        [
            "canonical_notation",
            "sequence",
            "modification_count",
            "modification_sites",
        ]
    )
    lines = [header]
    for peptide in peptides:
        record = build_modified_peptide_export_record(peptide, registry=registry)
        lines.append(
            "\t".join(
                [
                    record.canonical_notation,
                    record.sequence,
                    str(record.modification_count),
                    ";".join(record.modification_sites),
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n")
    return path


def validate_modified_peptide_sites(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> ModificationSiteValidationReport:
    """Validate modified peptide site assignments into a structured report."""
    try:
        parsed = _ensure_parsed_peptide(peptide, registry=registry)
    except ValueError as exc:
        text = (
            peptide.sequence
            if isinstance(peptide, ParsedModifiedPeptide)
            else str(peptide)
        )
        sequence = "".join(
            character for character in text.upper() if character.isalpha()
        )
        return ModificationSiteValidationReport(
            valid=False,
            sequence=sequence or "UNKNOWN",
            issues=(
                ModificationSiteValidationIssue(
                    code="invalid_modification_site",
                    message=str(exc),
                    site=ModificationPosition.ANYWHERE,
                ),
            ),
        )
    return ModificationSiteValidationReport(
        valid=True,
        sequence=parsed.sequence,
        canonical_notation=canonicalize_modified_peptide(parsed, registry=registry),
        issues=(),
    )


def _render_modified_peptide(
    sequence: str,
    modifications: tuple[AppliedModification, ...],
) -> str:
    tokens_by_index: dict[int, list[str]] = {}
    n_term_tokens: list[str] = []
    c_term_tokens: list[str] = []
    for modification in modifications:
        token = _render_modification_token(modification)
        if modification.site in {
            ModificationPosition.PEPTIDE_N_TERM,
            ModificationPosition.PROTEIN_N_TERM,
        }:
            n_term_tokens.append(f"[{token}]")
        elif modification.site in {
            ModificationPosition.PEPTIDE_C_TERM,
            ModificationPosition.PROTEIN_C_TERM,
        }:
            c_term_tokens.append(f"[{token}]")
        else:
            site_index = modification.site_index
            if site_index is None:
                raise ValueError(
                    "residue modification is missing a required site index"
                )
            tokens_by_index.setdefault(site_index, []).append(f"[{token}]")

    rendered = "".join(n_term_tokens)
    if n_term_tokens:
        rendered += "-"
    for index, residue in enumerate(sequence, start=1):
        rendered += residue
        for token in tokens_by_index.get(index, ()):
            rendered += token
    if c_term_tokens:
        rendered += "-" + "".join(c_term_tokens)
    return rendered


def _render_modification_token(modification: AppliedModification) -> str:
    if modification.site is ModificationPosition.PROTEIN_N_TERM:
        return f"{modification.token}@protein-n-term"
    if modification.site is ModificationPosition.PROTEIN_C_TERM:
        return f"{modification.token}@protein-c-term"
    return modification.token


def _render_modification_site(modification: AppliedModification) -> str:
    if modification.site is ModificationPosition.ANYWHERE:
        return str(modification.site_index)
    if modification.site is ModificationPosition.PEPTIDE_N_TERM:
        return "peptide_n_term"
    if modification.site is ModificationPosition.PEPTIDE_C_TERM:
        return "peptide_c_term"
    if modification.site is ModificationPosition.PROTEIN_N_TERM:
        return "protein_n_term"
    return "protein_c_term"


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
