# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM reporting surfaces."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm.contracts import (
    PtmEvidenceRecord,
    PtmSiteEntry,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
)
from bijux_proteomics_foundation import JsonModel


class PtmReportPeptideEntry(JsonModel):
    """One PTM peptide observation carried into a report bundle."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    localized_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    sequence: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    score: float
    q_value: float | None = Field(default=None, ge=0.0)
    localization_score: float = Field(..., ge=0.0)
    localization_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    modification_names: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel


class PtmReportSummary(JsonModel):
    """Compact summary over the current PTM report bundle."""

    model_config = ConfigDict(extra="forbid")

    accepted_evidence_count: int = Field(..., ge=0)
    peptide_entry_count: int = Field(..., ge=0)
    site_row_count: int = Field(..., ge=0)
    ambiguous_site_count: int = Field(..., ge=0)
    modified_peptide_count: int = Field(..., ge=0)


class PtmReportBundle(JsonModel):
    """Owned PTM report bundle over evidence-derived peptide and site surfaces."""

    model_config = ConfigDict(extra="forbid")

    peptide_entries: tuple[PtmReportPeptideEntry, ...] = Field(default_factory=tuple)
    site_table: tuple[PtmSiteEntry, ...] = Field(default_factory=tuple)
    summary: PtmReportSummary
    note: str = Field(..., min_length=1)


def build_ptm_report_bundle(
    records: tuple[PtmEvidenceRecord, ...],
    *,
    protein_sequences: dict[str, str],
) -> PtmReportBundle:
    """Build the core PTM report bundle from evidence rows and protein context."""

    peptide_entries = tuple(
        sorted(
            (
                PtmReportPeptideEntry(
                    spectrum_id=record.spectrum_id,
                    sample_id=record.sample_id,
                    localized_peptide=record.localized_peptide,
                    canonical_peptide=record.canonical_peptide,
                    sequence=record.sequence,
                    charge=record.charge,
                    score=record.score,
                    q_value=record.q_value,
                    localization_score=record.localization_score,
                    localization_probability=record.localization_probability,
                    protein_refs=record.protein_refs,
                    modification_names=record.modification_names,
                    target_decoy_label=record.target_decoy_label,
                )
                for record in records
            ),
            key=lambda entry: (
                entry.protein_refs[0] if entry.protein_refs else "",
                entry.localized_peptide,
                entry.spectrum_id,
                entry.sample_id or "",
            ),
        )
    )
    mappings = map_ptm_evidence_to_protein_sites(
        records,
        protein_sequences=protein_sequences,
    )
    site_table = build_ptm_site_table(mappings)
    return PtmReportBundle(
        peptide_entries=peptide_entries,
        site_table=site_table,
        summary=PtmReportSummary(
            accepted_evidence_count=len(records),
            peptide_entry_count=len(peptide_entries),
            site_row_count=len(site_table),
            ambiguous_site_count=sum(1 for entry in site_table if entry.ambiguous),
            modified_peptide_count=len(
                {
                    entry.localized_peptide
                    for entry in peptide_entries
                }
            ),
        ),
        note=(
            "ptm reporting starts from governed peptide observations and protein-mapped site rows before higher-level localization, quantification, and differential sections are added"
        ),
    )
