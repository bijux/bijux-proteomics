# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM site-annotation import and mapping surfaces."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from collections.abc import Sequence
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.ptm.contracts import PtmSiteEntry
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
    phosphatases: str | None = None
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
    phosphatases: tuple[str, ...] = Field(default_factory=tuple)
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
    phosphatase_annotated_count: int = Field(..., ge=0)
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


class PtmMappedSiteAnnotationEntry(JsonModel):
    """One imported annotation row mapped onto one observed PTM site."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    annotation_species: str = Field(..., min_length=1)
    observed_species: str | None = None
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    site_function: str | None = None
    kinases: tuple[str, ...] = Field(default_factory=tuple)
    phosphatases: tuple[str, ...] = Field(default_factory=tuple)
    pathways: tuple[str, ...] = Field(default_factory=tuple)
    source_name: str | None = None
    source_accession: str | None = None
    ambiguous_site: bool = False
    shared_peptide_site: bool = False


class PtmUnmappedSiteAnnotationEntry(JsonModel):
    """One imported annotation row that could not be mapped onto an observed PTM site."""

    model_config = ConfigDict(extra="forbid")

    annotation_species: str = Field(..., min_length=1)
    observed_species: str | None = None
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    source_name: str | None = None
    source_accession: str | None = None
    reason: str = Field(..., min_length=1)


class PtmSiteAnnotationMappingSummary(JsonModel):
    """Stable summary over PTM site-annotation mapping onto observed sites."""

    model_config = ConfigDict(extra="forbid")

    matched_annotation_count: int = Field(..., ge=0)
    matched_site_count: int = Field(..., ge=0)
    unmapped_annotation_count: int = Field(..., ge=0)
    species_mismatch_count: int = Field(..., ge=0)


class PtmSiteAnnotationMappingReport(JsonModel):
    """Governed PTM site-annotation mapping report."""

    model_config = ConfigDict(extra="forbid")

    target_species: str | None = None
    matched_annotations: tuple[PtmMappedSiteAnnotationEntry, ...] = Field(
        default_factory=tuple
    )
    unmapped_annotations: tuple[PtmUnmappedSiteAnnotationEntry, ...] = Field(
        default_factory=tuple
    )
    summary: PtmSiteAnnotationMappingSummary
    note: str = Field(..., min_length=1)


class PtmSiteAnnotationBiologyEntry(JsonModel):
    """One known-biology term summarized over mapped PTM site annotations."""

    model_config = ConfigDict(extra="forbid")

    term: str = Field(..., min_length=1)
    site_count: int = Field(..., ge=0)
    site_keys: tuple[str, ...] = Field(default_factory=tuple)


class PtmSiteAnnotationBiologySummary(JsonModel):
    """Known-biology summaries preserved over mapped PTM site annotations."""

    model_config = ConfigDict(extra="forbid")

    function_entries: tuple[PtmSiteAnnotationBiologyEntry, ...] = Field(
        default_factory=tuple
    )
    kinase_entries: tuple[PtmSiteAnnotationBiologyEntry, ...] = Field(
        default_factory=tuple
    )
    phosphatase_entries: tuple[PtmSiteAnnotationBiologyEntry, ...] = Field(
        default_factory=tuple
    )
    pathway_entries: tuple[PtmSiteAnnotationBiologyEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


def parse_ptm_site_annotation_tsv(
    path: Path,
    *,
    mapping: PtmSiteAnnotationColumnMapping | None = None,
    kinase_separator: str = ";",
    phosphatase_separator: str = ";",
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
        phosphatases="phosphatases",
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

            if position is not None:
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
                        phosphatases=_split_multi_value(
                            _row_value(raw_fields, active_mapping.phosphatases),
                            separator=phosphatase_separator,
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
            phosphatase_annotated_count=sum(
                1 for record in accepted_records if record.phosphatases
            ),
            pathway_annotated_count=sum(
                1 for record in accepted_records if record.pathways
            ),
        ),
        note=(
            "ptm site annotation import preserves species, protein, residue, modification, and optional function, kinase, phosphatase, and pathway context before any observed-site mapping"
        ),
    )


def build_ptm_site_annotation_mapping_report(
    site_entries: tuple[PtmSiteEntry, ...],
    annotation_records: tuple[PtmSiteAnnotationRecord, ...],
    *,
    target_species: str | None = None,
) -> PtmSiteAnnotationMappingReport:
    """Map imported PTM site annotations onto one observed PTM site table."""

    site_by_identity = {
        (
            entry.protein_ref,
            entry.residue,
            entry.position,
            entry.modification_name,
        ): entry
        for entry in site_entries
    }
    normalized_target_species = _normalized_species(target_species)
    matched: list[PtmMappedSiteAnnotationEntry] = []
    unmapped: list[PtmUnmappedSiteAnnotationEntry] = []
    species_mismatch_count = 0

    for record in annotation_records:
        if (
            normalized_target_species is not None
            and _normalized_species(record.species) != normalized_target_species
        ):
            species_mismatch_count += 1
            unmapped.append(
                PtmUnmappedSiteAnnotationEntry(
                    annotation_species=record.species,
                    observed_species=target_species,
                    protein_ref=record.protein_ref,
                    residue=record.residue,
                    position=record.position,
                    modification_name=record.modification_name,
                    source_name=record.source_name,
                    source_accession=record.source_accession,
                    reason="annotation species does not match the observed proteome species",
                )
            )
            continue

        site_entry = site_by_identity.get(
            (
                record.protein_ref,
                record.residue,
                record.position,
                record.modification_name,
            )
        )
        if site_entry is None:
            unmapped.append(
                PtmUnmappedSiteAnnotationEntry(
                    annotation_species=record.species,
                    observed_species=target_species,
                    protein_ref=record.protein_ref,
                    residue=record.residue,
                    position=record.position,
                    modification_name=record.modification_name,
                    source_name=record.source_name,
                    source_accession=record.source_accession,
                    reason="no observed PTM site matched the imported annotation identity",
                )
            )
            continue

        matched.append(
            PtmMappedSiteAnnotationEntry(
                site_key=site_entry.site_key,
                annotation_species=record.species,
                observed_species=target_species,
                protein_ref=record.protein_ref,
                residue=record.residue,
                position=record.position,
                modification_name=record.modification_name,
                site_function=record.site_function,
                kinases=record.kinases,
                phosphatases=record.phosphatases,
                pathways=record.pathways,
                source_name=record.source_name,
                source_accession=record.source_accession,
                ambiguous_site=site_entry.ambiguous,
                shared_peptide_site=site_entry.shared_peptide,
            )
        )

    return PtmSiteAnnotationMappingReport(
        target_species=target_species,
        matched_annotations=tuple(
            sorted(
                matched,
                key=lambda entry: (
                    entry.protein_ref,
                    entry.position,
                    entry.modification_name,
                    entry.source_accession or "",
                ),
            )
        ),
        unmapped_annotations=tuple(
            sorted(
                unmapped,
                key=lambda entry: (
                    entry.protein_ref,
                    entry.position,
                    entry.modification_name,
                    entry.reason,
                ),
            )
        ),
        summary=PtmSiteAnnotationMappingSummary(
            matched_annotation_count=len(matched),
            matched_site_count=len({entry.site_key for entry in matched}),
            unmapped_annotation_count=len(unmapped),
            species_mismatch_count=species_mismatch_count,
        ),
        note=(
            "ptm site annotation mapping preserves exact protein, residue, position, modification, and species matching against one observed PTM site table"
        ),
    )


def build_ptm_site_annotation_biology_summary(
    mapping_report: PtmSiteAnnotationMappingReport,
) -> PtmSiteAnnotationBiologySummary:
    """Summarize known functions, kinases, phosphatases, and pathways over mapped PTM sites."""

    return PtmSiteAnnotationBiologySummary(
        function_entries=_summarize_annotation_terms(
            mapping_report.matched_annotations,
            field_name="site_function",
        ),
        kinase_entries=_summarize_annotation_terms(
            mapping_report.matched_annotations,
            field_name="kinases",
        ),
        phosphatase_entries=_summarize_annotation_terms(
            mapping_report.matched_annotations,
            field_name="phosphatases",
        ),
        pathway_entries=_summarize_annotation_terms(
            mapping_report.matched_annotations,
            field_name="pathways",
        ),
        note=(
            "ptm site annotation biology summary preserves known function, kinase, phosphatase, and pathway labels over the mapped observed-site set"
        ),
    )


def render_ptm_site_annotation_mapping_summary_tsv(
    report: PtmSiteAnnotationMappingReport,
) -> str:
    """Render PTM site-annotation mapping summary as a stable TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "target_species",
            "matched_annotation_count",
            "matched_site_count",
            "unmapped_annotation_count",
            "species_mismatch_count",
        )
    )
    writer.writerow(
        (
            report.target_species or "",
            report.summary.matched_annotation_count,
            report.summary.matched_site_count,
            report.summary.unmapped_annotation_count,
            report.summary.species_mismatch_count,
        )
    )
    return buffer.getvalue()


def render_ptm_mapped_site_annotation_tsv(
    report: PtmSiteAnnotationMappingReport,
) -> str:
    """Render mapped PTM site annotations as a stable TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "site_key",
            "annotation_species",
            "observed_species",
            "protein_ref",
            "residue",
            "position",
            "modification_name",
            "site_function",
            "kinases",
            "phosphatases",
            "pathways",
            "source_name",
            "source_accession",
            "ambiguous_site",
            "shared_peptide_site",
        )
    )
    for entry in report.matched_annotations:
        writer.writerow(
            (
                entry.site_key,
                entry.annotation_species,
                entry.observed_species or "",
                entry.protein_ref,
                entry.residue,
                entry.position,
                entry.modification_name,
                entry.site_function or "",
                ";".join(entry.kinases),
                ";".join(entry.phosphatases),
                ";".join(entry.pathways),
                entry.source_name or "",
                entry.source_accession or "",
                str(entry.ambiguous_site).lower(),
                str(entry.shared_peptide_site).lower(),
            )
        )
    return buffer.getvalue()


def render_ptm_unmapped_site_annotation_tsv(
    report: PtmSiteAnnotationMappingReport,
) -> str:
    """Render unmapped PTM site annotations as a stable TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "annotation_species",
            "observed_species",
            "protein_ref",
            "residue",
            "position",
            "modification_name",
            "source_name",
            "source_accession",
            "reason",
        )
    )
    for entry in report.unmapped_annotations:
        writer.writerow(
            (
                entry.annotation_species,
                entry.observed_species or "",
                entry.protein_ref,
                entry.residue,
                entry.position,
                entry.modification_name,
                entry.source_name or "",
                entry.source_accession or "",
                entry.reason,
            )
        )
    return buffer.getvalue()


def render_ptm_site_annotation_biology_tsv(
    summary: PtmSiteAnnotationBiologySummary,
    *,
    category: str,
) -> str:
    """Render one PTM site-annotation biology category as a stable TSV ledger."""

    category_entries = {
        "function": summary.function_entries,
        "kinase": summary.kinase_entries,
        "phosphatase": summary.phosphatase_entries,
        "pathway": summary.pathway_entries,
    }
    if category not in category_entries:
        raise ValueError(
            "category must be one of function, kinase, phosphatase, or pathway"
        )
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("term", "site_count", "site_keys"))
    for entry in category_entries[category]:
        writer.writerow((entry.term, entry.site_count, ";".join(entry.site_keys)))
    return buffer.getvalue()


def export_ptm_site_annotation_mapping_summary_tsv(
    report: PtmSiteAnnotationMappingReport,
    path: Path,
) -> None:
    """Write PTM site-annotation mapping summary to a stable TSV artifact."""

    write_output_table_tsv(path, render_ptm_site_annotation_mapping_summary_tsv(report))


def export_ptm_mapped_site_annotation_tsv(
    report: PtmSiteAnnotationMappingReport,
    path: Path,
) -> None:
    """Write mapped PTM site annotations to a stable TSV artifact."""

    write_output_table_tsv(path, render_ptm_mapped_site_annotation_tsv(report))


def export_ptm_unmapped_site_annotation_tsv(
    report: PtmSiteAnnotationMappingReport,
    path: Path,
) -> None:
    """Write unmapped PTM site annotations to a stable TSV artifact."""

    write_output_table_tsv(path, render_ptm_unmapped_site_annotation_tsv(report))


def export_ptm_site_annotation_biology_tsv(
    summary: PtmSiteAnnotationBiologySummary,
    *,
    category: str,
    path: Path,
) -> None:
    """Write one PTM site-annotation biology category to a stable TSV artifact."""

    write_output_table_tsv(path, render_ptm_site_annotation_biology_tsv(summary, category=category))


def _validate_required_columns(
    fieldnames: Sequence[str],
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


def _normalized_species(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized or None


def _summarize_annotation_terms(
    matched_annotations: tuple[PtmMappedSiteAnnotationEntry, ...],
    *,
    field_name: str,
) -> tuple[PtmSiteAnnotationBiologyEntry, ...]:
    grouped: dict[str, set[str]] = {}
    for entry in matched_annotations:
        value = getattr(entry, field_name)
        if value is None:
            continue
        if isinstance(value, tuple):
            terms = value
        else:
            terms = (value,)
        for term in terms:
            grouped.setdefault(term, set()).add(entry.site_key)
    return tuple(
        PtmSiteAnnotationBiologyEntry(
            term=term,
            site_count=len(site_keys),
            site_keys=tuple(sorted(site_keys)),
        )
        for term, site_keys in sorted(
            grouped.items(),
            key=lambda item: (-len(item[1]), item[0]),
        )
    )
