# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Gene Ontology enrichment surfaces for biological interpretation workflows."""

from __future__ import annotations

from collections.abc import Sequence
import csv
from enum import StrEnum
from io import StringIO
import json
import math
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinReferenceEntry,
)
from bijux_proteomics.sequences.fasta import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel


class GoAspect(StrEnum):
    """Stable Gene Ontology aspect labels."""

    BIOLOGICAL_PROCESS = "biological_process"
    CELLULAR_COMPONENT = "cellular_component"
    MOLECULAR_FUNCTION = "molecular_function"


class GoAnnotationColumnMapping(JsonModel):
    """Column mapping from a GO annotation table into owned fields."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    go_term_id: str = Field(..., min_length=1)
    go_term_name: str | None = None
    go_aspect: str | None = None
    evidence_code: str | None = None


class GoAnnotationRecord(JsonModel):
    """One normalized GO membership row."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    go_term_id: str = Field(..., min_length=1)
    go_term_name: str | None = None
    go_aspect: GoAspect | None = None
    evidence_code: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedGoAnnotationRow(JsonModel):
    """One rejected GO annotation row with a stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class GoAnnotationImportSummary(JsonModel):
    """Stable summary over one GO annotation import pass."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_protein_ref_count: int = Field(..., ge=0)
    distinct_go_term_count: int = Field(..., ge=0)
    aspect_counts: dict[str, int] = Field(default_factory=dict)


class GoAnnotationImportReport(JsonModel):
    """Governed GO annotation import report."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[GoAnnotationRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedGoAnnotationRow, ...] = Field(default_factory=tuple)
    column_mapping: GoAnnotationColumnMapping
    summary: GoAnnotationImportSummary
    note: str = Field(..., min_length=1)


class GoTermEnrichmentEntry(JsonModel):
    """One GO term evaluated for protein-set enrichment."""

    model_config = ConfigDict(extra="forbid")

    go_term_id: str = Field(..., min_length=1)
    go_term_name: str | None = None
    go_aspect: GoAspect | None = None
    foreground_overlap_count: int = Field(..., ge=0)
    background_term_count: int = Field(..., ge=0)
    foreground_size: int = Field(..., ge=0)
    background_size: int = Field(..., ge=0)
    expected_overlap_count: float = Field(..., ge=0.0)
    enrichment_ratio: float | None = Field(default=None, ge=0.0)
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    foreground_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    background_protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class UnannotatedProteinSetEntry(JsonModel):
    """One foreground or background protein missing GO annotation support."""

    model_config = ConfigDict(extra="forbid")

    set_role: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)


class GoEnrichmentSummary(JsonModel):
    """Stable summary over one GO enrichment run."""

    model_config = ConfigDict(extra="forbid")

    foreground_size: int = Field(..., ge=0)
    background_size: int = Field(..., ge=0)
    evaluated_term_count: int = Field(..., ge=0)
    foreground_annotated_count: int = Field(..., ge=0)
    background_annotated_count: int = Field(..., ge=0)
    unannotated_foreground_count: int = Field(..., ge=0)
    unannotated_background_count: int = Field(..., ge=0)
    enriched_term_count: int = Field(..., ge=0)


class GoEnrichmentReport(JsonModel):
    """Owned GO enrichment report over foreground and background protein sets."""

    model_config = ConfigDict(extra="forbid")

    term_entries: tuple[GoTermEnrichmentEntry, ...] = Field(default_factory=tuple)
    unannotated_proteins: tuple[UnannotatedProteinSetEntry, ...] = Field(
        default_factory=tuple
    )
    summary: GoEnrichmentSummary
    note: str = Field(..., min_length=1)


class GoEnrichmentCorrectionPolicy(JsonModel):
    """Multiple-testing policy for GO enrichment reporting."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_enrichment_ratio: float = Field(default=1.0, ge=0.0)


def parse_go_annotation_table(
    path: Path,
    *,
    mapping: GoAnnotationColumnMapping | None = None,
) -> GoAnnotationImportReport:
    """Parse one GO annotation membership table into owned normalized records."""

    lines = _read_delimited_lines(path)
    active_mapping = mapping or GoAnnotationColumnMapping(
        protein_ref="protein_ref",
        go_term_id="go_term_id",
        go_term_name="go_term_name",
        go_aspect="go_aspect",
        evidence_code="evidence_code",
    )
    if not lines:
        return GoAnnotationImportReport(
            source_path=str(path),
            total_rows=0,
            accepted_records=(),
            rejected_rows=(
                RejectedGoAnnotationRow(
                    row_number=2,
                    reason="GO annotation table is empty",
                ),
            ),
            column_mapping=active_mapping,
            summary=GoAnnotationImportSummary(
                accepted_record_count=0,
                rejected_row_count=1,
                distinct_protein_ref_count=0,
                distinct_go_term_count=0,
                aspect_counts={},
            ),
            note="GO annotation table did not contain any readable rows",
        )

    reader = csv.DictReader(lines, delimiter=_infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("GO annotation table must include a header row")
    _validate_required_columns(
        reader.fieldnames,
        (active_mapping.protein_ref, active_mapping.go_term_id),
    )

    accepted_records: list[GoAnnotationRecord] = []
    rejected_rows: list[RejectedGoAnnotationRow] = []
    seen_memberships: set[tuple[str, str]] = set()
    for row_number, raw_row in enumerate(reader, start=2):
        values = _normalize_row(raw_row)
        protein_token = values.get(active_mapping.protein_ref, "").strip()
        go_term_id = values.get(active_mapping.go_term_id, "").strip()
        if not protein_token:
            rejected_rows.append(
                RejectedGoAnnotationRow(
                    row_number=row_number,
                    values=values,
                    reason="GO annotation row requires protein_ref",
                )
            )
            continue
        if not go_term_id:
            rejected_rows.append(
                RejectedGoAnnotationRow(
                    row_number=row_number,
                    values=values,
                    reason="GO annotation row requires go_term_id",
                )
            )
            continue
        protein_ref = canonicalize_protein_reference(protein_token)
        membership_key = (protein_ref, go_term_id)
        if membership_key in seen_memberships:
            rejected_rows.append(
                RejectedGoAnnotationRow(
                    row_number=row_number,
                    values=values,
                    reason=f"duplicate GO membership for {protein_ref} and {go_term_id}",
                )
            )
            continue
        seen_memberships.add(membership_key)
        accepted_records.append(
            GoAnnotationRecord(
                protein_ref=protein_ref,
                go_term_id=go_term_id,
                go_term_name=_optional_value(values, active_mapping.go_term_name),
                go_aspect=_parse_go_aspect(
                    _optional_value(values, active_mapping.go_aspect),
                    row_number=row_number,
                    raw_values=values,
                    rejected_rows=rejected_rows,
                ),
                evidence_code=_optional_value(values, active_mapping.evidence_code),
                metadata={
                    key: value
                    for key, value in values.items()
                    if key
                    not in {
                        active_mapping.protein_ref,
                        active_mapping.go_term_id,
                        active_mapping.go_term_name,
                        active_mapping.go_aspect,
                        active_mapping.evidence_code,
                    }
                    and value
                },
            )
        )

    aspect_counts: dict[str, int] = {}
    for record in accepted_records:
        if record.go_aspect is None:
            continue
        aspect_counts[record.go_aspect.value] = (
            aspect_counts.get(record.go_aspect.value, 0) + 1
        )
    return GoAnnotationImportReport(
        source_path=str(path),
        total_rows=max(len(lines) - 1, 0),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        summary=GoAnnotationImportSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected_rows),
            distinct_protein_ref_count=len(
                {record.protein_ref for record in accepted_records}
            ),
            distinct_go_term_count=len(
                {record.go_term_id for record in accepted_records}
            ),
            aspect_counts=dict(sorted(aspect_counts.items())),
        ),
        note="GO memberships were canonicalized onto the shared protein reference surface",
    )


def build_go_enrichment_report(
    foreground_entries: tuple[ProteinReferenceEntry, ...],
    background_entries: tuple[ProteinReferenceEntry, ...],
    go_annotations: tuple[GoAnnotationRecord, ...],
) -> GoEnrichmentReport:
    """Run one-sided GO term enrichment over foreground and background proteins."""

    foreground = _distinct_protein_refs(foreground_entries)
    background = _distinct_protein_refs(background_entries)
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

    term_to_proteins = _background_term_memberships(background, go_annotations)
    annotation_by_term = _term_metadata(go_annotations)
    annotated_foreground = {
        protein_ref
        for protein_ref in foreground
        if protein_ref in _annotated_proteins(go_annotations)
    }
    annotated_background = {
        protein_ref
        for protein_ref in background
        if protein_ref in _annotated_proteins(go_annotations)
    }
    unannotated_entries = tuple(
        sorted(
            (
                *[
                    UnannotatedProteinSetEntry(
                        set_role="foreground",
                        protein_ref=protein_ref,
                    )
                    for protein_ref in sorted(foreground - annotated_foreground)
                ],
                *[
                    UnannotatedProteinSetEntry(
                        set_role="background",
                        protein_ref=protein_ref,
                    )
                    for protein_ref in sorted(background - annotated_background)
                ],
            ),
            key=lambda entry: (entry.set_role, entry.protein_ref),
        )
    )

    term_entries: list[GoTermEnrichmentEntry] = []
    background_size = len(background)
    foreground_size = len(foreground)
    for go_term_id, background_proteins in sorted(term_to_proteins.items()):
        foreground_proteins = tuple(sorted(background_proteins & foreground))
        if not foreground_proteins:
            continue
        background_protein_refs = tuple(sorted(background_proteins))
        background_term_count = len(background_protein_refs)
        expected_overlap_count = (
            foreground_size * background_term_count / background_size
        )
        enrichment_ratio = (
            len(foreground_proteins) / expected_overlap_count
            if expected_overlap_count > 0.0
            else None
        )
        term_metadata = annotation_by_term[go_term_id]
        term_entries.append(
            GoTermEnrichmentEntry(
                go_term_id=go_term_id,
                go_term_name=term_metadata.go_term_name,
                go_aspect=term_metadata.go_aspect,
                foreground_overlap_count=len(foreground_proteins),
                background_term_count=background_term_count,
                foreground_size=foreground_size,
                background_size=background_size,
                expected_overlap_count=round(expected_overlap_count, 6),
                enrichment_ratio=(
                    None if enrichment_ratio is None else round(enrichment_ratio, 6)
                ),
                p_value=_hypergeometric_upper_tail(
                    overlap_count=len(foreground_proteins),
                    term_background_count=background_term_count,
                    foreground_size=foreground_size,
                    background_size=background_size,
                ),
                foreground_protein_refs=foreground_proteins,
                background_protein_refs=background_protein_refs,
            )
        )

    return GoEnrichmentReport(
        term_entries=tuple(
            sorted(
                term_entries,
                key=lambda entry: (
                    entry.p_value,
                    -(entry.enrichment_ratio or 0.0),
                    entry.go_term_id,
                ),
            )
        ),
        unannotated_proteins=unannotated_entries,
        summary=GoEnrichmentSummary(
            foreground_size=foreground_size,
            background_size=background_size,
            evaluated_term_count=len(term_entries),
            foreground_annotated_count=len(annotated_foreground),
            background_annotated_count=len(annotated_background),
            unannotated_foreground_count=sum(
                1 for entry in unannotated_entries if entry.set_role == "foreground"
            ),
            unannotated_background_count=sum(
                1 for entry in unannotated_entries if entry.set_role == "background"
            ),
            enriched_term_count=0,
        ),
        note=(
            "GO term enrichment compares foreground overlap against the explicit background "
            "set with a one-sided hypergeometric test and preserves unannotated proteins explicitly"
        ),
    )


def apply_go_enrichment_multiple_testing(
    report: GoEnrichmentReport,
    *,
    policy: GoEnrichmentCorrectionPolicy | None = None,
) -> GoEnrichmentReport:
    """Apply Benjamini-Hochberg correction across evaluated GO terms."""

    active_policy = policy or GoEnrichmentCorrectionPolicy()
    if not report.term_entries:
        return report.model_copy(
            update={
                "note": report.note
                + " Benjamini-Hochberg correction found no evaluated GO terms."
            }
        )
    total = len(report.term_entries)
    ranked_indices = sorted(
        range(total),
        key=lambda index: (
            report.term_entries[index].p_value,
            report.term_entries[index].go_term_id,
        ),
    )
    adjusted = [1.0] * total
    running_minimum = 1.0
    for reverse_rank, index in enumerate(reversed(ranked_indices), start=1):
        rank = total - reverse_rank + 1
        candidate = report.term_entries[index].p_value * total / rank
        running_minimum = min(running_minimum, candidate)
        adjusted[index] = min(1.0, running_minimum)
    corrected_entries = tuple(
        entry.model_copy(update={"adjusted_p_value": round(adjusted[index], 12)})
        for index, entry in enumerate(report.term_entries)
    )
    enriched_term_count = sum(
        1
        for entry in corrected_entries
        if entry.adjusted_p_value is not None
        and entry.adjusted_p_value <= active_policy.max_adjusted_p_value
        and (entry.enrichment_ratio or 0.0) >= active_policy.min_enrichment_ratio
    )
    return report.model_copy(
        update={
            "term_entries": corrected_entries,
            "summary": report.summary.model_copy(
                update={"enriched_term_count": enriched_term_count}
            ),
            "note": report.note
            + " Benjamini-Hochberg correction was applied across evaluated GO terms.",
        }
    )


def render_go_enrichment_summary_tsv(report: GoEnrichmentReport) -> str:
    """Render the compact GO enrichment summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "foreground_size",
            "background_size",
            "evaluated_term_count",
            "foreground_annotated_count",
            "background_annotated_count",
            "unannotated_foreground_count",
            "unannotated_background_count",
            "enriched_term_count",
        )
    )
    writer.writerow(
        (
            report.summary.foreground_size,
            report.summary.background_size,
            report.summary.evaluated_term_count,
            report.summary.foreground_annotated_count,
            report.summary.background_annotated_count,
            report.summary.unannotated_foreground_count,
            report.summary.unannotated_background_count,
            report.summary.enriched_term_count,
        )
    )
    return buffer.getvalue()


def render_go_enrichment_term_tsv(report: GoEnrichmentReport) -> str:
    """Render evaluated GO term enrichment rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "go_term_id",
            "go_term_name",
            "go_aspect",
            "foreground_overlap_count",
            "background_term_count",
            "foreground_size",
            "background_size",
            "expected_overlap_count",
            "enrichment_ratio",
            "p_value",
            "adjusted_p_value",
            "foreground_protein_refs",
            "background_protein_refs",
        )
    )
    for entry in report.term_entries:
        writer.writerow(
            (
                entry.go_term_id,
                entry.go_term_name or "",
                "" if entry.go_aspect is None else entry.go_aspect.value,
                entry.foreground_overlap_count,
                entry.background_term_count,
                entry.foreground_size,
                entry.background_size,
                f"{entry.expected_overlap_count:g}",
                "" if entry.enrichment_ratio is None else f"{entry.enrichment_ratio:g}",
                f"{entry.p_value:g}",
                "" if entry.adjusted_p_value is None else f"{entry.adjusted_p_value:g}",
                ";".join(entry.foreground_protein_refs),
                ";".join(entry.background_protein_refs),
            )
        )
    return buffer.getvalue()


def render_go_enrichment_unannotated_tsv(report: GoEnrichmentReport) -> str:
    """Render unannotated foreground or background proteins as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("set_role", "protein_ref"))
    for entry in report.unannotated_proteins:
        writer.writerow((entry.set_role, entry.protein_ref))
    return buffer.getvalue()


def render_rejected_go_annotation_tsv(report: GoAnnotationImportReport) -> str:
    """Render rejected GO annotation rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "values", "reason"))
    for row in report.rejected_rows:
        writer.writerow((row.row_number, _metadata_json(row.values), row.reason))
    return buffer.getvalue()


def _parse_go_aspect(
    value: str | None,
    *,
    row_number: int,
    raw_values: dict[str, str],
    rejected_rows: list[RejectedGoAnnotationRow],
) -> GoAspect | None:
    if value is None:
        return None
    normalized = value.strip().lower().replace(" ", "_")
    alias_map = {
        "bp": GoAspect.BIOLOGICAL_PROCESS,
        "biological_process": GoAspect.BIOLOGICAL_PROCESS,
        "biological-process": GoAspect.BIOLOGICAL_PROCESS,
        "cc": GoAspect.CELLULAR_COMPONENT,
        "cellular_component": GoAspect.CELLULAR_COMPONENT,
        "cellular-component": GoAspect.CELLULAR_COMPONENT,
        "mf": GoAspect.MOLECULAR_FUNCTION,
        "molecular_function": GoAspect.MOLECULAR_FUNCTION,
        "molecular-function": GoAspect.MOLECULAR_FUNCTION,
    }
    aspect = alias_map.get(normalized)
    if aspect is None:
        rejected_rows.append(
            RejectedGoAnnotationRow(
                row_number=row_number,
                values=raw_values,
                reason=f"unsupported go_aspect {value!r}",
            )
        )
    return aspect


def _distinct_protein_refs(entries: tuple[ProteinReferenceEntry, ...]) -> set[str]:
    return {entry.protein_ref for entry in entries}


def _annotated_proteins(
    go_annotations: tuple[GoAnnotationRecord, ...],
) -> set[str]:
    return {record.protein_ref for record in go_annotations}


def _background_term_memberships(
    background: set[str],
    go_annotations: tuple[GoAnnotationRecord, ...],
) -> dict[str, set[str]]:
    memberships: dict[str, set[str]] = {}
    for record in go_annotations:
        if record.protein_ref not in background:
            continue
        memberships.setdefault(record.go_term_id, set()).add(record.protein_ref)
    return memberships


def _term_metadata(
    go_annotations: tuple[GoAnnotationRecord, ...],
) -> dict[str, GoAnnotationRecord]:
    metadata: dict[str, GoAnnotationRecord] = {}
    for record in go_annotations:
        metadata.setdefault(record.go_term_id, record)
    return metadata


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


def _validate_required_columns(
    fieldnames: Sequence[str],
    required_columns: tuple[str, ...],
) -> None:
    available = {field.strip() for field in fieldnames}
    missing = [column for column in required_columns if column not in available]
    if missing:
        raise ValueError("missing required columns: " + ", ".join(sorted(missing)))
