# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Label-free quantification and differential abundance contracts."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    pass


class QuantEntityLevel(StrEnum):
    """Supported quantification aggregation levels."""

    PEPTIDE = "peptide"
    PROTEIN = "protein"


class QuantMeasureKind(StrEnum):
    """Supported quantification measurement kinds."""

    INTENSITY = "intensity"
    SPECTRAL_COUNT = "spectral_count"


class MissingValueKind(StrEnum):
    """Stable semantics for observed, absent, imputed, and excluded quant cells."""

    OBSERVED = "observed"
    ZERO = "zero"
    NOT_OBSERVED = "missing_not_observed"
    FILTERED = "filtered"
    IMPUTED = "imputed"
    CENSORED = "censored"
    EXCLUDED = "excluded"
    NOT_APPLICABLE = "not_applicable"


class QuantRollupMethod(StrEnum):
    """Supported peptide-to-protein quant rollup policies."""

    SUM = "sum"
    MEDIAN = "median"
    TOP_N = "top_n"


class NormalizationMethod(StrEnum):
    """Supported label-free normalization methods."""

    NONE = "none"
    TIC = "tic"
    MEDIAN = "median"
    QUANTILE = "quantile"
    LOG2_MEDIAN_CENTERING = "log2_median_centering"
    VSN_LIKE = "vsn_like"


class ImputationMethod(StrEnum):
    """Supported label-free missing-value imputation methods."""

    NONE = "none"
    LOW_INTENSITY = "low_intensity"
    GROUP_AWARE_LOW_INTENSITY = "group_aware_low_intensity"
    KNN = "knn"


class QuantAssessmentDisposition(StrEnum):
    """Whether a quantification report changes behavior or remains advisory."""

    ENFORCED = "ENFORCED"
    ADVISORY = "ADVISORY"


class MissingValueCorrectionPolicy(StrEnum):
    """Deterministic remapping policy for missing-value summary categories."""

    PRESERVE = "preserve"
    TREAT_AS_NOT_OBSERVED = "treat_as_not_observed"


class MissingChannelPolicy(StrEnum):
    """Policy for expected multiplex channels that are absent from a run."""

    PRESERVE = "preserve"
    TREAT_AS_MISSING = "treat_as_missing"
    ERROR = "error"


class LabelBasedChannelRole(StrEnum):
    """Stable role classification for multiplex quantification channels."""

    SAMPLE = "sample"
    CARRIER = "carrier"
    REFERENCE = "reference"
    QC_BRIDGE = "qc_bridge"


class Ms1FeatureColumnMapping(JsonModel):
    """User-supplied mapping from feature-table columns to the quant contract."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    intensity: str = Field(..., min_length=1)
    protein_refs: str | None = None
    feature_id: str | None = None
    charge: str | None = None
    mz: str | None = None
    retention_time_seconds: str | None = None
    missing_reason: str | None = None
    protein_separator: str = ";"


class QuantValidationIssue(JsonModel):
    """One validation issue while parsing feature quantification input."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=2)


class RejectedMs1FeatureRow(JsonModel):
    """One rejected MS1 feature row with stable issue details."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[QuantValidationIssue, ...] = Field(default_factory=tuple)


class Ms1FeatureRecord(JsonModel):
    """One normalized MS1 feature quantification row."""

    model_config = ConfigDict(extra="forbid")

    feature_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    intensity: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    charge: int | None = Field(default=None, ge=1)
    mz: float | None = Field(default=None, gt=0.0)
    retention_time_seconds: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind = MissingValueKind.OBSERVED
    missing_reason: str | None = None
    provenance: ImportedEvidenceProvenance | None = None

    @field_validator(
        "feature_id",
        "sample_id",
        "peptide",
        "canonical_peptide",
        "missing_reason",
        mode="before",
    )
    @classmethod
    def _strip_text(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("protein_refs", mode="before")
    @classmethod
    def _normalize_protein_refs(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, str):
            refs: tuple[str, ...] = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("protein references must be iterable")
            refs = tuple(str(token) for token in value)
        normalized = tuple(token.strip() for token in refs if token.strip())
        return tuple(dict.fromkeys(normalized))


class Ms1FeatureParseReport(JsonModel):
    """Stable parse report for one MS1 feature quantification table."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[Ms1FeatureRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedMs1FeatureRow, ...] = Field(default_factory=tuple)
    column_mapping: Ms1FeatureColumnMapping


class PrecursorIntensityColumnMapping(JsonModel):
    """User-supplied mapping from precursor-quant columns to the quant contract."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    intensity: str = Field(..., min_length=1)
    sample_id: str | None = "sample_id"
    run_id: str | None = "run_id"
    modified_peptide: str | None = None
    protein_refs: str | None = None
    precursor_id: str | None = None
    charge: str | None = None
    missing_reason: str | None = None
    protein_separator: str = ";"

    @model_validator(mode="after")
    def _require_sample_or_run_column(self) -> PrecursorIntensityColumnMapping:
        if self.sample_id is None and self.run_id is None:
            raise ValueError("precursor intensity mapping requires sample_id or run_id")
        return self


class RejectedPrecursorIntensityRow(JsonModel):
    """One rejected precursor-intensity row with stable issue details."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[QuantValidationIssue, ...] = Field(default_factory=tuple)


class PrecursorIntensityRecord(JsonModel):
    """One normalized precursor-intensity quantification row."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    run_id: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    modified_peptide: str | None = None
    canonical_peptide: str = Field(..., min_length=1)
    intensity: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    charge: int | None = Field(default=None, ge=1)
    missing_value_kind: MissingValueKind = MissingValueKind.OBSERVED
    missing_reason: str | None = None
    provenance: ImportedEvidenceProvenance | None = None

    @field_validator(
        "precursor_id",
        "sample_id",
        "run_id",
        "peptide_sequence",
        "modified_peptide",
        "canonical_peptide",
        "missing_reason",
        mode="before",
    )
    @classmethod
    def _strip_precursor_text(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("protein_refs", mode="before")
    @classmethod
    def _normalize_precursor_protein_refs(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, str):
            refs: tuple[str, ...] = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("protein references must be iterable")
            refs = tuple(str(token) for token in value)
        normalized = tuple(token.strip() for token in refs if token.strip())
        return tuple(dict.fromkeys(normalized))


class PrecursorIntensityParseReport(JsonModel):
    """Stable parse report for one precursor-intensity quantification table."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[PrecursorIntensityRecord, ...] = Field(
        default_factory=tuple
    )
    rejected_rows: tuple[RejectedPrecursorIntensityRow, ...] = Field(
        default_factory=tuple
    )
    column_mapping: PrecursorIntensityColumnMapping
