# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical scientific records shared across core import and engine boundaries."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics_foundation import JsonModel


class TargetDecoyState(StrEnum):
    """Stable target-decoy state for cross-boundary scientific evidence."""

    TARGET = "target"
    DECOY = "decoy"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class ContrastKind(StrEnum):
    """Stable contrast family names for cross-workflow study comparisons."""

    PAIRWISE = "pairwise"
    CASE_CONTROL = "case_control"
    PAIRED = "paired"
    TIME_COURSE = "time_course"
    MULTI_CONDITION = "multi_condition"


class QuantEntityKind(StrEnum):
    """Stable entity levels allowed inside canonical quant matrices."""

    PEPTIDE = "peptide"
    PROTEIN = "protein"
    PROTEIN_GROUP = "protein_group"
    PRECURSOR = "precursor"
    TRANSITION = "transition"
    PTM_SITE = "ptm_site"


class QuantMeasureKind(StrEnum):
    """Stable quantitative measures allowed inside canonical quant matrices."""

    INTENSITY = "intensity"
    SPECTRAL_COUNT = "spectral_count"
    RATIO = "ratio"
    LOG2_ABUNDANCE = "log2_abundance"


class MissingValueState(StrEnum):
    """Stable distinction between observed, zero, and missing quant cells."""

    OBSERVED = "observed"
    ZERO = "zero"
    NOT_OBSERVED = "missing_not_observed"
    FILTERED = "filtered"


class _CanonicalRecord(JsonModel):
    """Base helper for domain records with explicit dict-equivalent contracts."""

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def documented_dict_required_fields(cls) -> tuple[str, ...]:
        """Return the fixed required fields for dict-equivalent exchange."""

        return tuple(
            field_name
            for field_name, field_info in cls.model_fields.items()
            if field_info.is_required()
        )


class ProteinRecord(_CanonicalRecord):
    """Canonical protein-level evidence or summary record."""

    record_id: str = Field(..., min_length=1)
    primary_protein_ref: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptide_sequences: tuple[str, ...] = Field(default_factory=tuple)
    score: float | None = None
    q_value: float | None = Field(default=None, ge=0.0)
    abundance: float | None = Field(default=None, ge=0.0)
    target_decoy_state: TargetDecoyState = TargetDecoyState.UNKNOWN
    metadata: dict[str, str] = Field(default_factory=dict)


class PeptideRecord(_CanonicalRecord):
    """Canonical peptide-level evidence record."""

    record_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    spectrum_ids: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    score: float | None = None
    q_value: float | None = Field(default=None, ge=0.0)
    abundance: float | None = Field(default=None, ge=0.0)
    target_decoy_state: TargetDecoyState = TargetDecoyState.UNKNOWN
    metadata: dict[str, str] = Field(default_factory=dict)


class ModifiedPeptide(_CanonicalRecord):
    """Canonical modified-peptide record for identification and PTM workflows."""

    record_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    modified_peptide: str = Field(..., min_length=1)
    modification_names: tuple[str, ...] = Field(default_factory=tuple)
    charge_state: int | None = Field(default=None, ge=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, str] = Field(default_factory=dict)


class SpectrumRecord(_CanonicalRecord):
    """Canonical spectrum-level record."""

    spectrum_id: str = Field(..., min_length=1)
    precursor_mz: float = Field(..., gt=0.0)
    peak_count: int = Field(..., ge=0)
    run_id: str | None = None
    native_id: str | None = None
    ms_level: int | None = Field(default=None, ge=1)
    precursor_charge: int | None = Field(default=None, ge=1)
    retention_time_seconds: float | None = Field(default=None, ge=0.0)
    precursor_intensity: float | None = Field(default=None, ge=0.0)
    metadata: dict[str, str] = Field(default_factory=dict)


class PSMRecord(_CanonicalRecord):
    """Canonical peptide-spectrum match record."""

    spectrum_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    charge_state: int = Field(..., ge=1)
    score: float
    run_id: str | None = None
    modified_peptide: str | None = None
    intensity: float | None = Field(default=None, ge=0.0)
    q_value: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_state: TargetDecoyState = TargetDecoyState.UNKNOWN
    contaminant_flag: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)


class ProteinGroup(_CanonicalRecord):
    """Canonical indistinguishable protein-group record."""

    group_id: str = Field(..., min_length=1)
    representative_protein: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptides: tuple[str, ...] = Field(default_factory=tuple)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    score: float | None = None
    q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_state: TargetDecoyState = TargetDecoyState.UNKNOWN
    metadata: dict[str, str] = Field(default_factory=dict)


class SampleMetadata(_CanonicalRecord):
    """Canonical sample metadata record shared across quant workflows."""

    sample_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    replicate: int | None = Field(default=None, ge=1)
    fraction: int | None = Field(default=None, ge=1)
    batch: str | None = None
    pair_id: str | None = None
    timepoint: str | None = None
    plex_id: str | None = None
    channel: str | None = None
    sample_role: str | None = None
    cohort: str | None = None
    instrument: str | None = None
    search_engine: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class Contrast(_CanonicalRecord):
    """Canonical study contrast definition."""

    contrast_id: str = Field(..., min_length=1)
    left_condition: str = Field(..., min_length=1)
    right_condition: str = Field(..., min_length=1)
    kind: ContrastKind
    pair_id_field: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class QuantMatrix(_CanonicalRecord):
    """Canonical numeric matrix with explicit missingness and metadata."""

    matrix_id: str = Field(..., min_length=1)
    entity_kind: QuantEntityKind
    measure_kind: QuantMeasureKind
    entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    values: tuple[tuple[float | None, ...], ...] = Field(default_factory=tuple)
    missing_value_states: tuple[tuple[MissingValueState, ...], ...] = Field(
        default_factory=tuple
    )
    row_metadata: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    sample_metadata: tuple[SampleMetadata, ...] = Field(default_factory=tuple)
    transformation_history: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("entity_ids", "sample_ids", mode="before")
    @classmethod
    def _normalize_identifier_tuple(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            values = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("matrix identifiers must be iterable")
            values = tuple(str(item) for item in value)
        normalized = tuple(item.strip() for item in values if item.strip())
        return tuple(dict.fromkeys(normalized))

    @model_validator(mode="after")
    def _validate_matrix_shape(self) -> QuantMatrix:
        row_count = len(self.entity_ids)
        column_count = len(self.sample_ids)
        if len(self.values) != row_count:
            raise ValueError("values must contain one row per entity_id")
        if len(self.missing_value_states) != row_count:
            raise ValueError("missing_value_states must contain one row per entity_id")
        if self.row_metadata and len(self.row_metadata) != row_count:
            raise ValueError("row_metadata must align with entity_ids")
        for row in self.values:
            if len(row) != column_count:
                raise ValueError("each values row must align with sample_ids")
        for row in self.missing_value_states:
            if len(row) != column_count:
                raise ValueError(
                    "each missing_value_states row must align with sample_ids"
                )
        if self.sample_metadata and len(self.sample_metadata) != column_count:
            raise ValueError("sample_metadata must align with sample_ids")
        if self.sample_metadata:
            metadata_sample_ids = tuple(item.sample_id for item in self.sample_metadata)
            if metadata_sample_ids != self.sample_ids:
                raise ValueError("sample_metadata sample_id order must match sample_ids")
        return self


class PTMSite(_CanonicalRecord):
    """Canonical PTM site record."""

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    localized_peptides: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    localization_score: float | None = Field(default=None, ge=0.0)
    q_value: float | None = Field(default=None, ge=0.0)
    ambiguous: bool = False
    candidate_positions: tuple[int, ...] = Field(default_factory=tuple)
    metadata: dict[str, str] = Field(default_factory=dict)


class TransitionRecord(_CanonicalRecord):
    """Canonical targeted or DIA transition-level record."""

    transition_id: str = Field(..., min_length=1)
    precursor_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)
    peptide_sequence: str = Field(..., min_length=1)
    run_id: str | None = None
    protein_ref: str | None = None
    fragment_label: str | None = None
    retention_time_minutes: float | None = Field(default=None, ge=0.0)
    precursor_mz: float | None = Field(default=None, gt=0.0)
    fragment_mz: float | None = Field(default=None, gt=0.0)
    quality_flag: str | None = None
    q_value: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedEvidence(_CanonicalRecord):
    """Canonical rejected-row or rejected-evidence record."""

    record_kind: str = Field(..., min_length=1)
    rejection_reason: str = Field(..., min_length=1)
    source_name: str | None = None
    row_number: int | None = Field(default=None, ge=1)
    record_id: str | None = None
    raw_fields: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
