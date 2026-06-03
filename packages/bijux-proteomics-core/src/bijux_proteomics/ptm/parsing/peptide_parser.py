# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM peptide parsing and site-local review surfaces."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import (
    ModificationPosition,
    ModificationRegistryDocument,
    ParsedModifiedPeptide,
    parse_modified_peptide,
)
from bijux_proteomics.chemistry.contracts import AppliedModification
from bijux_proteomics_foundation import JsonModel


class PtmPeptideColumnMapping(JsonModel):
    """Column mapping from a peptide-level PTM table into owned parser fields."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    protein_ref: str | None = None
    peptide_start_position: str | None = None
    sample_id: str | None = None
    spectrum_id: str | None = None


class PtmPeptideValidationIssue(JsonModel):
    """One PTM peptide parsing validation issue."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=2)


class RejectedPtmPeptideRow(JsonModel):
    """One rejected PTM peptide input row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[PtmPeptideValidationIssue, ...] = Field(default_factory=tuple)


class PtmPeptideSiteEntry(JsonModel):
    """One PTM site extracted from a modified peptide."""

    model_config = ConfigDict(extra="forbid")

    modification_name: str = Field(..., min_length=1)
    controlled_id: str | None = None
    residue: str = Field(..., min_length=1, max_length=1)
    peptide_position: int = Field(..., ge=1)
    protein_position: int | None = Field(default=None, ge=1)
    site_kind: ModificationPosition


class PtmParsedPeptideRecord(JsonModel):
    """One parsed PTM peptide with explicit per-site localization."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str | None = None
    sample_id: str | None = None
    localized_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    sequence: str = Field(..., min_length=1)
    protein_ref: str | None = None
    peptide_start_position: int | None = Field(default=None, ge=1)
    modification_names: tuple[str, ...] = Field(default_factory=tuple)
    sites: tuple[PtmPeptideSiteEntry, ...] = Field(default_factory=tuple)


class PtmPeptideParseSummary(JsonModel):
    """Stable summary over one PTM peptide parsing pass."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    parsed_site_count: int = Field(..., ge=0)
    protein_mapped_site_count: int = Field(..., ge=0)
    multi_modified_record_count: int = Field(..., ge=0)


class PtmPeptideParseReport(JsonModel):
    """Governed PTM peptide parsing report."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[PtmParsedPeptideRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedPtmPeptideRow, ...] = Field(default_factory=tuple)
    column_mapping: PtmPeptideColumnMapping
    summary: PtmPeptideParseSummary
    note: str = Field(..., min_length=1)


def parse_ptm_peptide(
    localized_peptide: str,
    *,
    protein_ref: str | None = None,
    peptide_start_position: int | None = None,
    sample_id: str | None = None,
    spectrum_id: str | None = None,
    registry: ModificationRegistryDocument | None = None,
) -> PtmParsedPeptideRecord:
    """Parse one modified peptide into PTM-owned site records."""

    if peptide_start_position is not None and peptide_start_position < 1:
        raise ValueError("peptide start position must be at least 1")
    if peptide_start_position is not None and protein_ref is None:
        raise ValueError("protein position mapping requires a protein reference")
    parsed = parse_modified_peptide(localized_peptide, registry=registry)
    sites = tuple(
        _build_ptm_site_entry(
            modification=modification,
            parsed=parsed,
            peptide_start_position=peptide_start_position,
        )
        for modification in parsed.modifications
    )
    return PtmParsedPeptideRecord(
        spectrum_id=_normalized_text(spectrum_id),
        sample_id=_normalized_text(sample_id),
        localized_peptide=localized_peptide.strip(),
        canonical_peptide=parsed.canonical_notation,
        sequence=parsed.sequence,
        protein_ref=_normalized_text(protein_ref),
        peptide_start_position=peptide_start_position,
        modification_names=tuple(site.modification_name for site in sites),
        sites=sites,
    )


def parse_ptm_peptide_tsv(
    path: Path,
    *,
    mapping: PtmPeptideColumnMapping | None = None,
    registry: ModificationRegistryDocument | None = None,
) -> PtmPeptideParseReport:
    """Parse one PTM peptide table into owned peptide and site records."""

    active_mapping = mapping or PtmPeptideColumnMapping(
        peptide="peptide",
        protein_ref="protein_ref",
        peptide_start_position="peptide_start_position",
        sample_id="sample_id",
        spectrum_id="spectrum_id",
    )
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("PTM peptide TSV must include a header row")
        if active_mapping.peptide not in reader.fieldnames:
            raise ValueError(
                f"missing required PTM peptide column {active_mapping.peptide!r}"
            )

        accepted: list[PtmParsedPeptideRecord] = []
        rejected: list[RejectedPtmPeptideRow] = []
        for row_number, row in enumerate(reader, start=2):
            raw_fields = {
                str(key): str(value or "")
                for key, value in row.items()
                if key is not None
            }
            issues: list[PtmPeptideValidationIssue] = []
            localized_peptide = raw_fields.get(active_mapping.peptide, "").strip()
            protein_ref = _row_value(raw_fields, active_mapping.protein_ref)
            sample_id = _row_value(raw_fields, active_mapping.sample_id)
            spectrum_id = _row_value(raw_fields, active_mapping.spectrum_id)
            if not localized_peptide:
                issues.append(
                    _row_issue("missing_peptide", "missing PTM peptide", row_number)
                )

            peptide_start_position: int | None = None
            if active_mapping.peptide_start_position is not None:
                start_token = raw_fields.get(active_mapping.peptide_start_position, "").strip()
                if start_token:
                    try:
                        peptide_start_position = int(start_token)
                        if peptide_start_position < 1:
                            raise ValueError
                    except ValueError:
                        issues.append(
                            _row_issue(
                                "invalid_peptide_start_position",
                                "invalid peptide start position",
                                row_number,
                            )
                        )
            if peptide_start_position is not None and protein_ref is None:
                issues.append(
                    _row_issue(
                        "missing_protein_ref",
                        "protein position mapping requires a protein reference",
                        row_number,
                    )
                )
            if issues:
                rejected.append(
                    RejectedPtmPeptideRow(
                        row_number=row_number,
                        raw_fields=raw_fields,
                        issues=tuple(issues),
                    )
                )
                continue
            try:
                accepted.append(
                    parse_ptm_peptide(
                        localized_peptide,
                        protein_ref=protein_ref,
                        peptide_start_position=peptide_start_position,
                        sample_id=sample_id,
                        spectrum_id=spectrum_id,
                        registry=registry,
                    )
                )
            except ValueError as exc:
                rejected.append(
                    RejectedPtmPeptideRow(
                        row_number=row_number,
                        raw_fields=raw_fields,
                        issues=(
                            _row_issue(
                                "invalid_ptm_peptide",
                                str(exc),
                                row_number,
                            ),
                        ),
                    )
                )
    accepted_records = tuple(
        sorted(
            accepted,
            key=lambda record: (
                record.protein_ref or "",
                record.peptide_start_position or 0,
                record.localized_peptide,
                record.spectrum_id or "",
                record.sample_id or "",
            ),
        )
    )
    return PtmPeptideParseReport(
        total_rows=len(accepted_records) + len(rejected),
        accepted_records=accepted_records,
        rejected_rows=tuple(rejected),
        column_mapping=active_mapping,
        summary=PtmPeptideParseSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected),
            parsed_site_count=sum(len(record.sites) for record in accepted_records),
            protein_mapped_site_count=sum(
                1
                for record in accepted_records
                for site in record.sites
                if site.protein_position is not None
            ),
            multi_modified_record_count=sum(
                1 for record in accepted_records if len(record.sites) > 1
            ),
        ),
        note=(
            "ptm peptide parsing keeps modification type, modified residue, peptide-local position, and optional direct protein-position context explicit before downstream protein-site aggregation"
        ),
    )


def render_ptm_peptide_summary_tsv(report: PtmPeptideParseReport) -> str:
    """Render compact PTM peptide parser summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "accepted_record_count",
            "rejected_row_count",
            "parsed_site_count",
            "protein_mapped_site_count",
            "multi_modified_record_count",
        ]
    )
    writer.writerow(
        [
            report.summary.accepted_record_count,
            report.summary.rejected_row_count,
            report.summary.parsed_site_count,
            report.summary.protein_mapped_site_count,
            report.summary.multi_modified_record_count,
        ]
    )
    return buffer.getvalue()


def render_ptm_peptide_record_tsv(report: PtmPeptideParseReport) -> str:
    """Render accepted PTM peptide records as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "localized_peptide",
            "canonical_peptide",
            "sequence",
            "protein_ref",
            "peptide_start_position",
            "sample_id",
            "spectrum_id",
            "modification_names",
            "site_count",
        ]
    )
    for record in report.accepted_records:
        writer.writerow(
            [
                record.localized_peptide,
                record.canonical_peptide,
                record.sequence,
                record.protein_ref or "",
                record.peptide_start_position or "",
                record.sample_id or "",
                record.spectrum_id or "",
                ";".join(record.modification_names),
                len(record.sites),
            ]
        )
    return buffer.getvalue()


def render_ptm_peptide_site_tsv(report: PtmPeptideParseReport) -> str:
    """Render PTM peptide site rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "localized_peptide",
            "canonical_peptide",
            "protein_ref",
            "sample_id",
            "spectrum_id",
            "modification_name",
            "controlled_id",
            "residue",
            "peptide_position",
            "protein_position",
            "site_kind",
        ]
    )
    for record in report.accepted_records:
        for site in record.sites:
            writer.writerow(
                [
                    record.localized_peptide,
                    record.canonical_peptide,
                    record.protein_ref or "",
                    record.sample_id or "",
                    record.spectrum_id or "",
                    site.modification_name,
                    site.controlled_id or "",
                    site.residue,
                    site.peptide_position,
                    site.protein_position or "",
                    site.site_kind.value,
                ]
            )
    return buffer.getvalue()


def render_ptm_peptide_rejected_tsv(report: PtmPeptideParseReport) -> str:
    """Render rejected PTM peptide rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(["row_number", "issues", "raw_fields"])
    for row in report.rejected_rows:
        writer.writerow(
            [
                row.row_number,
                ";".join(issue.code for issue in row.issues),
                ";".join(
                    f"{key}={value}" for key, value in sorted(row.raw_fields.items())
                ),
            ]
        )
    return buffer.getvalue()


def _build_ptm_site_entry(
    *,
    modification: AppliedModification,
    parsed: ParsedModifiedPeptide,
    peptide_start_position: int | None,
) -> PtmPeptideSiteEntry:
    peptide_position = _peptide_position_for_modification(modification, parsed.sequence)
    protein_position = (
        peptide_start_position + peptide_position - 1
        if peptide_start_position is not None
        else None
    )
    return PtmPeptideSiteEntry(
        modification_name=modification.name,
        controlled_id=modification.controlled_id,
        residue=parsed.sequence[peptide_position - 1],
        peptide_position=peptide_position,
        protein_position=protein_position,
        site_kind=modification.site,
    )


def _peptide_position_for_modification(
    modification: AppliedModification,
    sequence: str,
) -> int:
    if modification.site is ModificationPosition.ANYWHERE:
        if modification.site_index is None:
            raise ValueError("residue-local PTM modification is missing a peptide position")
        return int(modification.site_index)
    if modification.site in (
        ModificationPosition.PEPTIDE_N_TERM,
        ModificationPosition.PROTEIN_N_TERM,
    ):
        return 1
    if modification.site in (
        ModificationPosition.PEPTIDE_C_TERM,
        ModificationPosition.PROTEIN_C_TERM,
    ):
        return len(sequence)
    raise ValueError(f"unsupported PTM site kind {modification.site!r}")


def _row_issue(code: str, message: str, row_number: int) -> PtmPeptideValidationIssue:
    return PtmPeptideValidationIssue(
        code=code,
        message=message,
        row_number=row_number,
    )


def _row_value(raw_fields: dict[str, str], column_name: str | None) -> str | None:
    if column_name is None:
        return None
    return _normalized_text(raw_fields.get(column_name, ""))


def _normalized_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
