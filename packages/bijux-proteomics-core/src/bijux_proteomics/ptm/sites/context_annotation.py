# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM site-context annotation surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.ptm.contracts import PtmSiteEntry
from bijux_proteomics.sequences.protein_region_context_models import (
    ProteinRegionContextColumnMapping,
    ProteinRegionContextRecord,
    ProteinSiteRegionReference,
)
from bijux_proteomics.sequences.protein_region_context_workflows import (
    build_protein_site_region_context_report,
    parse_protein_region_context_tsv,
)
from bijux_proteomics_foundation import JsonModel


class PtmSiteContextColumnMapping(JsonModel):
    """Column mapping from a PTM site-context table into owned context fields."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    start: str = Field(..., min_length=1)
    end: str = Field(..., min_length=1)
    domain_name: str | None = None
    disorder_region: str | None = None
    transmembrane_region: str | None = None
    active_site_label: str | None = None
    motif_name: str | None = None
    conservation_score: str | None = None
    source_name: str | None = None
    source_accession: str | None = None


class PtmSiteContextValidationIssue(JsonModel):
    """One PTM site-context validation issue."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=2)


class RejectedPtmSiteContextRow(JsonModel):
    """One rejected PTM site-context row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[PtmSiteContextValidationIssue, ...] = Field(default_factory=tuple)


class PtmSiteContextRecord(JsonModel):
    """One normalized PTM site-context record over a protein region."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    start: int = Field(..., ge=1)
    end: int = Field(..., ge=1)
    domain_name: str | None = None
    disorder_region: str | None = None
    transmembrane_region: str | None = None
    active_site_label: str | None = None
    motif_name: str | None = None
    conservation_score: float | None = Field(default=None, ge=0.0, le=1.0)
    source_name: str | None = None
    source_accession: str | None = None


class PtmSiteContextImportSummary(JsonModel):
    """Stable summary over one PTM site-context import pass."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_protein_ref_count: int = Field(..., ge=0)
    domain_record_count: int = Field(..., ge=0)
    disorder_record_count: int = Field(..., ge=0)
    transmembrane_record_count: int = Field(..., ge=0)
    active_site_record_count: int = Field(..., ge=0)
    motif_record_count: int = Field(..., ge=0)
    conservation_record_count: int = Field(..., ge=0)


class PtmSiteContextImportReport(JsonModel):
    """Governed PTM site-context import report."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[PtmSiteContextRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedPtmSiteContextRow, ...] = Field(default_factory=tuple)
    column_mapping: PtmSiteContextColumnMapping
    summary: PtmSiteContextImportSummary
    note: str = Field(..., min_length=1)


class PtmSiteContextStatus(StrEnum):
    """Whether one PTM site landed inside provided context annotations."""

    CONTEXT_ANNOTATED = "context_annotated"
    OUTSIDE_PROVIDED_ANNOTATIONS = "outside_provided_annotations"


class PtmSiteContextEntry(JsonModel):
    """One PTM site row with aggregated context annotations or explicit absence."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    ambiguous_site: bool = False
    shared_peptide_site: bool = False
    matched_context_record_count: int = Field(..., ge=0)
    context_status: PtmSiteContextStatus
    domain_names: tuple[str, ...] = Field(default_factory=tuple)
    disorder_regions: tuple[str, ...] = Field(default_factory=tuple)
    transmembrane_regions: tuple[str, ...] = Field(default_factory=tuple)
    active_site_labels: tuple[str, ...] = Field(default_factory=tuple)
    motif_names: tuple[str, ...] = Field(default_factory=tuple)
    conservation_scores: tuple[float, ...] = Field(default_factory=tuple)
    max_conservation_score: float | None = Field(default=None, ge=0.0, le=1.0)
    source_names: tuple[str, ...] = Field(default_factory=tuple)
    source_accessions: tuple[str, ...] = Field(default_factory=tuple)


class PtmSiteContextSummary(JsonModel):
    """Stable summary over PTM site-context mapping results."""

    model_config = ConfigDict(extra="forbid")

    site_count: int = Field(..., ge=0)
    context_annotated_site_count: int = Field(..., ge=0)
    outside_annotation_site_count: int = Field(..., ge=0)
    domain_annotated_site_count: int = Field(..., ge=0)
    disorder_annotated_site_count: int = Field(..., ge=0)
    transmembrane_annotated_site_count: int = Field(..., ge=0)
    active_site_annotated_site_count: int = Field(..., ge=0)
    motif_annotated_site_count: int = Field(..., ge=0)
    conservation_annotated_site_count: int = Field(..., ge=0)


class PtmSiteContextReport(JsonModel):
    """Owned PTM site-context report over one observed PTM site table."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PtmSiteContextEntry, ...] = Field(default_factory=tuple)
    summary: PtmSiteContextSummary
    note: str = Field(..., min_length=1)


def parse_ptm_site_context_tsv(
    path: Path,
    *,
    mapping: PtmSiteContextColumnMapping | None = None,
) -> PtmSiteContextImportReport:
    """Parse one PTM site-context TSV into owned normalized region records."""

    active_mapping = mapping or PtmSiteContextColumnMapping(
        protein_ref="protein_ref",
        start="start",
        end="end",
        domain_name="domain_name",
        disorder_region="disorder_region",
        transmembrane_region="transmembrane_region",
        active_site_label="active_site_label",
        motif_name="motif_name",
        conservation_score="conservation_score",
        source_name="source_name",
        source_accession="source_accession",
    )
    generic_report = parse_protein_region_context_tsv(
        path,
        mapping=ProteinRegionContextColumnMapping(
            protein_ref=active_mapping.protein_ref,
            start=active_mapping.start,
            end=active_mapping.end,
            domain_name=active_mapping.domain_name,
            signal_peptide=None,
            transmembrane_region=active_mapping.transmembrane_region,
            disorder_region=active_mapping.disorder_region,
            low_complexity_region=None,
            active_site_label=active_mapping.active_site_label,
            binding_region=None,
            motif_name=active_mapping.motif_name,
            conservation_score=active_mapping.conservation_score,
            source_name=active_mapping.source_name,
            source_accession=active_mapping.source_accession,
        ),
    )
    accepted_records = tuple(
        PtmSiteContextRecord(
            protein_ref=record.protein_ref,
            start=record.start,
            end=record.end,
            domain_name=record.domain_name,
            disorder_region=record.disorder_region,
            transmembrane_region=record.transmembrane_region,
            active_site_label=record.active_site_label,
            motif_name=record.motif_name,
            conservation_score=record.conservation_score,
            source_name=record.source_name,
            source_accession=record.source_accession,
        )
        for record in generic_report.accepted_records
    )
    return PtmSiteContextImportReport(
        total_rows=generic_report.total_rows,
        accepted_records=accepted_records,
        rejected_rows=tuple(
            RejectedPtmSiteContextRow(
                row_number=row.row_number,
                raw_fields=row.raw_fields,
                issues=tuple(
                    PtmSiteContextValidationIssue(
                        code=issue.code,
                        message=issue.message,
                        row_number=issue.row_number,
                    )
                    for issue in row.issues
                ),
            )
            for row in generic_report.rejected_rows
        ),
        column_mapping=active_mapping,
        summary=PtmSiteContextImportSummary(
            accepted_record_count=generic_report.summary.accepted_record_count,
            rejected_row_count=generic_report.summary.rejected_row_count,
            distinct_protein_ref_count=generic_report.summary.distinct_protein_ref_count,
            domain_record_count=generic_report.summary.domain_record_count,
            disorder_record_count=generic_report.summary.disorder_record_count,
            transmembrane_record_count=generic_report.summary.transmembrane_record_count,
            active_site_record_count=generic_report.summary.active_site_record_count,
            motif_record_count=generic_report.summary.motif_record_count,
            conservation_record_count=generic_report.summary.conservation_record_count,
        ),
        note=(
            "ptm site context import preserves protein-region annotations for domains, disorder, transmembrane spans, active sites, motifs, and conservation before observed-site mapping"
        ),
    )


def build_ptm_site_context_report(
    site_entries: tuple[PtmSiteEntry, ...],
    context_records: tuple[PtmSiteContextRecord, ...],
) -> PtmSiteContextReport:
    """Map provided protein-region context annotations onto observed PTM sites."""

    generic_report = build_protein_site_region_context_report(
        tuple(
            ProteinSiteRegionReference(
                site_key=site_entry.site_key,
                protein_ref=site_entry.protein_ref,
                position=site_entry.position,
            )
            for site_entry in site_entries
        ),
        tuple(
            ProteinRegionContextRecord(
                protein_ref=record.protein_ref,
                start=record.start,
                end=record.end,
                domain_name=record.domain_name,
                signal_peptide=None,
                transmembrane_region=record.transmembrane_region,
                disorder_region=record.disorder_region,
                low_complexity_region=None,
                active_site_label=record.active_site_label,
                binding_region=None,
                motif_name=record.motif_name,
                conservation_score=record.conservation_score,
                source_name=record.source_name,
                source_accession=record.source_accession,
            )
            for record in context_records
        ),
    )
    site_entry_by_key = {entry.site_key: entry for entry in site_entries}
    stable_entries = tuple(
        PtmSiteContextEntry(
            site_key=entry.site_key,
            protein_ref=entry.protein_ref,
            residue=site_entry_by_key[entry.site_key].residue,
            position=entry.position,
            modification_name=site_entry_by_key[entry.site_key].modification_name,
            ambiguous_site=site_entry_by_key[entry.site_key].ambiguous,
            shared_peptide_site=site_entry_by_key[entry.site_key].shared_peptide,
            matched_context_record_count=entry.matched_context_record_count,
            context_status=(
                PtmSiteContextStatus.CONTEXT_ANNOTATED
                if entry.context_status.value == "context_annotated"
                else PtmSiteContextStatus.OUTSIDE_PROVIDED_ANNOTATIONS
            ),
            domain_names=entry.domain_names,
            disorder_regions=entry.disorder_regions,
            transmembrane_regions=entry.transmembrane_regions,
            active_site_labels=entry.active_site_labels,
            motif_names=entry.motif_names,
            conservation_scores=entry.conservation_scores,
            max_conservation_score=entry.max_conservation_score,
            source_names=entry.source_names,
            source_accessions=entry.source_accessions,
        )
        for entry in generic_report.entries
    )
    return PtmSiteContextReport(
        entries=stable_entries,
        summary=PtmSiteContextSummary(
            site_count=generic_report.summary.site_count,
            context_annotated_site_count=generic_report.summary.context_annotated_site_count,
            outside_annotation_site_count=generic_report.summary.outside_annotation_site_count,
            domain_annotated_site_count=generic_report.summary.domain_annotated_site_count,
            disorder_annotated_site_count=generic_report.summary.disorder_annotated_site_count,
            transmembrane_annotated_site_count=generic_report.summary.transmembrane_annotated_site_count,
            active_site_annotated_site_count=generic_report.summary.active_site_annotated_site_count,
            motif_annotated_site_count=generic_report.summary.motif_annotated_site_count,
            conservation_annotated_site_count=generic_report.summary.conservation_annotated_site_count,
        ),
        note=(
            "ptm site context annotation preserves one row for every observed PTM site, keeps provided domain and region context when present, and marks sites outside the provided annotations explicitly"
        ),
    )


def render_ptm_site_context_summary_tsv(report: PtmSiteContextReport) -> str:
    """Render a compact PTM site-context summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "site_count",
            "context_annotated_site_count",
            "outside_annotation_site_count",
            "domain_annotated_site_count",
            "disorder_annotated_site_count",
            "transmembrane_annotated_site_count",
            "active_site_annotated_site_count",
            "motif_annotated_site_count",
            "conservation_annotated_site_count",
        )
    )
    writer.writerow(
        (
            report.summary.site_count,
            report.summary.context_annotated_site_count,
            report.summary.outside_annotation_site_count,
            report.summary.domain_annotated_site_count,
            report.summary.disorder_annotated_site_count,
            report.summary.transmembrane_annotated_site_count,
            report.summary.active_site_annotated_site_count,
            report.summary.motif_annotated_site_count,
            report.summary.conservation_annotated_site_count,
        )
    )
    return buffer.getvalue()


def render_ptm_site_context_tsv(report: PtmSiteContextReport) -> str:
    """Render PTM site-context rows as a stable TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "site_key",
            "protein_ref",
            "residue",
            "position",
            "modification_name",
            "ambiguous_site",
            "shared_peptide_site",
            "matched_context_record_count",
            "context_status",
            "domain_names",
            "disorder_regions",
            "transmembrane_regions",
            "active_site_labels",
            "motif_names",
            "conservation_scores",
            "max_conservation_score",
            "source_names",
            "source_accessions",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.site_key,
                entry.protein_ref,
                entry.residue,
                entry.position,
                entry.modification_name,
                str(entry.ambiguous_site).lower(),
                str(entry.shared_peptide_site).lower(),
                entry.matched_context_record_count,
                entry.context_status.value,
                ";".join(entry.domain_names),
                ";".join(entry.disorder_regions),
                ";".join(entry.transmembrane_regions),
                ";".join(entry.active_site_labels),
                ";".join(entry.motif_names),
                ";".join(f"{score:g}" for score in entry.conservation_scores),
                (
                    ""
                    if entry.max_conservation_score is None
                    else f"{entry.max_conservation_score:g}"
                ),
                ";".join(entry.source_names),
                ";".join(entry.source_accessions),
            )
        )
    return buffer.getvalue()


def export_ptm_site_context_summary_tsv(
    report: PtmSiteContextReport,
    path: Path,
) -> None:
    """Write PTM site-context summary to a stable TSV artifact."""

    write_output_table_tsv(path, render_ptm_site_context_summary_tsv(report))


def export_ptm_site_context_tsv(
    report: PtmSiteContextReport,
    path: Path,
) -> None:
    """Write PTM site-context rows to a stable TSV artifact."""

    write_output_table_tsv(path, render_ptm_site_context_tsv(report))
