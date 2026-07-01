# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Typed models for explicit regulator evidence and inference results."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class RegulatorEvidenceType(StrEnum):
    """Explicit upstream evidence classes supported by the regulator engine."""

    KINASE_SUBSTRATE = "kinase_substrate"
    TRANSCRIPTION_FACTOR_TARGET = "transcription_factor_target"
    PATHWAY = "pathway"
    PPI = "ppi"


class RegulatorSignalSurface(StrEnum):
    """Observed signal surface used to support one regulator result."""

    SITE_REGULATION = "site_regulation"
    PROTEIN_ABUNDANCE = "protein_abundance"
    PATHWAY_ACTIVITY = "pathway_activity"


class RegulatorInferenceDirection(StrEnum):
    """Stable direction labels preserved on one regulator result."""

    UP = "up"
    DOWN = "down"
    MIXED = "mixed"
    UNSUPPORTED = "unsupported"


class RegulatorEvidenceTargetField(StrEnum):
    """Explicit target field linked from one regulator evidence row."""

    PROTEIN_REF = "protein_ref"
    GENE_SYMBOL = "gene_symbol"
    PATHWAY_ID = "pathway_id"
    SITE_KEY = "site_key"


class RegulatorEvidenceColumnMapping(JsonModel):
    """Column mapping from one user-supplied regulator evidence table."""

    model_config = ConfigDict(extra="forbid")

    regulator: str = Field(default="regulator", min_length=1)
    evidence_type: str = Field(default="evidence_type", min_length=1)
    protein_ref: str | None = "protein_ref"
    gene_symbol: str | None = "gene_symbol"
    pathway_id: str | None = "pathway_id"
    site_key: str | None = "site_key"
    source_name: str | None = "source_name"
    source_accession: str | None = "source_accession"


class RegulatorEvidenceRecord(JsonModel):
    """One normalized regulator-to-target evidence row."""

    model_config = ConfigDict(extra="forbid")

    regulator: str = Field(..., min_length=1)
    evidence_type: RegulatorEvidenceType
    protein_ref: str | None = None
    gene_symbol: str | None = None
    pathway_id: str | None = None
    site_key: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedRegulatorEvidenceRow(JsonModel):
    """One rejected regulator evidence row with a durable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class RegulatorEvidenceImportSummary(JsonModel):
    """Stable summary over one regulator evidence import."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    regulator_count: int = Field(..., ge=0)
    kinase_substrate_record_count: int = Field(..., ge=0)
    transcription_factor_target_record_count: int = Field(..., ge=0)
    pathway_record_count: int = Field(..., ge=0)
    ppi_record_count: int = Field(..., ge=0)


class RegulatorEvidenceImportReport(JsonModel):
    """Governed import report over one regulator evidence table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[RegulatorEvidenceRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedRegulatorEvidenceRow, ...] = Field(
        default_factory=tuple
    )
    column_mapping: RegulatorEvidenceColumnMapping
    summary: RegulatorEvidenceImportSummary
    note: str = Field(..., min_length=1)


class RegulatorSiteSignalColumnMapping(JsonModel):
    """Column mapping from one user-supplied site differential table."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(default="site_key", min_length=1)
    protein_ref: str | None = "protein_ref"
    log2_fold_change: str = Field(default="log2_fold_change", min_length=1)
    adjusted_p_value: str | None = "adjusted_p_value"


class RegulatorSiteSignalEntry(JsonModel):
    """One normalized site-level differential signal row."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str | None = None
    log2_fold_change: float
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)


class RejectedRegulatorSiteSignalRow(JsonModel):
    """One rejected site-signal row with a durable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class RegulatorSiteSignalImportSummary(JsonModel):
    """Stable summary over one site-signal import."""

    model_config = ConfigDict(extra="forbid")

    accepted_entry_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_site_count: int = Field(..., ge=0)


class RegulatorSiteSignalImportReport(JsonModel):
    """Governed import report over one site differential table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_entries: tuple[RegulatorSiteSignalEntry, ...] = Field(
        default_factory=tuple
    )
    rejected_rows: tuple[RejectedRegulatorSiteSignalRow, ...] = Field(
        default_factory=tuple
    )
    column_mapping: RegulatorSiteSignalColumnMapping
    summary: RegulatorSiteSignalImportSummary
    note: str = Field(..., min_length=1)


class RegulatorInferenceEntry(JsonModel):
    """One aggregated upstream regulator result over one evidence surface."""

    model_config = ConfigDict(extra="forbid")

    regulator: str = Field(..., min_length=1)
    evidence_type: RegulatorEvidenceType
    signal_surface: RegulatorSignalSurface
    source_name: str | None = None
    source_accession: str | None = None
    target_count: int = Field(..., ge=0)
    matched_target_count: int = Field(..., ge=0)
    coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    supporting_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    supporting_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    supporting_pathway_ids: tuple[str, ...] = Field(default_factory=tuple)
    direction: RegulatorInferenceDirection
    score: float = Field(..., ge=0.0, le=1.0)
    mean_log2_fold_change: float | None = None
    mean_activity_score_delta: float | None = None
    note: str = Field(..., min_length=1)


class UnresolvedRegulatorTargetEntry(JsonModel):
    """One explicit target row that could not be linked to observed evidence."""

    model_config = ConfigDict(extra="forbid")

    regulator: str = Field(..., min_length=1)
    evidence_type: RegulatorEvidenceType
    target_field: RegulatorEvidenceTargetField
    target_value: str = Field(..., min_length=1)
    source_name: str | None = None
    source_accession: str | None = None
    reason: str = Field(..., min_length=1)


class RegulatorInferenceSummary(JsonModel):
    """Stable summary over one regulator-inference run."""

    model_config = ConfigDict(extra="forbid")

    regulator_count: int = Field(..., ge=0)
    entry_count: int = Field(..., ge=0)
    site_regulation_entry_count: int = Field(..., ge=0)
    protein_abundance_entry_count: int = Field(..., ge=0)
    pathway_activity_entry_count: int = Field(..., ge=0)
    unresolved_target_count: int = Field(..., ge=0)
    high_scoring_entry_count: int = Field(..., ge=0)


class RegulatorInferencePolicy(JsonModel):
    """Confidence policy for regulator inference coverage and scoring."""

    model_config = ConfigDict(extra="forbid")

    minimum_target_coverage_fraction: float = Field(default=0.5, ge=0.0, le=1.0)
    low_coverage_score_cap: float = Field(default=0.49, ge=0.0, le=1.0)


class RegulatorInferenceReport(JsonModel):
    """Owned upstream regulator inference report over explicit evidence rows."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    entries: tuple[RegulatorInferenceEntry, ...] = Field(default_factory=tuple)
    unresolved_targets: tuple[UnresolvedRegulatorTargetEntry, ...] = Field(
        default_factory=tuple
    )
    summary: RegulatorInferenceSummary
    note: str = Field(..., min_length=1)


__all__ = [
    "RegulatorEvidenceColumnMapping",
    "RegulatorEvidenceImportReport",
    "RegulatorEvidenceImportSummary",
    "RegulatorEvidenceRecord",
    "RegulatorEvidenceTargetField",
    "RegulatorEvidenceType",
    "RegulatorInferenceDirection",
    "RegulatorInferenceEntry",
    "RegulatorInferencePolicy",
    "RegulatorInferenceReport",
    "RegulatorInferenceSummary",
    "RegulatorSignalSurface",
    "RegulatorSiteSignalColumnMapping",
    "RegulatorSiteSignalEntry",
    "RegulatorSiteSignalImportReport",
    "RegulatorSiteSignalImportSummary",
    "RejectedRegulatorEvidenceRow",
    "RejectedRegulatorSiteSignalRow",
    "UnresolvedRegulatorTargetEntry",
]
