# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned protein functional-region models and stable report contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class ProteinRegionContextColumnMapping(JsonModel):
    """Column mapping from one protein-region table into owned region fields."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    start: str = Field(..., min_length=1)
    end: str = Field(..., min_length=1)
    domain_name: str | None = None
    signal_peptide: str | None = None
    transmembrane_region: str | None = None
    disorder_region: str | None = None
    low_complexity_region: str | None = None
    active_site_label: str | None = None
    binding_region: str | None = None
    motif_name: str | None = None
    conservation_score: str | None = None
    source_name: str | None = None
    source_accession: str | None = None


class ProteinRegionContextValidationIssue(JsonModel):
    """One validation issue from a protein-region annotation row."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=2)


class RejectedProteinRegionContextRow(JsonModel):
    """One rejected protein-region annotation row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[ProteinRegionContextValidationIssue, ...] = Field(
        default_factory=tuple
    )


class ProteinRegionContextRecord(JsonModel):
    """One normalized protein region or feature annotation row."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    start: int = Field(..., ge=1)
    end: int = Field(..., ge=1)
    domain_name: str | None = None
    signal_peptide: str | None = None
    transmembrane_region: str | None = None
    disorder_region: str | None = None
    low_complexity_region: str | None = None
    active_site_label: str | None = None
    binding_region: str | None = None
    motif_name: str | None = None
    conservation_score: float | None = Field(default=None, ge=0.0, le=1.0)
    source_name: str | None = None
    source_accession: str | None = None


class ProteinRegionContextImportSummary(JsonModel):
    """Stable summary over one protein-region import pass."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_protein_ref_count: int = Field(..., ge=0)
    domain_record_count: int = Field(..., ge=0)
    signal_peptide_record_count: int = Field(..., ge=0)
    transmembrane_record_count: int = Field(..., ge=0)
    disorder_record_count: int = Field(..., ge=0)
    low_complexity_record_count: int = Field(..., ge=0)
    active_site_record_count: int = Field(..., ge=0)
    binding_region_record_count: int = Field(..., ge=0)
    motif_record_count: int = Field(..., ge=0)
    conservation_record_count: int = Field(..., ge=0)


class ProteinRegionContextImportReport(JsonModel):
    """Governed protein-region annotation import report."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[ProteinRegionContextRecord, ...] = Field(
        default_factory=tuple
    )
    rejected_rows: tuple[RejectedProteinRegionContextRow, ...] = Field(
        default_factory=tuple
    )
    column_mapping: ProteinRegionContextColumnMapping
    summary: ProteinRegionContextImportSummary
    note: str = Field(..., min_length=1)


class ProteinFunctionalRegionKind(StrEnum):
    """Stable functional-region kinds exposed on evidence surfaces."""

    DOMAIN = "domain"
    SIGNAL_PEPTIDE = "signal_peptide"
    TRANSMEMBRANE_REGION = "transmembrane_region"
    DISORDER_REGION = "disorder_region"
    LOW_COMPLEXITY_REGION = "low_complexity_region"
    ACTIVE_SITE = "active_site"
    BINDING_REGION = "binding_region"
    MOTIF = "motif"


class ProteinFunctionalRegionEvidence(JsonModel):
    """One functional-region annotation linked to supporting evidence."""

    model_config = ConfigDict(extra="forbid")

    region_kind: ProteinFunctionalRegionKind
    label: str = Field(..., min_length=1)
    start: int = Field(..., ge=1)
    end: int = Field(..., ge=1)
    source_name: str | None = None
    source_accession: str | None = None
    supporting_evidence_refs: tuple[str, ...] = Field(default_factory=tuple)


class ProteinRegionContextStatus(StrEnum):
    """Whether one evidence item lands inside provided protein-region annotations."""

    CONTEXT_ANNOTATED = "context_annotated"
    OUTSIDE_PROVIDED_ANNOTATIONS = "outside_provided_annotations"
    UNMAPPED_TO_SEQUENCE = "unmapped_to_sequence"


class ProteinSiteRegionReference(JsonModel):
    """One site-level evidence row to place onto protein-region annotations."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    position: int = Field(..., ge=1)


class ProteinSiteRegionContextEntry(JsonModel):
    """One site-level evidence row with aggregated protein functional context."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    position: int = Field(..., ge=1)
    matched_context_record_count: int = Field(..., ge=0)
    context_status: ProteinRegionContextStatus
    domain_names: tuple[str, ...] = Field(default_factory=tuple)
    signal_peptides: tuple[str, ...] = Field(default_factory=tuple)
    transmembrane_regions: tuple[str, ...] = Field(default_factory=tuple)
    disorder_regions: tuple[str, ...] = Field(default_factory=tuple)
    low_complexity_regions: tuple[str, ...] = Field(default_factory=tuple)
    active_site_labels: tuple[str, ...] = Field(default_factory=tuple)
    binding_regions: tuple[str, ...] = Field(default_factory=tuple)
    motif_names: tuple[str, ...] = Field(default_factory=tuple)
    conservation_scores: tuple[float, ...] = Field(default_factory=tuple)
    max_conservation_score: float | None = Field(default=None, ge=0.0, le=1.0)
    source_names: tuple[str, ...] = Field(default_factory=tuple)
    source_accessions: tuple[str, ...] = Field(default_factory=tuple)
    functional_regions: tuple[ProteinFunctionalRegionEvidence, ...] = Field(
        default_factory=tuple
    )


class ProteinSiteRegionContextSummary(JsonModel):
    """Stable summary over site-level functional-context mapping."""

    model_config = ConfigDict(extra="forbid")

    site_count: int = Field(..., ge=0)
    context_annotated_site_count: int = Field(..., ge=0)
    outside_annotation_site_count: int = Field(..., ge=0)
    domain_annotated_site_count: int = Field(..., ge=0)
    signal_peptide_annotated_site_count: int = Field(..., ge=0)
    transmembrane_annotated_site_count: int = Field(..., ge=0)
    disorder_annotated_site_count: int = Field(..., ge=0)
    low_complexity_annotated_site_count: int = Field(..., ge=0)
    active_site_annotated_site_count: int = Field(..., ge=0)
    binding_region_annotated_site_count: int = Field(..., ge=0)
    motif_annotated_site_count: int = Field(..., ge=0)
    conservation_annotated_site_count: int = Field(..., ge=0)


class ProteinSiteRegionContextReport(JsonModel):
    """Owned site-level functional-context report over observed protein sites."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ProteinSiteRegionContextEntry, ...] = Field(default_factory=tuple)
    summary: ProteinSiteRegionContextSummary
    note: str = Field(..., min_length=1)


class ProteinPeptideSpan(JsonModel):
    """One peptide span on a protein sequence."""

    model_config = ConfigDict(extra="forbid")

    start: int = Field(..., ge=1)
    end: int = Field(..., ge=1)


class ProteinPeptideRegionReference(JsonModel):
    """One peptide-level evidence row to place onto protein-region annotations."""

    model_config = ConfigDict(extra="forbid")

    peptide_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)


class ProteinPeptideRegionContextEntry(JsonModel):
    """One peptide-level evidence row with aggregated functional context."""

    model_config = ConfigDict(extra="forbid")

    peptide_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    spans: tuple[ProteinPeptideSpan, ...] = Field(default_factory=tuple)
    matched_context_record_count: int = Field(..., ge=0)
    context_status: ProteinRegionContextStatus
    domain_names: tuple[str, ...] = Field(default_factory=tuple)
    signal_peptides: tuple[str, ...] = Field(default_factory=tuple)
    transmembrane_regions: tuple[str, ...] = Field(default_factory=tuple)
    disorder_regions: tuple[str, ...] = Field(default_factory=tuple)
    low_complexity_regions: tuple[str, ...] = Field(default_factory=tuple)
    active_site_labels: tuple[str, ...] = Field(default_factory=tuple)
    binding_regions: tuple[str, ...] = Field(default_factory=tuple)
    motif_names: tuple[str, ...] = Field(default_factory=tuple)
    conservation_scores: tuple[float, ...] = Field(default_factory=tuple)
    max_conservation_score: float | None = Field(default=None, ge=0.0, le=1.0)
    source_names: tuple[str, ...] = Field(default_factory=tuple)
    source_accessions: tuple[str, ...] = Field(default_factory=tuple)
    functional_regions: tuple[ProteinFunctionalRegionEvidence, ...] = Field(
        default_factory=tuple
    )


class ProteinPeptideRegionContextSummary(JsonModel):
    """Stable summary over peptide-level functional-context mapping."""

    model_config = ConfigDict(extra="forbid")

    peptide_count: int = Field(..., ge=0)
    context_annotated_peptide_count: int = Field(..., ge=0)
    outside_annotation_peptide_count: int = Field(..., ge=0)
    unmapped_peptide_count: int = Field(..., ge=0)
    domain_annotated_peptide_count: int = Field(..., ge=0)
    signal_peptide_annotated_peptide_count: int = Field(..., ge=0)
    transmembrane_annotated_peptide_count: int = Field(..., ge=0)
    disorder_annotated_peptide_count: int = Field(..., ge=0)
    low_complexity_annotated_peptide_count: int = Field(..., ge=0)
    active_site_annotated_peptide_count: int = Field(..., ge=0)
    binding_region_annotated_peptide_count: int = Field(..., ge=0)
    motif_annotated_peptide_count: int = Field(..., ge=0)
    conservation_annotated_peptide_count: int = Field(..., ge=0)


class ProteinPeptideRegionContextReport(JsonModel):
    """Owned peptide-level functional-context report over peptide evidence."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ProteinPeptideRegionContextEntry, ...] = Field(default_factory=tuple)
    summary: ProteinPeptideRegionContextSummary
    note: str = Field(..., min_length=1)


__all__ = [
    "ProteinFunctionalRegionEvidence",
    "ProteinFunctionalRegionKind",
    "ProteinPeptideRegionContextEntry",
    "ProteinPeptideRegionContextReport",
    "ProteinPeptideRegionContextSummary",
    "ProteinPeptideRegionReference",
    "ProteinPeptideSpan",
    "ProteinRegionContextColumnMapping",
    "ProteinRegionContextImportReport",
    "ProteinRegionContextImportSummary",
    "ProteinRegionContextRecord",
    "ProteinRegionContextStatus",
    "ProteinRegionContextValidationIssue",
    "ProteinSiteRegionContextEntry",
    "ProteinSiteRegionContextReport",
    "ProteinSiteRegionContextSummary",
    "ProteinSiteRegionReference",
    "RejectedProteinRegionContextRow",
]
