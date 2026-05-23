# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM site-context annotation surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.ptm.contracts import PtmSiteEntry
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
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("PTM site context TSV must include a header row")
        _validate_required_columns(reader.fieldnames, active_mapping)

        accepted: list[PtmSiteContextRecord] = []
        rejected: list[RejectedPtmSiteContextRow] = []
        for row_number, row in enumerate(reader, start=2):
            raw_fields = {
                str(key): str(value or "")
                for key, value in row.items()
                if key is not None
            }
            issues: list[PtmSiteContextValidationIssue] = []

            protein_ref = raw_fields.get(active_mapping.protein_ref, "").strip()
            start_token = raw_fields.get(active_mapping.start, "").strip()
            end_token = raw_fields.get(active_mapping.end, "").strip()
            domain_name = _row_value(raw_fields, active_mapping.domain_name)
            disorder_region = _row_value(raw_fields, active_mapping.disorder_region)
            transmembrane_region = _row_value(
                raw_fields,
                active_mapping.transmembrane_region,
            )
            active_site_label = _row_value(raw_fields, active_mapping.active_site_label)
            motif_name = _row_value(raw_fields, active_mapping.motif_name)
            conservation_token = _row_value(raw_fields, active_mapping.conservation_score)

            if not protein_ref:
                issues.append(
                    _row_issue(
                        "missing_protein_ref",
                        "missing protein reference",
                        row_number,
                    )
                )
            if not any(
                value is not None
                for value in (
                    domain_name,
                    disorder_region,
                    transmembrane_region,
                    active_site_label,
                    motif_name,
                    conservation_token,
                )
            ):
                issues.append(
                    _row_issue(
                        "missing_context_fields",
                        "site-context row requires at least one annotation field",
                        row_number,
                    )
                )

            start: int | None = None
            end: int | None = None
            try:
                start = int(start_token)
                if start < 1:
                    raise ValueError
            except ValueError:
                issues.append(
                    _row_issue(
                        "invalid_start",
                        "start must be a positive integer",
                        row_number,
                    )
                )
            try:
                end = int(end_token)
                if end < 1:
                    raise ValueError
            except ValueError:
                issues.append(
                    _row_issue(
                        "invalid_end",
                        "end must be a positive integer",
                        row_number,
                    )
                )
            if start is not None and end is not None and end < start:
                issues.append(
                    _row_issue(
                        "inverted_interval",
                        "end must be greater than or equal to start",
                        row_number,
                    )
                )

            conservation_score: float | None = None
            if conservation_token is not None:
                try:
                    conservation_score = float(conservation_token)
                    if conservation_score < 0.0 or conservation_score > 1.0:
                        raise ValueError
                except ValueError:
                    issues.append(
                        _row_issue(
                            "invalid_conservation_score",
                            "conservation score must be between 0.0 and 1.0",
                            row_number,
                        )
                    )

            if issues:
                rejected.append(
                    RejectedPtmSiteContextRow(
                        row_number=row_number,
                        raw_fields=raw_fields,
                        issues=tuple(issues),
                    )
                )
                continue

            accepted.append(
                PtmSiteContextRecord(
                    protein_ref=protein_ref,
                    start=start,
                    end=end,
                    domain_name=domain_name,
                    disorder_region=disorder_region,
                    transmembrane_region=transmembrane_region,
                    active_site_label=active_site_label,
                    motif_name=motif_name,
                    conservation_score=conservation_score,
                    source_name=_row_value(raw_fields, active_mapping.source_name),
                    source_accession=_row_value(
                        raw_fields,
                        active_mapping.source_accession,
                    ),
                )
            )

    accepted_records = tuple(
        sorted(
            accepted,
            key=lambda record: (
                record.protein_ref,
                record.start,
                record.end,
                record.domain_name or "",
                record.motif_name or "",
            ),
        )
    )
    return PtmSiteContextImportReport(
        total_rows=len(accepted_records) + len(rejected),
        accepted_records=accepted_records,
        rejected_rows=tuple(rejected),
        column_mapping=active_mapping,
        summary=PtmSiteContextImportSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected),
            distinct_protein_ref_count=len(
                {record.protein_ref for record in accepted_records}
            ),
            domain_record_count=sum(
                1 for record in accepted_records if record.domain_name is not None
            ),
            disorder_record_count=sum(
                1 for record in accepted_records if record.disorder_region is not None
            ),
            transmembrane_record_count=sum(
                1
                for record in accepted_records
                if record.transmembrane_region is not None
            ),
            active_site_record_count=sum(
                1
                for record in accepted_records
                if record.active_site_label is not None
            ),
            motif_record_count=sum(
                1 for record in accepted_records if record.motif_name is not None
            ),
            conservation_record_count=sum(
                1
                for record in accepted_records
                if record.conservation_score is not None
            ),
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

    context_by_protein: dict[str, list[PtmSiteContextRecord]] = {}
    for record in context_records:
        context_by_protein.setdefault(record.protein_ref, []).append(record)

    entries: list[PtmSiteContextEntry] = []
    for site_entry in site_entries:
        matched_records = tuple(
            record
            for record in context_by_protein.get(site_entry.protein_ref, ())
            if record.start <= site_entry.position <= record.end
        )
        domain_names = _unique_sorted(
            record.domain_name
            for record in matched_records
            if record.domain_name is not None
        )
        disorder_regions = _unique_sorted(
            record.disorder_region
            for record in matched_records
            if record.disorder_region is not None
        )
        transmembrane_regions = _unique_sorted(
            record.transmembrane_region
            for record in matched_records
            if record.transmembrane_region is not None
        )
        active_site_labels = _unique_sorted(
            record.active_site_label
            for record in matched_records
            if record.active_site_label is not None
        )
        motif_names = _unique_sorted(
            record.motif_name
            for record in matched_records
            if record.motif_name is not None
        )
        conservation_scores = tuple(
            sorted(
                {
                    round(record.conservation_score, 6)
                    for record in matched_records
                    if record.conservation_score is not None
                }
            )
        )
        source_names = _unique_sorted(
            record.source_name
            for record in matched_records
            if record.source_name is not None
        )
        source_accessions = _unique_sorted(
            record.source_accession
            for record in matched_records
            if record.source_accession is not None
        )
        context_status = (
            PtmSiteContextStatus.CONTEXT_ANNOTATED
            if matched_records
            else PtmSiteContextStatus.OUTSIDE_PROVIDED_ANNOTATIONS
        )
        entries.append(
            PtmSiteContextEntry(
                site_key=site_entry.site_key,
                protein_ref=site_entry.protein_ref,
                residue=site_entry.residue,
                position=site_entry.position,
                modification_name=site_entry.modification_name,
                ambiguous_site=site_entry.ambiguous,
                shared_peptide_site=site_entry.shared_peptide,
                matched_context_record_count=len(matched_records),
                context_status=context_status,
                domain_names=domain_names,
                disorder_regions=disorder_regions,
                transmembrane_regions=transmembrane_regions,
                active_site_labels=active_site_labels,
                motif_names=motif_names,
                conservation_scores=conservation_scores,
                max_conservation_score=(
                    None if not conservation_scores else conservation_scores[-1]
                ),
                source_names=source_names,
                source_accessions=source_accessions,
            )
        )

    stable_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.protein_ref,
                entry.position,
                entry.modification_name,
                entry.site_key,
            ),
        )
    )
    return PtmSiteContextReport(
        entries=stable_entries,
        summary=PtmSiteContextSummary(
            site_count=len(stable_entries),
            context_annotated_site_count=sum(
                1
                for entry in stable_entries
                if entry.context_status is PtmSiteContextStatus.CONTEXT_ANNOTATED
            ),
            outside_annotation_site_count=sum(
                1
                for entry in stable_entries
                if entry.context_status
                is PtmSiteContextStatus.OUTSIDE_PROVIDED_ANNOTATIONS
            ),
            domain_annotated_site_count=sum(
                1 for entry in stable_entries if entry.domain_names
            ),
            disorder_annotated_site_count=sum(
                1 for entry in stable_entries if entry.disorder_regions
            ),
            transmembrane_annotated_site_count=sum(
                1 for entry in stable_entries if entry.transmembrane_regions
            ),
            active_site_annotated_site_count=sum(
                1 for entry in stable_entries if entry.active_site_labels
            ),
            motif_annotated_site_count=sum(
                1 for entry in stable_entries if entry.motif_names
            ),
            conservation_annotated_site_count=sum(
                1 for entry in stable_entries if entry.conservation_scores
            ),
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

    path.write_text(render_ptm_site_context_summary_tsv(report), encoding="utf-8")


def export_ptm_site_context_tsv(
    report: PtmSiteContextReport,
    path: Path,
) -> None:
    """Write PTM site-context rows to a stable TSV artifact."""

    path.write_text(render_ptm_site_context_tsv(report), encoding="utf-8")


def _row_issue(
    code: str,
    message: str,
    row_number: int,
) -> PtmSiteContextValidationIssue:
    return PtmSiteContextValidationIssue(
        code=code,
        message=message,
        row_number=row_number,
    )


def _row_value(raw_fields: dict[str, str], column: str | None) -> str | None:
    if column is None:
        return None
    value = raw_fields.get(column, "").strip()
    return value or None


def _validate_required_columns(
    fieldnames: list[str],
    mapping: PtmSiteContextColumnMapping,
) -> None:
    required = (
        mapping.protein_ref,
        mapping.start,
        mapping.end,
    )
    for column in required:
        if column not in fieldnames:
            raise ValueError(f"missing required PTM site context column {column!r}")


def _unique_sorted(
    values: list[str] | tuple[str, ...] | set[str] | object,
) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))
