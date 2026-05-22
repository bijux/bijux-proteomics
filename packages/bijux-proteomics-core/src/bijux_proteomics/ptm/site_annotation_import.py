# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM site-annotation import and mapping surfaces."""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class PtmSiteAnnotationColumnMapping(JsonModel):
    """Column mapping from a PTM site-annotation table into owned annotation fields."""

    model_config = ConfigDict(extra="forbid")

    species: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1)
    position: str = Field(..., min_length=1)
    modification_name: str = Field(..., min_length=1)
    site_function: str | None = None
    kinases: str | None = None
    pathways: str | None = None
    source_name: str | None = None
    source_accession: str | None = None


class PtmSiteAnnotationValidationIssue(JsonModel):
    """One PTM site-annotation validation issue."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=2)


class RejectedPtmSiteAnnotationRow(JsonModel):
    """One rejected PTM site-annotation input row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[PtmSiteAnnotationValidationIssue, ...] = Field(default_factory=tuple)


class PtmSiteAnnotationRecord(JsonModel):
    """One normalized PTM site-annotation record."""

    model_config = ConfigDict(extra="forbid")

    species: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    site_function: str | None = None
    kinases: tuple[str, ...] = Field(default_factory=tuple)
    pathways: tuple[str, ...] = Field(default_factory=tuple)
    source_name: str | None = None
    source_accession: str | None = None


class PtmSiteAnnotationImportSummary(JsonModel):
    """Stable summary over one PTM site-annotation import pass."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    species_count: int = Field(..., ge=0)
    function_annotated_count: int = Field(..., ge=0)
    kinase_annotated_count: int = Field(..., ge=0)
    pathway_annotated_count: int = Field(..., ge=0)


class PtmSiteAnnotationImportReport(JsonModel):
    """Governed PTM site-annotation import report."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[PtmSiteAnnotationRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedPtmSiteAnnotationRow, ...] = Field(default_factory=tuple)
    column_mapping: PtmSiteAnnotationColumnMapping
    summary: PtmSiteAnnotationImportSummary
    note: str = Field(..., min_length=1)


def parse_ptm_site_annotation_tsv(
    path: Path,
    *,
    mapping: PtmSiteAnnotationColumnMapping | None = None,
    kinase_separator: str = ";",
    pathway_separator: str = ";",
) -> PtmSiteAnnotationImportReport:
    """Parse one PTM site-annotation TSV into owned normalized records."""

    active_mapping = mapping or PtmSiteAnnotationColumnMapping(
        species="species",
        protein_ref="protein_ref",
        residue="residue",
        position="position",
        modification_name="modification_name",
        site_function="site_function",
        kinases="kinases",
        pathways="pathways",
        source_name="source_name",
        source_accession="source_accession",
    )
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("PTM site annotation TSV must include a header row")
        _validate_required_columns(reader.fieldnames, active_mapping)

        accepted: list[PtmSiteAnnotationRecord] = []
        rejected: list[RejectedPtmSiteAnnotationRow] = []
        for row_number, row in enumerate(reader, start=2):
            raw_fields = {
                str(key): str(value or "")
                for key, value in row.items()
                if key is not None
            }
            issues: list[PtmSiteAnnotationValidationIssue] = []

            species = raw_fields.get(active_mapping.species, "").strip()
            protein_ref = raw_fields.get(active_mapping.protein_ref, "").strip()
            residue = raw_fields.get(active_mapping.residue, "").strip()
            position_token = raw_fields.get(active_mapping.position, "").strip()
            modification_name = raw_fields.get(active_mapping.modification_name, "").strip()

            if not species:
                issues.append(_row_issue("missing_species", "missing species", row_number))
            if not protein_ref:
                issues.append(
                    _row_issue("missing_protein_ref", "missing protein reference", row_number)
                )
            if len(residue) != 1:
                issues.append(
                    _row_issue(
                        "invalid_residue",
                        "residue must contain exactly one amino-acid character",
                        row_number,
                    )
                )
            if not modification_name:
                issues.append(
                    _row_issue(
                        "missing_modification_name",
                        "missing modification name",
                        row_number,
                    )
                )

            position: int | None = None
            try:
                position = int(position_token)
                if position < 1:
                    raise ValueError
            except ValueError:
                issues.append(
                    _row_issue(
                        "invalid_position",
                        "position must be a positive integer",
                        row_number,
                    )
                )

            if issues:
                rejected.append(
                    RejectedPtmSiteAnnotationRow(
                        row_number=row_number,
                        raw_fields=raw_fields,
                        issues=tuple(issues),
                    )
                )
                continue

            accepted.append(
                PtmSiteAnnotationRecord(
                    species=species,
                    protein_ref=protein_ref,
                    residue=residue,
                    position=position,
                    modification_name=modification_name,
                    site_function=_row_value(raw_fields, active_mapping.site_function),
                    kinases=_split_multi_value(
                        _row_value(raw_fields, active_mapping.kinases),
                        separator=kinase_separator,
                    ),
                    pathways=_split_multi_value(
                        _row_value(raw_fields, active_mapping.pathways),
                        separator=pathway_separator,
                    ),
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
                record.species.lower(),
                record.protein_ref,
                record.position,
                record.modification_name,
            ),
        )
    )
    return PtmSiteAnnotationImportReport(
        total_rows=len(accepted_records) + len(rejected),
        accepted_records=accepted_records,
        rejected_rows=tuple(rejected),
        column_mapping=active_mapping,
        summary=PtmSiteAnnotationImportSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected),
            species_count=len({record.species.lower() for record in accepted_records}),
            function_annotated_count=sum(
                1 for record in accepted_records if record.site_function is not None
            ),
            kinase_annotated_count=sum(
                1 for record in accepted_records if record.kinases
            ),
            pathway_annotated_count=sum(
                1 for record in accepted_records if record.pathways
            ),
        ),
        note=(
            "ptm site annotation import preserves species, protein, residue, modification, and optional function, kinase, and pathway context before any observed-site mapping"
        ),
    )


def _validate_required_columns(
    fieldnames: list[str],
    mapping: PtmSiteAnnotationColumnMapping,
) -> None:
    required = (
        mapping.species,
        mapping.protein_ref,
        mapping.residue,
        mapping.position,
        mapping.modification_name,
    )
    for column in required:
        if column not in fieldnames:
            raise ValueError(f"missing required PTM site annotation column {column!r}")


def _row_issue(
    code: str,
    message: str,
    row_number: int,
) -> PtmSiteAnnotationValidationIssue:
    return PtmSiteAnnotationValidationIssue(
        code=code,
        message=message,
        row_number=row_number,
    )


def _row_value(raw_fields: dict[str, str], column: str | None) -> str | None:
    if column is None:
        return None
    value = raw_fields.get(column, "").strip()
    return value or None


def _split_multi_value(value: str | None, *, separator: str) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(
        token
        for token in (part.strip() for part in value.split(separator))
        if token
    )
