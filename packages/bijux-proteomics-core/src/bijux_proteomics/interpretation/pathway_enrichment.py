# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pathway enrichment surfaces for biological interpretation workflows."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
import json
import math
from pathlib import Path
from typing import Sequence

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationRecord,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinReferenceEntry,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel


class PathwayMemberKind(StrEnum):
    """Stable comparable member kinds for pathway-set enrichment."""

    PROTEIN = "protein"
    GENE = "gene"


class PathwayMembershipColumnMapping(JsonModel):
    """Column mapping from a pathway membership table into owned fields."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    protein_ref: str | None = None
    gene_symbol: str | None = None


class PathwayMembershipRecord(JsonModel):
    """One normalized pathway membership row."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    member_kind: PathwayMemberKind
    member_id: str = Field(..., min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedPathwayMembershipRow(JsonModel):
    """One rejected pathway membership row with a stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class PathwayMembershipImportSummary(JsonModel):
    """Stable summary over one pathway membership import pass."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_pathway_count: int = Field(..., ge=0)
    distinct_member_count: int = Field(..., ge=0)
    member_kind_counts: dict[str, int] = Field(default_factory=dict)
    source_counts: dict[str, int] = Field(default_factory=dict)


class PathwayMembershipImportReport(JsonModel):
    """Governed pathway membership import report."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[PathwayMembershipRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedPathwayMembershipRow, ...] = Field(default_factory=tuple)
    column_mapping: PathwayMembershipColumnMapping
    summary: PathwayMembershipImportSummary
    note: str = Field(..., min_length=1)


class PathwayEnrichmentEntry(JsonModel):
    """One evaluated pathway enrichment row."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    member_kind: PathwayMemberKind
    foreground_overlap_count: int = Field(..., ge=0)
    background_member_count: int = Field(..., ge=0)
    foreground_size: int = Field(..., ge=0)
    background_size: int = Field(..., ge=0)
    expected_overlap_count: float = Field(..., ge=0.0)
    enrichment_ratio: float | None = Field(default=None, ge=0.0)
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    foreground_member_ids: tuple[str, ...] = Field(default_factory=tuple)
    background_member_ids: tuple[str, ...] = Field(default_factory=tuple)


class UnresolvedPathwayMemberEntry(JsonModel):
    """One foreground or background protein missing gene support for gene-based pathways."""

    model_config = ConfigDict(extra="forbid")

    set_role: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class PathwayEnrichmentSummary(JsonModel):
    """Stable summary over one pathway enrichment run."""

    model_config = ConfigDict(extra="forbid")

    foreground_size: int = Field(..., ge=0)
    background_size: int = Field(..., ge=0)
    evaluated_entry_count: int = Field(..., ge=0)
    protein_entry_count: int = Field(..., ge=0)
    gene_entry_count: int = Field(..., ge=0)
    unresolved_foreground_count: int = Field(..., ge=0)
    unresolved_background_count: int = Field(..., ge=0)
    enriched_entry_count: int = Field(..., ge=0)


class PathwayEnrichmentReport(JsonModel):
    """Owned pathway enrichment report over protein foreground/background sets."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PathwayEnrichmentEntry, ...] = Field(default_factory=tuple)
    unresolved_members: tuple[UnresolvedPathwayMemberEntry, ...] = Field(
        default_factory=tuple
    )
    summary: PathwayEnrichmentSummary
    note: str = Field(..., min_length=1)


class PathwayEnrichmentCorrectionPolicy(JsonModel):
    """Multiple-testing policy for pathway enrichment reporting."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_enrichment_ratio: float = Field(default=1.0, ge=0.0)


def parse_pathway_membership_table(
    path: Path,
    *,
    mapping: PathwayMembershipColumnMapping | None = None,
) -> PathwayMembershipImportReport:
    """Parse one pathway membership table with protein or gene members."""

    lines = _read_delimited_lines(path)
    active_mapping = mapping or PathwayMembershipColumnMapping(
        pathway_id="pathway_id",
        pathway_name="pathway_name",
        source_name="source_name",
        source_accession="source_accession",
        protein_ref="protein_ref",
        gene_symbol="gene_symbol",
    )
    if not lines:
        return PathwayMembershipImportReport(
            source_path=str(path),
            total_rows=0,
            accepted_records=(),
            rejected_rows=(
                RejectedPathwayMembershipRow(
                    row_number=2,
                    reason="pathway membership table is empty",
                ),
            ),
            column_mapping=active_mapping,
            summary=PathwayMembershipImportSummary(
                accepted_record_count=0,
                rejected_row_count=1,
                distinct_pathway_count=0,
                distinct_member_count=0,
                member_kind_counts={},
                source_counts={},
            ),
            note="pathway membership table did not contain any readable rows",
        )

    reader = csv.DictReader(lines, delimiter=_infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("pathway membership table must include a header row")
    _validate_required_columns(reader.fieldnames, (active_mapping.pathway_id,))

    accepted_records: list[PathwayMembershipRecord] = []
    rejected_rows: list[RejectedPathwayMembershipRow] = []
    seen_memberships: set[tuple[str, str, str]] = set()
    for row_number, raw_row in enumerate(reader, start=2):
        values = _normalize_row(raw_row)
        pathway_id = values.get(active_mapping.pathway_id, "").strip()
        if not pathway_id:
            rejected_rows.append(
                RejectedPathwayMembershipRow(
                    row_number=row_number,
                    values=values,
                    reason="pathway membership row requires pathway_id",
                )
            )
            continue
        protein_token = (
            None
            if active_mapping.protein_ref is None
            else values.get(active_mapping.protein_ref, "").strip() or None
        )
        gene_symbol = (
            None
            if active_mapping.gene_symbol is None
            else values.get(active_mapping.gene_symbol, "").strip() or None
        )
        if protein_token and gene_symbol:
            rejected_rows.append(
                RejectedPathwayMembershipRow(
                    row_number=row_number,
                    values=values,
                    reason="pathway membership row must choose protein_ref or gene_symbol, not both",
                )
            )
            continue
        if protein_token is None and gene_symbol is None:
            rejected_rows.append(
                RejectedPathwayMembershipRow(
                    row_number=row_number,
                    values=values,
                    reason="pathway membership row requires protein_ref or gene_symbol",
                )
            )
            continue
        if protein_token is not None:
            member_kind = PathwayMemberKind.PROTEIN
            member_id = canonicalize_protein_reference(protein_token)
        else:
            member_kind = PathwayMemberKind.GENE
            member_id = str(gene_symbol)
        membership_key = (pathway_id, member_kind.value, member_id)
        if membership_key in seen_memberships:
            rejected_rows.append(
                RejectedPathwayMembershipRow(
                    row_number=row_number,
                    values=values,
                    reason=(
                        f"duplicate pathway membership for {pathway_id} and "
                        f"{member_kind.value} member {member_id}"
                    ),
                )
            )
            continue
        seen_memberships.add(membership_key)
        accepted_records.append(
            PathwayMembershipRecord(
                pathway_id=pathway_id,
                pathway_name=_optional_value(values, active_mapping.pathway_name),
                source_name=_optional_value(values, active_mapping.source_name),
                source_accession=_optional_value(values, active_mapping.source_accession),
                member_kind=member_kind,
                member_id=member_id,
                metadata={
                    key: value
                    for key, value in values.items()
                    if key
                    not in {
                        active_mapping.pathway_id,
                        active_mapping.pathway_name,
                        active_mapping.source_name,
                        active_mapping.source_accession,
                        active_mapping.protein_ref,
                        active_mapping.gene_symbol,
                    }
                    and value
                },
            )
        )

    member_kind_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    for record in accepted_records:
        member_kind_counts[record.member_kind.value] = (
            member_kind_counts.get(record.member_kind.value, 0) + 1
        )
        if record.source_name is not None:
            source_counts[record.source_name] = source_counts.get(record.source_name, 0) + 1

    return PathwayMembershipImportReport(
        source_path=str(path),
        total_rows=max(len(lines) - 1, 0),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        summary=PathwayMembershipImportSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected_rows),
            distinct_pathway_count=len({record.pathway_id for record in accepted_records}),
            distinct_member_count=len(
                {(record.member_kind.value, record.member_id) for record in accepted_records}
            ),
            member_kind_counts=dict(sorted(member_kind_counts.items())),
            source_counts=dict(sorted(source_counts.items())),
        ),
        note="pathway memberships preserve KEGG, Reactome, or user-supplied provenance over protein or gene members",
    )


def build_pathway_enrichment_report(
    foreground_entries: tuple[ProteinReferenceEntry, ...],
    background_entries: tuple[ProteinReferenceEntry, ...],
    pathway_records: tuple[PathwayMembershipRecord, ...],
    *,
    fasta_records: tuple[NormalizedProteinRecord, ...] = (),
    custom_annotations: tuple[ProteinAnnotationRecord, ...] = (),
) -> PathwayEnrichmentReport:
    """Run pathway enrichment over protein- or gene-based pathway memberships."""

    foreground = {entry.protein_ref for entry in foreground_entries}
    background = {entry.protein_ref for entry in background_entries}
    if not foreground:
        raise ValueError("foreground protein set must contain at least one protein")
    if not background:
        raise ValueError("background protein set must contain at least one protein")
    if not foreground <= background:
        missing = sorted(foreground - background)
        raise ValueError(
            "foreground proteins must be present in the background set: "
            + ", ".join(missing)
        )

    gene_annotations = _protein_gene_annotations(
        fasta_records=fasta_records,
        custom_annotations=custom_annotations,
    )
    unresolved_entries = _build_unresolved_pathway_members(
        foreground=foreground,
        background=background,
        pathway_records=pathway_records,
        gene_annotations=gene_annotations,
    )
    background_genes = {
        gene_symbol
        for protein_ref in background
        for gene_symbol in gene_annotations.get(protein_ref, ())
    }
    foreground_genes = {
        gene_symbol
        for protein_ref in foreground
        for gene_symbol in gene_annotations.get(protein_ref, ())
    }

    grouped = _group_pathway_records(pathway_records)
    entries: list[PathwayEnrichmentEntry] = []
    for (pathway_id, member_kind), members in sorted(grouped.items()):
        first = members[0]
        if member_kind is PathwayMemberKind.PROTEIN:
            background_members = {member.member_id for member in members} & background
            foreground_members = {member.member_id for member in members} & foreground
            background_size = len(background)
            foreground_size = len(foreground)
        else:
            background_members = {member.member_id for member in members} & background_genes
            foreground_members = {member.member_id for member in members} & foreground_genes
            background_size = len(background_genes)
            foreground_size = len(foreground_genes)
        if not foreground_members or background_size == 0 or foreground_size == 0:
            continue
        expected_overlap_count = foreground_size * len(background_members) / background_size
        enrichment_ratio = (
            len(foreground_members) / expected_overlap_count
            if expected_overlap_count > 0.0
            else None
        )
        entries.append(
            PathwayEnrichmentEntry(
                pathway_id=pathway_id,
                pathway_name=first.pathway_name,
                source_name=first.source_name,
                source_accession=first.source_accession,
                member_kind=member_kind,
                foreground_overlap_count=len(foreground_members),
                background_member_count=len(background_members),
                foreground_size=foreground_size,
                background_size=background_size,
                expected_overlap_count=round(expected_overlap_count, 6),
                enrichment_ratio=None if enrichment_ratio is None else round(enrichment_ratio, 6),
                p_value=_hypergeometric_upper_tail(
                    overlap_count=len(foreground_members),
                    term_background_count=len(background_members),
                    foreground_size=foreground_size,
                    background_size=background_size,
                ),
                foreground_member_ids=tuple(sorted(foreground_members)),
                background_member_ids=tuple(sorted(background_members)),
            )
        )

    entries = sorted(
        entries,
        key=lambda entry: (
            entry.p_value,
            -(entry.enrichment_ratio or 0.0),
            entry.pathway_id,
            entry.member_kind.value,
        ),
    )
    return PathwayEnrichmentReport(
        entries=tuple(entries),
        unresolved_members=unresolved_entries,
        summary=PathwayEnrichmentSummary(
            foreground_size=len(foreground),
            background_size=len(background),
            evaluated_entry_count=len(entries),
            protein_entry_count=sum(
                1 for entry in entries if entry.member_kind is PathwayMemberKind.PROTEIN
            ),
            gene_entry_count=sum(
                1 for entry in entries if entry.member_kind is PathwayMemberKind.GENE
            ),
            unresolved_foreground_count=sum(
                1 for entry in unresolved_entries if entry.set_role == "foreground"
            ),
            unresolved_background_count=sum(
                1 for entry in unresolved_entries if entry.set_role == "background"
            ),
            enriched_entry_count=0,
        ),
        note=(
            "pathway enrichment evaluates protein-member and gene-member pathways separately "
            "against the declared background set and preserves unresolved gene mapping explicitly"
        ),
    )


def apply_pathway_enrichment_multiple_testing(
    report: PathwayEnrichmentReport,
    *,
    policy: PathwayEnrichmentCorrectionPolicy | None = None,
) -> PathwayEnrichmentReport:
    """Apply Benjamini-Hochberg correction across evaluated pathway entries."""

    active_policy = policy or PathwayEnrichmentCorrectionPolicy()
    if not report.entries:
        return report.model_copy(
            update={
                "note": report.note
                + " Benjamini-Hochberg correction found no evaluated pathway entries."
            }
        )
    total = len(report.entries)
    ranked_indices = sorted(
        range(total),
        key=lambda index: (
            report.entries[index].p_value,
            report.entries[index].pathway_id,
            report.entries[index].member_kind.value,
        ),
    )
    adjusted = [1.0] * total
    running_minimum = 1.0
    for reverse_rank, index in enumerate(reversed(ranked_indices), start=1):
        rank = total - reverse_rank + 1
        candidate = report.entries[index].p_value * total / rank
        running_minimum = min(running_minimum, candidate)
        adjusted[index] = min(1.0, running_minimum)
    corrected_entries = tuple(
        entry.model_copy(update={"adjusted_p_value": round(adjusted[index], 12)})
        for index, entry in enumerate(report.entries)
    )
    enriched_entry_count = sum(
        1
        for entry in corrected_entries
        if entry.adjusted_p_value is not None
        and entry.adjusted_p_value <= active_policy.max_adjusted_p_value
        and (entry.enrichment_ratio or 0.0) >= active_policy.min_enrichment_ratio
    )
    return report.model_copy(
        update={
            "entries": corrected_entries,
            "summary": report.summary.model_copy(
                update={"enriched_entry_count": enriched_entry_count}
            ),
            "note": report.note
            + " Benjamini-Hochberg correction was applied across evaluated pathway entries.",
        }
    )


def render_pathway_enrichment_summary_tsv(report: PathwayEnrichmentReport) -> str:
    """Render the compact pathway enrichment summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "foreground_size",
            "background_size",
            "evaluated_entry_count",
            "protein_entry_count",
            "gene_entry_count",
            "unresolved_foreground_count",
            "unresolved_background_count",
            "enriched_entry_count",
        )
    )
    writer.writerow(
        (
            report.summary.foreground_size,
            report.summary.background_size,
            report.summary.evaluated_entry_count,
            report.summary.protein_entry_count,
            report.summary.gene_entry_count,
            report.summary.unresolved_foreground_count,
            report.summary.unresolved_background_count,
            report.summary.enriched_entry_count,
        )
    )
    return buffer.getvalue()


def render_pathway_enrichment_entry_tsv(report: PathwayEnrichmentReport) -> str:
    """Render evaluated pathway enrichment rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "pathway_name",
            "source_name",
            "source_accession",
            "member_kind",
            "foreground_overlap_count",
            "background_member_count",
            "foreground_size",
            "background_size",
            "expected_overlap_count",
            "enrichment_ratio",
            "p_value",
            "adjusted_p_value",
            "foreground_member_ids",
            "background_member_ids",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.pathway_id,
                entry.pathway_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.member_kind.value,
                entry.foreground_overlap_count,
                entry.background_member_count,
                entry.foreground_size,
                entry.background_size,
                f"{entry.expected_overlap_count:g}",
                "" if entry.enrichment_ratio is None else f"{entry.enrichment_ratio:g}",
                f"{entry.p_value:g}",
                "" if entry.adjusted_p_value is None else f"{entry.adjusted_p_value:g}",
                ";".join(entry.foreground_member_ids),
                ";".join(entry.background_member_ids),
            )
        )
    return buffer.getvalue()


def render_pathway_unresolved_member_tsv(report: PathwayEnrichmentReport) -> str:
    """Render foreground or background proteins unresolved for gene pathways as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("set_role", "protein_ref", "reason"))
    for entry in report.unresolved_members:
        writer.writerow((entry.set_role, entry.protein_ref, entry.reason))
    return buffer.getvalue()


def render_rejected_pathway_membership_tsv(
    report: PathwayMembershipImportReport,
) -> str:
    """Render rejected pathway membership rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "values", "reason"))
    for row in report.rejected_rows:
        writer.writerow((row.row_number, _metadata_json(row.values), row.reason))
    return buffer.getvalue()


def _infer_delimiter(header_line: str) -> str:
    return "\t" if "\t" in header_line else ","


def _normalize_row(raw_row: dict[str | None, str | None]) -> dict[str, str]:
    return {
        (key or "").strip(): (value or "").strip()
        for key, value in raw_row.items()
        if key is not None
    }


def _optional_value(row: dict[str, str], field_name: str | None) -> str | None:
    if field_name is None:
        return None
    value = row.get(field_name, "").strip()
    return value or None


def _read_delimited_lines(path: Path) -> list[str]:
    payload = path.read_text(encoding="utf-8")
    return payload.splitlines()


def _metadata_json(values: dict[str, str]) -> str:
    return json.dumps(values, sort_keys=True)


def _group_pathway_records(
    pathway_records: tuple[PathwayMembershipRecord, ...],
) -> dict[tuple[str, PathwayMemberKind], list[PathwayMembershipRecord]]:
    grouped: dict[tuple[str, PathwayMemberKind], list[PathwayMembershipRecord]] = {}
    for record in pathway_records:
        grouped.setdefault((record.pathway_id, record.member_kind), []).append(record)
    return grouped


def _protein_gene_annotations(
    *,
    fasta_records: tuple[NormalizedProteinRecord, ...],
    custom_annotations: tuple[ProteinAnnotationRecord, ...],
) -> dict[str, tuple[str, ...]]:
    annotations: dict[str, set[str]] = {}
    for fasta_record in fasta_records:
        if fasta_record.gene:
            annotations.setdefault(fasta_record.canonical_accession, set()).add(
                fasta_record.gene
            )
    for annotation_record in custom_annotations:
        if annotation_record.gene_symbol:
            annotations.setdefault(annotation_record.protein_ref, set()).add(
                annotation_record.gene_symbol
            )
    return {
        protein_ref: tuple(sorted(gene_symbols))
        for protein_ref, gene_symbols in annotations.items()
    }


def _build_unresolved_pathway_members(
    *,
    foreground: set[str],
    background: set[str],
    pathway_records: tuple[PathwayMembershipRecord, ...],
    gene_annotations: dict[str, tuple[str, ...]],
) -> tuple[UnresolvedPathwayMemberEntry, ...]:
    if not any(record.member_kind is PathwayMemberKind.GENE for record in pathway_records):
        return ()
    unresolved: list[UnresolvedPathwayMemberEntry] = []
    for protein_ref in sorted(foreground):
        if protein_ref not in gene_annotations:
            unresolved.append(
                UnresolvedPathwayMemberEntry(
                    set_role="foreground",
                    protein_ref=protein_ref,
                    reason="protein lacks gene annotation required for gene-based pathway memberships",
                )
            )
    for protein_ref in sorted(background - foreground):
        if protein_ref not in gene_annotations:
            unresolved.append(
                UnresolvedPathwayMemberEntry(
                    set_role="background",
                    protein_ref=protein_ref,
                    reason="protein lacks gene annotation required for gene-based pathway memberships",
                )
            )
    return tuple(unresolved)


def _hypergeometric_upper_tail(
    *,
    overlap_count: int,
    term_background_count: int,
    foreground_size: int,
    background_size: int,
) -> float:
    maximum_overlap = min(term_background_count, foreground_size)
    denominator = math.comb(background_size, foreground_size)
    probability = 0.0
    for overlap in range(overlap_count, maximum_overlap + 1):
        probability += (
            math.comb(term_background_count, overlap)
            * math.comb(
                background_size - term_background_count,
                foreground_size - overlap,
            )
            / denominator
        )
    return round(min(probability, 1.0), 12)


def _validate_required_columns(
    fieldnames: Sequence[str],
    required_columns: tuple[str, ...],
) -> None:
    available = {field.strip() for field in fieldnames}
    missing = [column for column in required_columns if column not in available]
    if missing:
        raise ValueError("missing required columns: " + ", ".join(sorted(missing)))
