# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable chemistry contract models and enums."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
import re

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics.chemistry.amino_acid_mass import _CANONICAL_RESIDUES
from bijux_proteomics_foundation import DocumentSchema, JsonModel

_RESIDUE_TOKEN_RE = re.compile(r"^[A-Z]+$")
_SUPPORTED_ELEMENT_SYMBOLS = ("C", "H", "N", "O", "S", "P")


class MassType(StrEnum):
    """Supported peptide mass spaces."""

    MONOISOTOPIC = "monoisotopic"
    AVERAGE = "average"


class FragmentIonSeries(StrEnum):
    """Supported backbone fragment series."""

    A = "a"
    B = "b"
    Y = "y"


class ModificationPosition(StrEnum):
    """Where a modification can apply."""

    ANYWHERE = "anywhere"
    PEPTIDE_N_TERM = "peptide_n_term"
    PEPTIDE_C_TERM = "peptide_c_term"
    PROTEIN_N_TERM = "protein_n_term"
    PROTEIN_C_TERM = "protein_c_term"


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
    elemental_composition_delta: dict[str, int] = Field(default_factory=dict)
    neutral_losses: tuple[NeutralLoss, ...] = Field(default_factory=tuple)
    controlled_id: str | None = None
    isotopic_label_family: str | None = None

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

    @field_validator("isotopic_label_family")
    @classmethod
    def _normalize_isotopic_label_family(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None

    @field_validator("elemental_composition_delta", mode="before")
    @classmethod
    def _normalize_elemental_composition_delta(
        cls,
        value: object,
    ) -> dict[str, int]:
        if value in (None, ""):
            return {}
        if not isinstance(value, dict):
            raise ValueError("elemental composition delta must be a mapping")
        normalized: dict[str, int] = {}
        for symbol, count in value.items():
            token = str(symbol).strip()
            if token not in _SUPPORTED_ELEMENT_SYMBOLS:
                allowed = ", ".join(_SUPPORTED_ELEMENT_SYMBOLS)
                raise ValueError(
                    f"invalid elemental composition symbol {symbol!r}; expected one of {allowed}"
                )
            if isinstance(count, bool):
                raise ValueError("elemental composition counts must be integers")
            normalized_count = int(count)
            if normalized_count:
                normalized[token] = normalized_count
        return {
            symbol: normalized[symbol]
            for symbol in _SUPPORTED_ELEMENT_SYMBOLS
            if symbol in normalized
        }

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


class ModificationRegistryValidationIssue(JsonModel):
    """One registry-definition validation issue."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    modification_name: str | None = None
    controlled_id: str | None = None


class ModificationRegistryValidationReport(JsonModel):
    """Structured validation result for one modification registry."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    issues: tuple[ModificationRegistryValidationIssue, ...] = Field(
        default_factory=tuple
    )


class IsotopicLabelingPolicy(JsonModel):
    """Explicit policy for isotopic labeling and heavy modifications."""

    model_config = ConfigDict(extra="forbid")

    allow_isotopic_labels: bool = False
    allowed_label_families: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("allowed_label_families", mode="before")
    @classmethod
    def _normalize_allowed_label_families(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        families: tuple[str, ...]
        if isinstance(value, str):
            families = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("allowed label families must be iterable")
            families = tuple(str(token) for token in value)
        normalized = tuple(
            family.strip().lower() for family in families if family.strip()
        )
        return tuple(dict.fromkeys(normalized))


class ModificationProvenance(JsonModel):
    """Provenance for one applied peptide modification."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(..., min_length=1)
    assignment_token: str = Field(..., min_length=1)
    rule_path: tuple[str, ...] = Field(default_factory=tuple)
    resolved_name: str | None = None
    controlled_id: str | None = None


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
    provenance: ModificationProvenance | None = None

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
    at_protein_n_term: bool = False
    at_protein_c_term: bool = False
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
    span_start: int = Field(..., ge=1)
    span_end: int = Field(..., ge=1)
    sequence: str = Field(..., min_length=1)
    neutral_loss: str | None = None
    neutral_mass_monoisotopic: float = Field(..., gt=0.0)
    neutral_mass_average: float = Field(..., gt=0.0)
    mz_monoisotopic: float = Field(..., gt=0.0)
    mz_average: float = Field(..., gt=0.0)


class FragmentIonShiftValidationEntry(JsonModel):
    """One fragment-ion shift audit row for a modified peptide."""

    model_config = ConfigDict(extra="forbid")

    series: FragmentIonSeries
    ordinal: int = Field(..., ge=1)
    charge: int = Field(..., ge=1)
    neutral_loss: str | None = None
    expected_shift_monoisotopic: float
    observed_shift_monoisotopic: float
    expected_shift_average: float
    observed_shift_average: float
    shifted: bool
    valid: bool
    included_modifications: tuple[AppliedModification, ...] = Field(
        default_factory=tuple
    )


class FragmentIonShiftValidationReport(JsonModel):
    """Audit whether modified-peptide fragment ions shift only where expected."""

    model_config = ConfigDict(extra="forbid")

    canonical_notation: str = Field(..., min_length=1)
    valid: bool
    entries: tuple[FragmentIonShiftValidationEntry, ...] = Field(default_factory=tuple)


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

    PREDICTED = "predicted"
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

    status: IsotopeEnvelopeStatus = IsotopeEnvelopeStatus.PREDICTED
    canonical_notation: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    estimated_carbon_count: float = Field(..., ge=0.0)
    monoisotopic_mz: float = Field(..., gt=0.0)
    peaks: tuple[IsotopePeak, ...] = Field(default_factory=tuple)


class ModificationLocalizationStatus(StrEnum):
    """Support level for localization output."""

    ADVISORY = "advisory"


class ModificationLocalizationState(StrEnum):
    """Explicit localization state for one modification assignment."""

    LOCALIZED = "localized"
    AMBIGUOUS = "ambiguous"
    UNLOCALIZED = "unlocalized"
    CONFLICTING = "conflicting"
    UNSUPPORTED = "unsupported"


class ModificationLocalizationCandidate(JsonModel):
    """One modification localization advisory item."""

    model_config = ConfigDict(extra="forbid")

    modification_name: str = Field(..., min_length=1)
    assigned_site: ModificationPosition
    assigned_site_index: int | None = Field(default=None, ge=1)
    candidate_site_indices: tuple[int, ...] = Field(default_factory=tuple)
    residue_scope: tuple[str, ...] = Field(default_factory=tuple)
    localization_state: ModificationLocalizationState
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


class VariableModificationEnumerationEntry(JsonModel):
    """One deterministic modified-peptide variant from bounded enumeration."""

    model_config = ConfigDict(extra="forbid")

    canonical_notation: str = Field(..., min_length=1)
    modification_count: int = Field(..., ge=0)
    modifications: tuple[AppliedModification, ...] = Field(default_factory=tuple)


class VariableModificationEnumerationReport(JsonModel):
    """Bounded enumeration result for variable modifications on one peptide."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1)
    at_protein_n_term: bool = False
    at_protein_c_term: bool = False
    base_modification_count: int = Field(..., ge=0)
    candidate_site_count: int = Field(..., ge=0)
    generated_variant_count: int = Field(..., ge=0)
    max_variants: int = Field(..., ge=1)
    truncated: bool = False
    variants: tuple[VariableModificationEnumerationEntry, ...] = Field(
        default_factory=tuple
    )


class ModifiedPeptideExportRecord(JsonModel):
    """Stable export record for one canonical modified peptide."""

    model_config = ConfigDict(extra="forbid")

    canonical_notation: str = Field(..., min_length=1)
    sequence: str = Field(..., min_length=1)
    modification_count: int = Field(..., ge=0)
    modification_sites: tuple[str, ...] = Field(default_factory=tuple)
    modifications: tuple[AppliedModification, ...] = Field(default_factory=tuple)


__all__ = [
    "AppliedModification",
    "FragmentIon",
    "FragmentIonSeries",
    "FragmentIonShiftValidationEntry",
    "FragmentIonShiftValidationReport",
    "IsotopeEnvelopeStatus",
    "IsotopePeak",
    "IsotopicLabelingPolicy",
    "MassType",
    "ModificationLocalizationAdvisory",
    "ModificationLocalizationCandidate",
    "ModificationLocalizationState",
    "ModificationLocalizationStatus",
    "ModificationPosition",
    "ModificationProvenance",
    "ModificationRegistryDocument",
    "ModificationRegistryValidationIssue",
    "ModificationRegistryValidationReport",
    "ModificationSiteValidationIssue",
    "ModificationSiteValidationReport",
    "ModifiedPeptideExportRecord",
    "NeutralLoss",
    "ParsedModifiedPeptide",
    "PeptideChargeState",
    "PeptideIsotopeEnvelope",
    "StaticModification",
    "VariableModification",
    "VariableModificationEnumerationEntry",
    "VariableModificationEnumerationReport",
]
