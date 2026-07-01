# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""FragPipe import models for reviewer-facing adapter surfaces."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.rejected_evidence_table import (
    RejectedEvidenceTableEntry,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterNormalizationReport,
)
from bijux_proteomics_foundation import JsonModel


class FragpipePsmReviewEntry(JsonModel):
    """Reviewer-facing PSM row from one FragPipe import bundle."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    modified_peptide: str | None = None
    canonical_modified_peptide: str | None = None
    charge: int = Field(..., ge=1)
    hyperscore: float
    q_value: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    assigned_modifications: tuple[str, ...] = Field(default_factory=tuple)
    observed_modifications: tuple[str, ...] = Field(default_factory=tuple)
    mass_difference: float | None = None
    open_search_candidate: bool = False
    provenance: ImportedEvidenceProvenance


class FragpipeCanonicalPsmEntry(JsonModel):
    """Canonical PSM contract plus FragPipe-specific mass-delta evidence."""

    model_config = ConfigDict(extra="forbid")

    record: PsmRecord
    assigned_modifications: tuple[str, ...] = Field(default_factory=tuple)
    observed_modifications: tuple[str, ...] = Field(default_factory=tuple)
    mass_difference: float | None = None
    open_search_candidate: bool = False


class FragpipePeptideReviewEntry(JsonModel):
    """Reviewer-facing peptide-table row from one FragPipe bundle."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    modified_peptide: str | None = None
    canonical_modified_peptide: str | None = None
    charge: int | None = Field(default=None, ge=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    mapped_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    assigned_modifications: tuple[str, ...] = Field(default_factory=tuple)
    observed_modifications: tuple[str, ...] = Field(default_factory=tuple)
    hyperscore: float | None = None
    probability: float | None = Field(default=None, ge=0.0)
    q_value: float | None = Field(default=None, ge=0.0)
    spectral_count: int | None = Field(default=None, ge=0)
    mass_difference: float | None = None
    open_search_candidate: bool = False
    provenance: ImportedEvidenceProvenance


class FragpipeProteinReviewEntry(JsonModel):
    """Reviewer-facing protein-table row from one FragPipe bundle."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    entry_name: str | None = None
    gene_name: str | None = None
    description: str | None = None
    coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    total_peptides: int | None = Field(default=None, ge=0)
    unique_peptides: int | None = Field(default=None, ge=0)
    spectral_count: int | None = Field(default=None, ge=0)
    probability: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel
    provenance: ImportedEvidenceProvenance


class FragpipeOpenSearchEvidenceEntry(JsonModel):
    """One preserved open-search mass-delta row from the FragPipe bundle."""

    model_config = ConfigDict(extra="forbid")

    entity_kind: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    modified_peptide: str | None = None
    canonical_modified_peptide: str | None = None
    mass_difference: float


class FragpipeProteinQuantityEntry(JsonModel):
    """One optional FragPipe quant-table protein abundance row."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    abundance: float = Field(..., ge=0.0)
    quantity_kind: str = Field(..., min_length=1)
    target_decoy_label: TargetDecoyLabel
    provenance: ImportedEvidenceProvenance


class FragpipeImportSummary(JsonModel):
    """Compact summary over one imported FragPipe result bundle."""

    model_config = ConfigDict(extra="forbid")

    accepted_psm_count: int = Field(..., ge=0)
    rejected_psm_count: int = Field(..., ge=0)
    peptide_row_count: int = Field(..., ge=0)
    protein_row_count: int = Field(..., ge=0)
    canonical_psm_count: int = Field(..., ge=0)
    peptide_evidence_count: int = Field(..., ge=0)
    protein_reference_count: int = Field(..., ge=0)
    open_search_evidence_count: int = Field(..., ge=0)
    protein_quantity_count: int = Field(..., ge=0)
    modified_psm_count: int = Field(..., ge=0)
    modified_peptide_row_count: int = Field(..., ge=0)
    open_search_psm_count: int = Field(..., ge=0)
    open_search_peptide_count: int = Field(..., ge=0)
    q_value_psm_count: int = Field(..., ge=0)
    q_value_peptide_count: int = Field(..., ge=0)
    mapped_protein_count: int = Field(..., ge=0)
    target_protein_count: int = Field(..., ge=0)
    decoy_protein_count: int = Field(..., ge=0)


class FragpipeImportReport(JsonModel):
    """One governed FragPipe bundle import report."""

    model_config = ConfigDict(extra="forbid")

    psm_normalization: SearchAdapterNormalizationReport
    canonical_psms: tuple[FragpipeCanonicalPsmEntry, ...] = Field(default_factory=tuple)
    psm_rows: tuple[FragpipePsmReviewEntry, ...] = Field(default_factory=tuple)
    peptide_evidence: tuple[FragpipePeptideReviewEntry, ...] = Field(
        default_factory=tuple
    )
    peptide_rows: tuple[FragpipePeptideReviewEntry, ...] = Field(default_factory=tuple)
    protein_references: tuple[FragpipeProteinReviewEntry, ...] = Field(
        default_factory=tuple
    )
    protein_rows: tuple[FragpipeProteinReviewEntry, ...] = Field(default_factory=tuple)
    open_search_evidence: tuple[FragpipeOpenSearchEvidenceEntry, ...] = Field(
        default_factory=tuple
    )
    protein_quantity_rows: tuple[FragpipeProteinQuantityEntry, ...] = Field(
        default_factory=tuple
    )
    rejected_evidence_rows: tuple[RejectedEvidenceTableEntry, ...] = Field(
        default_factory=tuple
    )
    summary: FragpipeImportSummary


__all__ = [
    "FragpipeCanonicalPsmEntry",
    "FragpipeImportReport",
    "FragpipeImportSummary",
    "FragpipeOpenSearchEvidenceEntry",
    "FragpipePeptideReviewEntry",
    "FragpipeProteinQuantityEntry",
    "FragpipeProteinReviewEntry",
    "FragpipePsmReviewEntry",
]
