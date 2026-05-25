# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM ortholog-site conservation surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.io.stable_outputs import sort_rows_by_fields
from bijux_proteomics.ptm.contracts import PtmSiteEntry
from bijux_proteomics_foundation import JsonModel


class PtmOrthologSiteColumnMapping(JsonModel):
    """Column mapping from one ortholog-site table into owned PTM fields."""

    model_config = ConfigDict(extra="forbid")

    source_species: str = Field(..., min_length=1)
    source_protein_ref: str = Field(..., min_length=1)
    source_residue: str = Field(..., min_length=1)
    source_position: str = Field(..., min_length=1)
    source_modification_name: str = Field(..., min_length=1)
    target_species: str = Field(..., min_length=1)
    target_protein_ref: str | None = None
    target_residue: str | None = None
    target_position: str | None = None
    target_modification_name: str | None = None
    evidence: str | None = None
    source_name: str | None = None
    source_accession: str | None = None


class PtmOrthologSiteValidationIssue(JsonModel):
    """One PTM ortholog-site validation issue."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=2)


class RejectedPtmOrthologSiteRow(JsonModel):
    """One rejected PTM ortholog-site row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[PtmOrthologSiteValidationIssue, ...] = Field(default_factory=tuple)


class PtmOrthologSiteRecord(JsonModel):
    """One normalized PTM ortholog-site row."""

    model_config = ConfigDict(extra="forbid")

    source_species: str = Field(..., min_length=1)
    source_protein_ref: str = Field(..., min_length=1)
    source_residue: str = Field(..., min_length=1, max_length=1)
    source_position: int = Field(..., ge=1)
    source_modification_name: str = Field(..., min_length=1)
    target_species: str = Field(..., min_length=1)
    target_protein_ref: str | None = None
    target_residue: str | None = Field(default=None, min_length=1, max_length=1)
    target_position: int | None = Field(default=None, ge=1)
    target_modification_name: str | None = None
    evidence: str | None = None
    source_name: str | None = None
    source_accession: str | None = None


class PtmOrthologSiteImportSummary(JsonModel):
    """Stable summary over one PTM ortholog-site import pass."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    source_site_count: int = Field(..., ge=0)
    target_site_count: int = Field(..., ge=0)
    missing_target_count: int = Field(..., ge=0)


class PtmOrthologSiteImportReport(JsonModel):
    """Governed PTM ortholog-site import report."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[PtmOrthologSiteRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedPtmOrthologSiteRow, ...] = Field(default_factory=tuple)
    column_mapping: PtmOrthologSiteColumnMapping
    summary: PtmOrthologSiteImportSummary
    note: str = Field(..., min_length=1)


class PtmOrthologConservationStatus(StrEnum):
    """Stable ortholog-conservation status for one observed PTM site."""

    CONSERVED = "conserved"
    SHIFTED = "shifted"
    MISSING = "missing"
    UNMAPPED = "unmapped"


class PtmOrthologConservationEntry(JsonModel):
    """One observed PTM site annotated with ortholog conservation context."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    status: PtmOrthologConservationStatus
    source_species: str = Field(..., min_length=1)
    target_species: str = Field(..., min_length=1)
    ortholog_target_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    ortholog_target_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    ortholog_target_positions: tuple[int, ...] = Field(default_factory=tuple)
    evidence_labels: tuple[str, ...] = Field(default_factory=tuple)
    source_names: tuple[str, ...] = Field(default_factory=tuple)
    source_accessions: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class PtmOrthologConservationSummary(JsonModel):
    """Stable summary over one PTM ortholog-conservation pass."""

    model_config = ConfigDict(extra="forbid")

    observed_site_count: int = Field(..., ge=0)
    conserved_site_count: int = Field(..., ge=0)
    shifted_site_count: int = Field(..., ge=0)
    missing_site_count: int = Field(..., ge=0)
    unmapped_site_count: int = Field(..., ge=0)


class PtmOrthologConservationReport(JsonModel):
    """Owned report over PTM site conservation across an ortholog species pair."""

    model_config = ConfigDict(extra="forbid")

    source_species: str = Field(..., min_length=1)
    target_species: str = Field(..., min_length=1)
    entries: tuple[PtmOrthologConservationEntry, ...] = Field(default_factory=tuple)
    summary: PtmOrthologConservationSummary
    note: str = Field(..., min_length=1)


def parse_ptm_ortholog_site_tsv(
    path: Path,
    *,
    mapping: PtmOrthologSiteColumnMapping | None = None,
) -> PtmOrthologSiteImportReport:
    """Parse one PTM ortholog-site table into owned normalized rows."""

    active_mapping = mapping or PtmOrthologSiteColumnMapping(
        source_species="source_species",
        source_protein_ref="source_protein_ref",
        source_residue="source_residue",
        source_position="source_position",
        source_modification_name="source_modification_name",
        target_species="target_species",
        target_protein_ref="target_protein_ref",
        target_residue="target_residue",
        target_position="target_position",
        target_modification_name="target_modification_name",
        evidence="evidence",
        source_name="source_name",
        source_accession="source_accession",
    )
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("PTM ortholog-site TSV must include a header row")
        _validate_required_columns(reader.fieldnames, active_mapping)

        accepted_records: list[PtmOrthologSiteRecord] = []
        rejected_rows: list[RejectedPtmOrthologSiteRow] = []
        seen_rows: set[
            tuple[
                str,
                str,
                str,
                int,
                str,
                str,
                str | None,
                str | None,
                int | None,
                str | None,
            ]
        ] = set()

        for row_number, row in enumerate(reader, start=2):
            raw_fields = {
                str(key): str(value or "")
                for key, value in row.items()
                if key is not None
            }
            issues: list[PtmOrthologSiteValidationIssue] = []

            source_species = raw_fields.get(active_mapping.source_species, "").strip()
            source_protein_ref = raw_fields.get(
                active_mapping.source_protein_ref,
                "",
            ).strip()
            source_residue = raw_fields.get(active_mapping.source_residue, "").strip()
            source_position_token = raw_fields.get(
                active_mapping.source_position,
                "",
            ).strip()
            source_modification_name = raw_fields.get(
                active_mapping.source_modification_name,
                "",
            ).strip()
            target_species = raw_fields.get(active_mapping.target_species, "").strip()
            target_protein_ref = _optional_row_value(
                raw_fields,
                active_mapping.target_protein_ref,
            )
            target_residue = _optional_row_value(raw_fields, active_mapping.target_residue)
            target_position_token = _optional_row_value(
                raw_fields,
                active_mapping.target_position,
            )
            target_modification_name = _optional_row_value(
                raw_fields,
                active_mapping.target_modification_name,
            )

            if not source_species:
                issues.append(
                    _row_issue("missing_source_species", "missing source species", row_number)
                )
            if not source_protein_ref:
                issues.append(
                    _row_issue(
                        "missing_source_protein_ref",
                        "missing source protein reference",
                        row_number,
                    )
                )
            if len(source_residue) != 1:
                issues.append(
                    _row_issue(
                        "invalid_source_residue",
                        "source residue must contain exactly one amino-acid character",
                        row_number,
                    )
                )
            if not source_modification_name:
                issues.append(
                    _row_issue(
                        "missing_source_modification_name",
                        "missing source modification name",
                        row_number,
                    )
                )
            if not target_species:
                issues.append(
                    _row_issue("missing_target_species", "missing target species", row_number)
                )
            try:
                source_position = int(source_position_token)
                if source_position < 1:
                    raise ValueError
            except ValueError:
                issues.append(
                    _row_issue(
                        "invalid_source_position",
                        "source position must be a positive integer",
                        row_number,
                    )
                )
                source_position = 0

            target_position: int | None = None
            if target_position_token is not None:
                try:
                    target_position = int(target_position_token)
                    if target_position < 1:
                        raise ValueError
                except ValueError:
                    issues.append(
                        _row_issue(
                            "invalid_target_position",
                            "target position must be a positive integer when provided",
                            row_number,
                        )
                    )

            if target_residue is not None and len(target_residue) != 1:
                issues.append(
                    _row_issue(
                        "invalid_target_residue",
                        "target residue must contain exactly one amino-acid character when provided",
                        row_number,
                    )
                )

            has_any_target_site_field = any(
                value is not None
                for value in (
                    target_protein_ref,
                    target_residue,
                    target_position,
                    target_modification_name,
                )
            )
            if has_any_target_site_field and any(
                value is None
                for value in (
                    target_protein_ref,
                    target_residue,
                    target_position,
                    target_modification_name,
                )
            ):
                issues.append(
                    _row_issue(
                        "partial_target_site",
                        "target protein, residue, position, and modification must all be present when any target-site field is provided",
                        row_number,
                    )
                )

            if issues:
                rejected_rows.append(
                    RejectedPtmOrthologSiteRow(
                        row_number=row_number,
                        raw_fields=raw_fields,
                        issues=tuple(issues),
                    )
                )
                continue

            record = PtmOrthologSiteRecord(
                source_species=source_species,
                source_protein_ref=source_protein_ref,
                source_residue=source_residue,
                source_position=source_position,
                source_modification_name=source_modification_name,
                target_species=target_species,
                target_protein_ref=target_protein_ref,
                target_residue=target_residue,
                target_position=target_position,
                target_modification_name=target_modification_name,
                evidence=_optional_row_value(raw_fields, active_mapping.evidence),
                source_name=_optional_row_value(raw_fields, active_mapping.source_name),
                source_accession=_optional_row_value(
                    raw_fields,
                    active_mapping.source_accession,
                ),
            )
            record_key = (
                record.source_species,
                record.source_protein_ref,
                record.source_residue,
                record.source_position,
                record.source_modification_name,
                record.target_species,
                record.target_protein_ref,
                record.target_residue,
                record.target_position,
                record.target_modification_name,
            )
            if record_key in seen_rows:
                rejected_rows.append(
                    RejectedPtmOrthologSiteRow(
                        row_number=row_number,
                        raw_fields=raw_fields,
                        issues=(
                            _row_issue(
                                "duplicate_ortholog_site",
                                "duplicate PTM ortholog-site relationship",
                                row_number,
                            ),
                        ),
                    )
                )
                continue
            seen_rows.add(record_key)
            accepted_records.append(record)

    return PtmOrthologSiteImportReport(
        total_rows=len(accepted_records) + len(rejected_rows),
        accepted_records=tuple(
            sort_rows_by_fields(
                accepted_records,
                "source_species",
                "source_protein_ref",
                "source_position",
                "target_species",
            )
        ),
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        summary=PtmOrthologSiteImportSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected_rows),
            source_site_count=len(
                {
                    (
                        record.source_species,
                        record.source_protein_ref,
                        record.source_residue,
                        record.source_position,
                        record.source_modification_name,
                    )
                    for record in accepted_records
                }
            ),
            target_site_count=sum(
                1 for record in accepted_records if record.target_position is not None
            ),
            missing_target_count=sum(
                1 for record in accepted_records if record.target_position is None
            ),
        ),
        note=(
            "ptm ortholog-site import preserves explicit source and target site coordinates "
            "so conserved, shifted, missing, and unmapped statuses can be distinguished "
            "without guessing from gene names"
        ),
    )


def build_ptm_ortholog_conservation_report(
    site_entries: tuple[PtmSiteEntry, ...],
    ortholog_site_records: tuple[PtmOrthologSiteRecord, ...],
    *,
    source_species: str,
    target_species: str,
) -> PtmOrthologConservationReport:
    """Map observed PTM sites onto one explicit ortholog-site species pair."""

    records_by_source_site = _group_ortholog_site_records(
        ortholog_site_records,
        source_species=source_species,
        target_species=target_species,
    )
    entries = tuple(
        _build_conservation_entry(
            site_entry,
            matching_records=records_by_source_site.get(
                (
                    site_entry.protein_ref,
                    site_entry.residue,
                    site_entry.position,
                    site_entry.modification_name,
                ),
                (),
            ),
            source_species=source_species,
            target_species=target_species,
        )
        for site_entry in sort_rows_by_fields(
            site_entries,
            "protein_ref",
            "position",
            "modification_name",
            "site_key",
        )
    )
    return PtmOrthologConservationReport(
        source_species=source_species,
        target_species=target_species,
        entries=entries,
        summary=PtmOrthologConservationSummary(
            observed_site_count=len(entries),
            conserved_site_count=sum(
                1
                for entry in entries
                if entry.status is PtmOrthologConservationStatus.CONSERVED
            ),
            shifted_site_count=sum(
                1
                for entry in entries
                if entry.status is PtmOrthologConservationStatus.SHIFTED
            ),
            missing_site_count=sum(
                1
                for entry in entries
                if entry.status is PtmOrthologConservationStatus.MISSING
            ),
            unmapped_site_count=sum(
                1
                for entry in entries
                if entry.status is PtmOrthologConservationStatus.UNMAPPED
            ),
        ),
        note=(
            "ptm ortholog conservation reports one explicit species-pair status per observed site "
            "and keeps unmapped sites separate from true missing ortholog PTM evidence"
        ),
    )


def render_ptm_ortholog_conservation_summary_tsv(
    report: PtmOrthologConservationReport,
) -> str:
    """Render the PTM ortholog-conservation summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("source_species", report.source_species))
    writer.writerow(("target_species", report.target_species))
    writer.writerow(("observed_site_count", report.summary.observed_site_count))
    writer.writerow(("conserved_site_count", report.summary.conserved_site_count))
    writer.writerow(("shifted_site_count", report.summary.shifted_site_count))
    writer.writerow(("missing_site_count", report.summary.missing_site_count))
    writer.writerow(("unmapped_site_count", report.summary.unmapped_site_count))
    writer.writerow(("note", report.note))
    return buffer.getvalue()


def render_ptm_ortholog_conservation_tsv(
    report: PtmOrthologConservationReport,
) -> str:
    """Render PTM ortholog-conservation entries as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "site_key",
            "protein_ref",
            "residue",
            "position",
            "modification_name",
            "status",
            "source_species",
            "target_species",
            "ortholog_target_site_keys",
            "ortholog_target_protein_refs",
            "ortholog_target_positions",
            "evidence_labels",
            "source_names",
            "source_accessions",
            "note",
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
                entry.status.value,
                entry.source_species,
                entry.target_species,
                ";".join(entry.ortholog_target_site_keys),
                ";".join(entry.ortholog_target_protein_refs),
                ";".join(str(position) for position in entry.ortholog_target_positions),
                ";".join(entry.evidence_labels),
                ";".join(entry.source_names),
                ";".join(entry.source_accessions),
                entry.note,
            )
        )
    return buffer.getvalue()


def export_ptm_ortholog_conservation_summary_tsv(
    report: PtmOrthologConservationReport,
    path: Path,
) -> None:
    """Write PTM ortholog-conservation summary TSV."""

    path.write_text(
        render_ptm_ortholog_conservation_summary_tsv(report),
        encoding="utf-8",
    )


def export_ptm_ortholog_conservation_tsv(
    report: PtmOrthologConservationReport,
    path: Path,
) -> None:
    """Write PTM ortholog-conservation entry TSV."""

    path.write_text(render_ptm_ortholog_conservation_tsv(report), encoding="utf-8")


def _build_conservation_entry(
    site_entry: PtmSiteEntry,
    *,
    matching_records: tuple[PtmOrthologSiteRecord, ...],
    source_species: str,
    target_species: str,
) -> PtmOrthologConservationEntry:
    if not matching_records:
        return PtmOrthologConservationEntry(
            site_key=site_entry.site_key,
            protein_ref=site_entry.protein_ref,
            residue=site_entry.residue,
            position=site_entry.position,
            modification_name=site_entry.modification_name,
            status=PtmOrthologConservationStatus.UNMAPPED,
            source_species=source_species,
            target_species=target_species,
            note=(
                f"no ortholog-site relationship was supplied for {site_entry.site_key} "
                f"between {source_species} and {target_species}"
            ),
        )

    realized_records = tuple(
        record for record in matching_records if record.target_position is not None
    )
    if not realized_records:
        return PtmOrthologConservationEntry(
            site_key=site_entry.site_key,
            protein_ref=site_entry.protein_ref,
            residue=site_entry.residue,
            position=site_entry.position,
            modification_name=site_entry.modification_name,
            status=PtmOrthologConservationStatus.MISSING,
            source_species=source_species,
            target_species=target_species,
            evidence_labels=_stable_tuple(record.evidence for record in matching_records),
            source_names=_stable_tuple(record.source_name for record in matching_records),
            source_accessions=_stable_tuple(
                record.source_accession for record in matching_records
            ),
            note=(
                f"an ortholog protein relationship exists for {site_entry.site_key}, "
                "but no mapped ortholog PTM site was supplied"
            ),
        )

    conserved_records = tuple(
        record
        for record in realized_records
        if record.target_residue == site_entry.residue
        and record.target_position == site_entry.position
        and record.target_modification_name == site_entry.modification_name
    )
    status = (
        PtmOrthologConservationStatus.CONSERVED
        if conserved_records
        else PtmOrthologConservationStatus.SHIFTED
    )
    evidence_records = conserved_records or realized_records
    target_site_keys = tuple(
        sorted(
            f"{record.target_protein_ref}:{record.target_residue}{record.target_position}:{record.target_modification_name}"
            for record in evidence_records
            if record.target_protein_ref is not None
            and record.target_residue is not None
            and record.target_position is not None
            and record.target_modification_name is not None
        )
    )
    return PtmOrthologConservationEntry(
        site_key=site_entry.site_key,
        protein_ref=site_entry.protein_ref,
        residue=site_entry.residue,
        position=site_entry.position,
        modification_name=site_entry.modification_name,
        status=status,
        source_species=source_species,
        target_species=target_species,
        ortholog_target_site_keys=target_site_keys,
        ortholog_target_protein_refs=_stable_tuple(
            record.target_protein_ref for record in evidence_records
        ),
        ortholog_target_positions=tuple(
            sorted(
                {
                    record.target_position
                    for record in evidence_records
                    if record.target_position is not None
                }
            )
        ),
        evidence_labels=_stable_tuple(record.evidence for record in evidence_records),
        source_names=_stable_tuple(record.source_name for record in evidence_records),
        source_accessions=_stable_tuple(
            record.source_accession for record in evidence_records
        ),
        note=(
            f"{site_entry.site_key} is {status.value} across {source_species} -> "
            f"{target_species} based on explicit ortholog-site mapping"
        ),
    )


def _group_ortholog_site_records(
    records: tuple[PtmOrthologSiteRecord, ...],
    *,
    source_species: str,
    target_species: str,
) -> dict[tuple[str, str, int, str], tuple[PtmOrthologSiteRecord, ...]]:
    grouped: dict[tuple[str, str, int, str], list[PtmOrthologSiteRecord]] = {}
    for record in records:
        if record.source_species != source_species or record.target_species != target_species:
            continue
        grouped.setdefault(
            (
                record.source_protein_ref,
                record.source_residue,
                record.source_position,
                record.source_modification_name,
            ),
            [],
        ).append(record)
    return {
        site_key: tuple(
            sort_rows_by_fields(
                entries,
                "source_protein_ref",
                "source_position",
                "target_protein_ref",
                "target_position",
            )
        )
        for site_key, entries in grouped.items()
    }


def _optional_row_value(raw_fields: dict[str, str], column_name: str | None) -> str | None:
    if column_name is None:
        return None
    value = raw_fields.get(column_name, "").strip()
    return None if not value else value


def _stable_tuple(values: object) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value is not None}))


def _row_issue(
    code: str,
    message: str,
    row_number: int,
) -> PtmOrthologSiteValidationIssue:
    return PtmOrthologSiteValidationIssue(
        code=code,
        message=message,
        row_number=row_number,
    )


def _validate_required_columns(
    fieldnames: list[str],
    mapping: PtmOrthologSiteColumnMapping,
) -> None:
    required_columns = (
        mapping.source_species,
        mapping.source_protein_ref,
        mapping.source_residue,
        mapping.source_position,
        mapping.source_modification_name,
        mapping.target_species,
    )
    missing = [column for column in required_columns if column not in fieldnames]
    if missing:
        raise ValueError(
            "PTM ortholog-site TSV is missing required columns: "
            + ", ".join(missing)
        )


__all__ = (
    "PtmOrthologConservationEntry",
    "PtmOrthologConservationReport",
    "PtmOrthologConservationStatus",
    "PtmOrthologConservationSummary",
    "PtmOrthologSiteColumnMapping",
    "PtmOrthologSiteImportReport",
    "PtmOrthologSiteImportSummary",
    "PtmOrthologSiteRecord",
    "PtmOrthologSiteValidationIssue",
    "RejectedPtmOrthologSiteRow",
    "build_ptm_ortholog_conservation_report",
    "export_ptm_ortholog_conservation_summary_tsv",
    "export_ptm_ortholog_conservation_tsv",
    "parse_ptm_ortholog_site_tsv",
    "render_ptm_ortholog_conservation_summary_tsv",
    "render_ptm_ortholog_conservation_tsv",
)
