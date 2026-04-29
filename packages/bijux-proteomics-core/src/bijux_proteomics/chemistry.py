# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Peptide chemistry and modification contracts."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from math import exp, factorial
from pathlib import Path
import re

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics_foundation import DocumentSchema, JsonModel

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
_WATER_MONOISOTOPIC_MASS = 18.01056
_WATER_AVERAGE_MASS = 18.01528
_AMMONIA_MONOISOTOPIC_MASS = 17.026549
_AMMONIA_AVERAGE_MASS = 17.03052
_PHOSPHORIC_ACID_MONOISOTOPIC_MASS = 97.976896
_PHOSPHORIC_ACID_AVERAGE_MASS = 97.9952
_C13_NEUTRON_SHIFT = 1.0033548378
_RESIDUE_TOKEN_RE = re.compile(r"^[A-Z]+$")
_DELTA_TOKEN_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d+)?|\.\d+)$")


class MassType(StrEnum):
    """Supported peptide mass spaces."""

    MONOISOTOPIC = "monoisotopic"
    AVERAGE = "average"


class FragmentIonSeries(StrEnum):
    """Supported backbone fragment series."""

    B = "b"
    Y = "y"


class ModificationPosition(StrEnum):
    """Where a modification can apply."""

    ANYWHERE = "anywhere"
    PEPTIDE_N_TERM = "peptide_n_term"
    PEPTIDE_C_TERM = "peptide_c_term"


class NeutralLoss(JsonModel):
    """One neutral loss that can be emitted from a fragment ion."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    monoisotopic_mass: float = Field(..., gt=0.0)
    average_mass: float = Field(..., gt=0.0)


class _BaseModification(JsonModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    residues: tuple[str, ...] = Field(default_factory=tuple)
    position: ModificationPosition = ModificationPosition.ANYWHERE
    mass_delta_monoisotopic: float
    mass_delta_average: float
    neutral_losses: tuple[NeutralLoss, ...] = Field(default_factory=tuple)
    controlled_id: str | None = None

    @field_validator("residues", mode="before")
    @classmethod
    def _normalize_residues(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, str):
            residues = tuple(value.strip().upper())
        else:
            if not isinstance(value, Iterable):
                raise ValueError("modification residues must be iterable")
            residues = tuple(str(token).strip().upper() for token in value)
        invalid = [
            residue for residue in residues if residue not in _CANONICAL_RESIDUES
        ]
        if invalid:
            raise ValueError(
                f"invalid modification residues: {', '.join(sorted(set(invalid)))}"
            )
        return tuple(sorted(dict.fromkeys(residues)))

    @model_validator(mode="after")
    def _validate_site_specificity(self) -> _BaseModification:
        if self.position is ModificationPosition.ANYWHERE and not self.residues:
            raise ValueError(
                "residue-scoped modifications must declare at least one target residue"
            )
        return self


class StaticModification(_BaseModification):
    """Static modification applied to every compatible site."""

    application: str = Field(default="static", frozen=True)


class VariableModification(_BaseModification):
    """Variable modification that can be applied to selected sites."""

    application: str = Field(default="variable", frozen=True)
    max_occurrences: int | None = Field(default=None, ge=1)


class ModificationRegistryDocument(JsonModel):
    """Stable modification registry document."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    static_modifications: tuple[StaticModification, ...] = Field(default_factory=tuple)
    variable_modifications: tuple[VariableModification, ...] = Field(
        default_factory=tuple
    )


class AppliedModification(JsonModel):
    """One concrete modification placed onto a peptide site."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    token: str = Field(..., min_length=1)
    site: ModificationPosition
    site_index: int | None = Field(default=None, ge=1)
    residue: str | None = None
    mass_delta_monoisotopic: float
    mass_delta_average: float
    neutral_losses: tuple[NeutralLoss, ...] = Field(default_factory=tuple)
    controlled_id: str | None = None
    source: str = Field(default="registry", min_length=1)

    @field_validator("residue")
    @classmethod
    def _normalize_residue(cls, value: str | None) -> str | None:
        if value is None:
            return None
        residue = value.strip().upper()
        if residue not in _CANONICAL_RESIDUES:
            raise ValueError(f"invalid residue {value!r}")
        return residue


class ParsedModifiedPeptide(JsonModel):
    """Parsed peptide plus explicit site-localized modifications."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1)
    modifications: tuple[AppliedModification, ...] = Field(default_factory=tuple)
    canonical_notation: str = Field(..., min_length=1)

    @field_validator("sequence")
    @classmethod
    def _normalize_sequence(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not _RESIDUE_TOKEN_RE.fullmatch(normalized):
            raise ValueError("sequence must use canonical uppercase amino-acid symbols")
        return normalized


class FragmentIon(JsonModel):
    """One theoretical fragment ion."""

    model_config = ConfigDict(extra="forbid")

    series: FragmentIonSeries
    ordinal: int = Field(..., ge=1)
    charge: int = Field(..., ge=1)
    sequence: str = Field(..., min_length=1)
    neutral_loss: str | None = None
    neutral_mass_monoisotopic: float = Field(..., gt=0.0)
    neutral_mass_average: float = Field(..., gt=0.0)
    mz_monoisotopic: float = Field(..., gt=0.0)
    mz_average: float = Field(..., gt=0.0)


class ModificationSiteValidationIssue(JsonModel):
    """One modification-site validation issue."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    site: ModificationPosition
    site_index: int | None = Field(default=None, ge=1)
    residue: str | None = None


class ModificationSiteValidationReport(JsonModel):
    """Structured site-validation result for a modified peptide."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    sequence: str = Field(..., min_length=1)
    canonical_notation: str | None = None
    issues: tuple[ModificationSiteValidationIssue, ...] = Field(default_factory=tuple)


class PeptideChargeState(JsonModel):
    """Resolved peptide neutral mass plus one charge-state projection."""

    model_config = ConfigDict(extra="forbid")

    canonical_notation: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    mass_type: MassType
    neutral_mass: float
    mz: float


class IsotopeEnvelopeStatus(StrEnum):
    """Support level for isotope-envelope output."""

    ADVISORY = "advisory"


class IsotopePeak(JsonModel):
    """One approximate isotope peak."""

    model_config = ConfigDict(extra="forbid")

    isotope_index: int = Field(..., ge=0)
    intensity: float = Field(..., ge=0.0)
    mz: float = Field(..., gt=0.0)


class PeptideIsotopeEnvelope(JsonModel):
    """Approximate isotope envelope for a precursor."""

    model_config = ConfigDict(extra="forbid")

    status: IsotopeEnvelopeStatus = IsotopeEnvelopeStatus.ADVISORY
    canonical_notation: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    estimated_carbon_count: float = Field(..., ge=0.0)
    monoisotopic_mz: float = Field(..., gt=0.0)
    peaks: tuple[IsotopePeak, ...] = Field(default_factory=tuple)


class ModificationLocalizationStatus(StrEnum):
    """Support level for localization output."""

    ADVISORY = "advisory"


class ModificationLocalizationCandidate(JsonModel):
    """One modification localization advisory item."""

    model_config = ConfigDict(extra="forbid")

    modification_name: str = Field(..., min_length=1)
    assigned_site: ModificationPosition
    assigned_site_index: int | None = Field(default=None, ge=1)
    candidate_site_indices: tuple[int, ...] = Field(default_factory=tuple)
    residue_scope: tuple[str, ...] = Field(default_factory=tuple)
    ambiguous: bool = False


class ModificationLocalizationAdvisory(JsonModel):
    """Advisory-only localization output until real scoring exists."""

    model_config = ConfigDict(extra="forbid")

    status: ModificationLocalizationStatus = ModificationLocalizationStatus.ADVISORY
    canonical_notation: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)
    candidates: tuple[ModificationLocalizationCandidate, ...] = Field(
        default_factory=tuple
    )


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
) -> AppliedModification:
    mapping = _registry_lookup(registry)
    stripped_token = token.strip()
    definition = (
        None
        if _DELTA_TOKEN_RE.fullmatch(stripped_token)
        else mapping.get(stripped_token.lower())
    )
    residue = _validate_definition_site(
        definition=definition,
        sequence=sequence,
        site=site,
        site_index=site_index,
    )
    name, mono, average, losses, controlled_id, source = _resolve_token(
        stripped_token,
        registry=registry,
    )
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
    )


def _candidate_definition_for_delta(
    *,
    delta: float,
    site: ModificationPosition,
    residue: str | None,
    registry: ModificationRegistryDocument | None,
    tolerance: float = 1e-6,
) -> StaticModification | VariableModification | None:
    for definition in _registry_lookup(registry).values():
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


def _build_builtin_registry() -> ModificationRegistryDocument:
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="peptide_modification_registry",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    registry = ModificationRegistryDocument(
        document_schema=schema,
        static_modifications=(
            StaticModification(
                name="Carbamidomethyl",
                residues=("C",),
                position=ModificationPosition.ANYWHERE,
                mass_delta_monoisotopic=57.021464,
                mass_delta_average=57.05132,
                controlled_id="UNIMOD:4",
            ),
        ),
        variable_modifications=(
            VariableModification(
                name="Oxidation",
                residues=("M",),
                position=ModificationPosition.ANYWHERE,
                mass_delta_monoisotopic=15.994915,
                mass_delta_average=15.9994,
                controlled_id="UNIMOD:35",
            ),
            VariableModification(
                name="Phospho",
                residues=("S", "T", "Y"),
                position=ModificationPosition.ANYWHERE,
                mass_delta_monoisotopic=79.966331,
                mass_delta_average=79.9799,
                neutral_losses=(
                    NeutralLoss(
                        name="phosphoric_acid",
                        monoisotopic_mass=_PHOSPHORIC_ACID_MONOISOTOPIC_MASS,
                        average_mass=_PHOSPHORIC_ACID_AVERAGE_MASS,
                    ),
                ),
                controlled_id="UNIMOD:21",
            ),
            VariableModification(
                name="Acetyl",
                position=ModificationPosition.PEPTIDE_N_TERM,
                mass_delta_monoisotopic=42.010565,
                mass_delta_average=42.0367,
                controlled_id="UNIMOD:1",
            ),
            VariableModification(
                name="Amidated",
                position=ModificationPosition.PEPTIDE_C_TERM,
                mass_delta_monoisotopic=-0.984016,
                mass_delta_average=-0.9848,
                controlled_id="UNIMOD:2",
            ),
        ),
    )
    payload = registry.to_dict()
    return registry.model_copy(
        update={"document_schema": registry.document_schema.with_content_hash(payload)}
    )


_BUILTIN_REGISTRY = _build_builtin_registry()


def build_modification_registry(
    *,
    static_modifications: tuple[StaticModification, ...] = (),
    variable_modifications: tuple[VariableModification, ...] = (),
) -> ModificationRegistryDocument:
    """Build a stable user-supplied modification registry document."""
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="peptide_modification_registry",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    registry = ModificationRegistryDocument(
        document_schema=schema,
        static_modifications=static_modifications,
        variable_modifications=variable_modifications,
    )
    payload = registry.to_dict()
    return registry.model_copy(
        update={"document_schema": registry.document_schema.with_content_hash(payload)}
    )


def modification_registry() -> ModificationRegistryDocument:
    """Return the built-in peptide modification registry."""
    return _BUILTIN_REGISTRY.model_copy(deep=True)


def load_modification_registry(path: Path) -> ModificationRegistryDocument:
    """Load and validate a modification registry document from JSON."""
    return ModificationRegistryDocument.model_validate_json(path.read_text())


def _registry_lookup(
    registry: ModificationRegistryDocument | None,
) -> dict[str, StaticModification | VariableModification]:
    active_registry = registry or modification_registry()
    mapping: dict[str, StaticModification | VariableModification] = {}
    for modification in active_registry.static_modifications:
        mapping[modification.name.strip().lower()] = modification
    for variable_modification in active_registry.variable_modifications:
        mapping[variable_modification.name.strip().lower()] = variable_modification
    return mapping


def get_modification(
    name: str,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> StaticModification | VariableModification:
    """Return one modification definition from the active registry."""
    normalized = name.strip().lower()
    try:
        return _registry_lookup(registry)[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown modification {name!r}") from exc


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
        canonical_notation=normalized,
    )


def _mass_delta_for(
    mass_type: MassType,
    *,
    mono: float,
    average: float,
) -> float:
    return mono if mass_type is MassType.MONOISOTOPIC else average


def _base_residue_mass(sequence: str, mass_type: MassType) -> float:
    table = (
        _MONOISOTOPIC_RESIDUE_MASS
        if mass_type is MassType.MONOISOTOPIC
        else _AVERAGE_RESIDUE_MASS
    )
    water_mass = (
        _WATER_MONOISOTOPIC_MASS
        if mass_type is MassType.MONOISOTOPIC
        else _WATER_AVERAGE_MASS
    )
    return water_mass + sum(table[residue] for residue in sequence)


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
            modification.position is ModificationPosition.PEPTIDE_N_TERM
            and include_n_term
        ) or (
            modification.position is ModificationPosition.PEPTIDE_C_TERM
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
            modification.site is ModificationPosition.PEPTIDE_N_TERM and include_n_term
        ) or (
            modification.site is ModificationPosition.PEPTIDE_C_TERM and include_c_term
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
        _base_residue_mass(parsed.sequence, MassType.MONOISOTOPIC)
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
        _base_residue_mass(parsed.sequence, MassType.AVERAGE)
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
    peak_count: int = 4,
    registry: ModificationRegistryDocument | None = None,
) -> PeptideIsotopeEnvelope:
    """Approximate a precursor isotope envelope using an averagine-style advisory model."""
    if peak_count < 1:
        raise ValueError("peak_count must be at least 1")
    charge_state = build_peptide_charge_state(
        peptide,
        charge=charge,
        mass_type=MassType.MONOISOTOPIC,
        registry=registry,
    )
    estimated_carbon_count = max((charge_state.neutral_mass / 111.1254) * 4.9384, 0.0)
    lambda_13c = estimated_carbon_count * 0.0107
    raw_intensities = tuple(
        exp(-lambda_13c) * (lambda_13c**index) / factorial(index)
        for index in range(peak_count)
    )
    total_intensity = sum(raw_intensities) or 1.0
    peaks = tuple(
        IsotopePeak(
            isotope_index=index,
            intensity=intensity / total_intensity,
            mz=charge_state.mz + ((_C13_NEUTRON_SHIFT * index) / charge),
        )
        for index, intensity in enumerate(raw_intensities)
    )
    return PeptideIsotopeEnvelope(
        canonical_notation=charge_state.canonical_notation,
        charge=charge,
        estimated_carbon_count=estimated_carbon_count,
        monoisotopic_mz=charge_state.mz,
        peaks=peaks,
    )


def build_modification_localization_advisory(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> ModificationLocalizationAdvisory:
    """Emit an advisory-only localization summary until scored localization exists."""
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    mapping = _registry_lookup(registry)
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
                ambiguous=len(candidate_site_indices) > 1,
            )
        )
    return ModificationLocalizationAdvisory(
        canonical_notation=canonicalize_modified_peptide(parsed, registry=registry),
        note="localization is advisory only; site scores and probability models are not implemented yet",
        candidates=tuple(candidates),
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
) -> str | None:
    if definition is None:
        return sequence[site_index - 1] if site_index is not None else None
    if definition.position is not site:
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
    return None


def parse_modified_peptide(
    notation: str,
    *,
    registry: ModificationRegistryDocument | None = None,
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
        modifications.append(
            _build_applied_modification(
                token=token,
                site=ModificationPosition.PEPTIDE_N_TERM,
                site_index=None,
                sequence="",
                registry=registry,
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
        modifications.append(
            _build_applied_modification(
                token=token,
                site=ModificationPosition.PEPTIDE_C_TERM,
                site_index=None,
                sequence=sequence,
                registry=registry,
            )
        )

    return ParsedModifiedPeptide(
        sequence=sequence,
        modifications=tuple(modifications),
        canonical_notation=_render_modified_peptide(sequence, tuple(modifications)),
    )


def build_modified_peptide(
    sequence: str,
    *,
    assignments: tuple[str, ...] = (),
    registry: ModificationRegistryDocument | None = None,
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
        elif site_label in {"c-term", "cterm", "peptide_c_term"}:
            site = ModificationPosition.PEPTIDE_C_TERM
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
            )
        )
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
        token = modification.token
        if modification.site is ModificationPosition.PEPTIDE_N_TERM:
            n_term_tokens.append(f"[{token}]")
        elif modification.site is ModificationPosition.PEPTIDE_C_TERM:
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
        if modification.site is ModificationPosition.PEPTIDE_N_TERM:
            if series is FragmentIonSeries.B:
                selected.append(modification)
        elif modification.site is ModificationPosition.PEPTIDE_C_TERM:
            if series is FragmentIonSeries.Y:
                selected.append(modification)
        else:
            site_index = modification.site_index
            if site_index is None:
                raise ValueError(
                    "residue modification is missing a required site index"
                )
            if series is FragmentIonSeries.B and site_index <= ordinal:
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
    """Calculate theoretical b/y fragment ions for one peptide."""
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    if len(parsed.sequence) < 2:
        return ()
    invalid_charges = [charge for charge in charges if charge < 1]
    if invalid_charges:
        raise ValueError("fragment charges must all be at least 1")

    ions: list[FragmentIon] = []
    for fragment_series in series:
        for ordinal in range(1, len(parsed.sequence)):
            if fragment_series is FragmentIonSeries.B:
                fragment_sequence = parsed.sequence[:ordinal]
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
            else:
                fragment_sequence = parsed.sequence[-ordinal:]
                mono_neutral = _WATER_MONOISOTOPIC_MASS + sum(
                    _MONOISOTOPIC_RESIDUE_MASS[residue] for residue in fragment_sequence
                )
                average_neutral = _WATER_AVERAGE_MASS + sum(
                    _AVERAGE_RESIDUE_MASS[residue] for residue in fragment_sequence
                )
                start = len(parsed.sequence) - ordinal + 1
                mono_neutral += _matching_static_mass_delta(
                    parsed.sequence,
                    static_modifications,
                    MassType.MONOISOTOPIC,
                    start=start,
                    end=len(parsed.sequence),
                    include_n_term=False,
                    include_c_term=True,
                )
                average_neutral += _matching_static_mass_delta(
                    parsed.sequence,
                    static_modifications,
                    MassType.AVERAGE,
                    start=start,
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
                ion_sequence=fragment_sequence,
                neutral_mass_monoisotopic=mono_neutral,
                neutral_mass_average=average_neutral,
            )
            for neutral_loss in neutral_losses.values():
                append_ion(
                    series=fragment_series,
                    ion_ordinal=ordinal,
                    ion_sequence=fragment_sequence,
                    neutral_mass_monoisotopic=mono_neutral
                    - neutral_loss.monoisotopic_mass,
                    neutral_mass_average=average_neutral - neutral_loss.average_mass,
                    neutral_loss_name=neutral_loss.name,
                )

    return tuple(ions)
