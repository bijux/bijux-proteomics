# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Disease and phenotype interpretation over explicit user-supplied context."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.domain import ConfidenceTier
from bijux_proteomics.interpretation.biological_context_mapping import (
    BiologicalContextKind,
    BiologicalContextRecord,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import ProteinReferenceEntry
from bijux_proteomics.interpretation.protein_set_enrichment import (
    ProteinSetEnrichmentEntry,
    ProteinSetEnrichmentPolicy,
    build_protein_set_enrichment_report,
)
from bijux_proteomics.interpretation.protein_set_scoring import ProteinSetRecord
from bijux_proteomics.io.stable_outputs import sort_strings
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
    QuantEntityLevel,
)
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel


DiseasePhenotypeConfidenceStatus = ConfidenceTier


class DiseasePhenotypeAnnotationScope(StrEnum):
    """Whether a missing annotation came from the foreground or background."""

    FOREGROUND = "foreground"
    BACKGROUND = "background"


class DiseasePhenotypeInterpretationPolicy(JsonModel):
    """Selection and confidence policy for disease and phenotype interpretation."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(default=1.0, ge=0.0)
    min_enrichment_ratio: float = Field(default=1.0, ge=0.0)
    high_confidence_min_supporting_protein_count: int = Field(default=2, ge=1)


class DiseasePhenotypeUnknownAnnotationEntry(JsonModel):
    """One protein lacking explicit disease or phenotype annotation."""

    model_config = ConfigDict(extra="forbid")

    annotation_scope: DiseasePhenotypeAnnotationScope
    protein_ref: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class DiseasePhenotypeInterpretationEntry(JsonModel):
    """One disease or phenotype term interpreted from explicit annotation input."""

    model_config = ConfigDict(extra="forbid")

    context_kind: BiologicalContextKind
    term_id: str = Field(..., min_length=1)
    term_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    evidence_values: tuple[str, ...] = Field(default_factory=tuple)
    foreground_overlap_count: int = Field(..., ge=0)
    background_member_count: int = Field(..., ge=0)
    foreground_size: int = Field(..., ge=0)
    background_size: int = Field(..., ge=0)
    expected_overlap_count: float = Field(..., ge=0.0)
    enrichment_ratio: float | None = Field(default=None, ge=0.0)
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    supporting_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    confidence_status: DiseasePhenotypeConfidenceStatus
    confidence_note: str = Field(..., min_length=1)
    passes_interpretation_filter: bool = False


class DiseasePhenotypeInterpretationSummary(JsonModel):
    """Stable summary over one disease and phenotype interpretation run."""

    model_config = ConfigDict(extra="forbid")

    term_count: int = Field(..., ge=0)
    disease_term_count: int = Field(..., ge=0)
    phenotype_term_count: int = Field(..., ge=0)
    foreground_protein_count: int = Field(..., ge=0)
    background_protein_count: int = Field(..., ge=0)
    evaluated_term_count: int = Field(..., ge=0)
    filter_passing_term_count: int = Field(..., ge=0)
    high_confidence_term_count: int = Field(..., ge=0)
    unknown_foreground_protein_count: int = Field(..., ge=0)
    unknown_background_protein_count: int = Field(..., ge=0)


class DiseasePhenotypeInterpretationReport(JsonModel):
    """Owned disease and phenotype interpretation report over changed proteins."""

    model_config = ConfigDict(extra="forbid")

    policy: DiseasePhenotypeInterpretationPolicy
    entries: tuple[DiseasePhenotypeInterpretationEntry, ...] = Field(default_factory=tuple)
    unknown_annotation_entries: tuple[DiseasePhenotypeUnknownAnnotationEntry, ...] = (
        Field(default_factory=tuple)
    )
    summary: DiseasePhenotypeInterpretationSummary
    note: str = Field(..., min_length=1)


def build_disease_phenotype_interpretation_report(
    table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    context_records: tuple[BiologicalContextRecord, ...],
    *,
    policy: DiseasePhenotypeInterpretationPolicy | None = None,
) -> DiseasePhenotypeInterpretationReport:
    """Interpret changed proteins through explicit disease and phenotype annotation."""

    if table.entity_level is not QuantEntityLevel.PROTEIN:
        raise ValueError(
            "disease and phenotype interpretation requires a protein-level quantification table"
        )

    active_policy = policy or DiseasePhenotypeInterpretationPolicy()
    disease_phenotype_records = tuple(
        record
        for record in context_records
        if record.context_kind in {
            BiologicalContextKind.DISEASE_TERM,
            BiologicalContextKind.PHENOTYPE_TERM,
        }
    )
    if not disease_phenotype_records:
        raise ValueError(
            "disease and phenotype interpretation requires disease_term or phenotype_term context records"
        )

    protein_set_records = _build_disease_phenotype_set_records(disease_phenotype_records)
    foreground_entries = _build_foreground_protein_entries(
        differential_report,
        protein_refs_by_entity=table.entity_protein_refs,
        policy=active_policy,
    )
    background_entries = _build_background_protein_entries(table)
    if not background_entries:
        raise ValueError(
            "disease and phenotype interpretation requires entity_protein_refs on the protein quantification table"
        )
    enrichment_report = build_protein_set_enrichment_report(
        foreground_entries,
        protein_set_records,
        background_entries=background_entries,
        policy=ProteinSetEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_enrichment_ratio=0.0,
        ),
    )
    evidence_by_term = _build_evidence_lookup(disease_phenotype_records)
    entries = tuple(
        _build_interpretation_entry(
            entry,
            evidence_values=evidence_by_term[(entry.set_id, entry.set_name or "")],
            policy=active_policy,
        )
        for entry in enrichment_report.entries
    )
    unknown_annotation_entries = _build_unknown_annotation_entries(
        foreground_entries=foreground_entries,
        background_entries=background_entries,
        protein_set_records=protein_set_records,
    )
    return DiseasePhenotypeInterpretationReport(
        policy=active_policy,
        entries=entries,
        unknown_annotation_entries=unknown_annotation_entries,
        summary=DiseasePhenotypeInterpretationSummary(
            term_count=len({entry.term_id for entry in entries}),
            disease_term_count=sum(
                1 for entry in entries if entry.context_kind is BiologicalContextKind.DISEASE_TERM
            ),
            phenotype_term_count=sum(
                1
                for entry in entries
                if entry.context_kind is BiologicalContextKind.PHENOTYPE_TERM
            ),
            foreground_protein_count=len(foreground_entries),
            background_protein_count=len(background_entries),
            evaluated_term_count=len(entries),
            filter_passing_term_count=sum(
                1 for entry in entries if entry.passes_interpretation_filter
            ),
            high_confidence_term_count=sum(
                1
                for entry in entries
                if entry.confidence_status is DiseasePhenotypeConfidenceStatus.HIGH_CONFIDENCE
            ),
            unknown_foreground_protein_count=sum(
                1
                for entry in unknown_annotation_entries
                if entry.annotation_scope is DiseasePhenotypeAnnotationScope.FOREGROUND
            ),
            unknown_background_protein_count=sum(
                1
                for entry in unknown_annotation_entries
                if entry.annotation_scope is DiseasePhenotypeAnnotationScope.BACKGROUND
            ),
        ),
        note=(
            "disease and phenotype interpretation uses only explicit user-supplied "
            "disease_term and phenotype_term records, preserves source provenance and "
            "supporting proteins, and never generates a biological claim from text matching"
        ),
    )


def render_disease_phenotype_interpretation_summary_tsv(
    report: DiseasePhenotypeInterpretationReport,
) -> str:
    """Render the compact disease and phenotype interpretation summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "term_count",
            "disease_term_count",
            "phenotype_term_count",
            "foreground_protein_count",
            "background_protein_count",
            "evaluated_term_count",
            "filter_passing_term_count",
            "high_confidence_term_count",
            "unknown_foreground_protein_count",
            "unknown_background_protein_count",
        )
    )
    writer.writerow(
        (
            report.summary.term_count,
            report.summary.disease_term_count,
            report.summary.phenotype_term_count,
            report.summary.foreground_protein_count,
            report.summary.background_protein_count,
            report.summary.evaluated_term_count,
            report.summary.filter_passing_term_count,
            report.summary.high_confidence_term_count,
            report.summary.unknown_foreground_protein_count,
            report.summary.unknown_background_protein_count,
        )
    )
    return buffer.getvalue()


def render_disease_phenotype_interpretation_tsv(
    report: DiseasePhenotypeInterpretationReport,
) -> str:
    """Render disease and phenotype term results with support and confidence."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "context_kind",
            "term_id",
            "term_name",
            "source_name",
            "source_accession",
            "evidence_values",
            "foreground_overlap_count",
            "background_member_count",
            "foreground_size",
            "background_size",
            "expected_overlap_count",
            "enrichment_ratio",
            "p_value",
            "adjusted_p_value",
            "confidence_status",
            "confidence_note",
            "passes_interpretation_filter",
            "supporting_protein_refs",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.context_kind.value,
                entry.term_id,
                entry.term_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                ";".join(entry.evidence_values),
                entry.foreground_overlap_count,
                entry.background_member_count,
                entry.foreground_size,
                entry.background_size,
                f"{entry.expected_overlap_count:g}",
                "" if entry.enrichment_ratio is None else f"{entry.enrichment_ratio:g}",
                f"{entry.p_value:g}",
                "" if entry.adjusted_p_value is None else f"{entry.adjusted_p_value:g}",
                entry.confidence_status.value,
                entry.confidence_note,
                str(entry.passes_interpretation_filter).lower(),
                ";".join(entry.supporting_protein_refs),
            )
        )
    return buffer.getvalue()


def render_unknown_disease_phenotype_annotation_tsv(
    report: DiseasePhenotypeInterpretationReport,
) -> str:
    """Render proteins that lacked explicit disease or phenotype annotation."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("annotation_scope", "protein_ref", "reason"))
    for entry in report.unknown_annotation_entries:
        writer.writerow((entry.annotation_scope.value, entry.protein_ref, entry.reason))
    return buffer.getvalue()


def _build_disease_phenotype_set_records(
    records: tuple[BiologicalContextRecord, ...],
) -> tuple[ProteinSetRecord, ...]:
    return tuple(
        ProteinSetRecord(
            set_id=record.context_id,
            protein_ref=canonicalize_protein_reference(record.protein_ref),
            set_name=record.context_name,
            set_category=record.context_kind.value,
            source_name=record.source_name,
            source_accession=record.source_accession,
        )
        for record in sorted(
            records,
            key=lambda record: (
                record.context_kind.value,
                record.context_id,
                canonicalize_protein_reference(record.protein_ref),
            ),
        )
    )


def _build_foreground_protein_entries(
    report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]],
    policy: DiseasePhenotypeInterpretationPolicy,
) -> tuple[ProteinReferenceEntry, ...]:
    entries: list[ProteinReferenceEntry] = []
    row_number = 2
    for differential_entry in report.entries:
        adjusted_p_value = differential_entry.adjusted_p_value
        if adjusted_p_value is None or adjusted_p_value > policy.max_adjusted_p_value:
            continue
        if abs(differential_entry.log2_fold_change) < policy.min_absolute_log2_fold_change:
            continue
        for protein_ref in protein_refs_by_entity.get(
            differential_entry.entity_id,
            (differential_entry.entity_id,),
        ):
            entries.append(
                ProteinReferenceEntry(
                    row_number=row_number,
                    source_row_id=differential_entry.entity_id,
                    input_protein_ref=protein_ref,
                    protein_ref=canonicalize_protein_reference(protein_ref),
                )
            )
            row_number += 1
    return tuple(entries)


def _build_background_protein_entries(
    table: LabelFreeQuantTable,
) -> tuple[ProteinReferenceEntry, ...]:
    entries: list[ProteinReferenceEntry] = []
    row_number = 2
    for entity_id in table.entity_ids:
        for protein_ref in table.entity_protein_refs.get(entity_id, (entity_id,)):
            entries.append(
                ProteinReferenceEntry(
                    row_number=row_number,
                    source_row_id=entity_id,
                    input_protein_ref=protein_ref,
                    protein_ref=canonicalize_protein_reference(protein_ref),
                )
            )
            row_number += 1
    return tuple(entries)


def _build_evidence_lookup(
    records: tuple[BiologicalContextRecord, ...],
) -> dict[tuple[str, str], tuple[str, ...]]:
    evidence_by_term: dict[tuple[str, str], set[str]] = {}
    for record in records:
        key = (record.context_id, record.context_name or "")
        evidence_by_term.setdefault(key, set())
        if record.evidence is not None:
            evidence_by_term[key].add(record.evidence)
    return {
        key: sort_strings(tuple(values))
        for key, values in evidence_by_term.items()
    }


def _build_interpretation_entry(
    entry: ProteinSetEnrichmentEntry,
    *,
    evidence_values: tuple[str, ...],
    policy: DiseasePhenotypeInterpretationPolicy,
) -> DiseasePhenotypeInterpretationEntry:
    if entry.set_category is None:
        raise ValueError("disease phenotype interpretation requires set_category")
    context_kind = BiologicalContextKind(entry.set_category)
    passes_filter = _passes_interpretation_filter(entry, policy)
    confidence_status, confidence_note = _resolve_confidence(entry, policy=policy)
    return DiseasePhenotypeInterpretationEntry(
        context_kind=context_kind,
        term_id=entry.set_id,
        term_name=entry.set_name,
        source_name=entry.source_name,
        source_accession=entry.source_accession,
        evidence_values=evidence_values,
        foreground_overlap_count=entry.foreground_overlap_count,
        background_member_count=entry.background_member_count,
        foreground_size=entry.foreground_size,
        background_size=entry.background_size,
        expected_overlap_count=entry.expected_overlap_count,
        enrichment_ratio=entry.enrichment_ratio,
        p_value=entry.p_value,
        adjusted_p_value=entry.adjusted_p_value,
        supporting_protein_refs=entry.supporting_protein_refs,
        confidence_status=confidence_status,
        confidence_note=confidence_note,
        passes_interpretation_filter=passes_filter,
    )


def _resolve_confidence(
    entry: ProteinSetEnrichmentEntry,
    *,
    policy: DiseasePhenotypeInterpretationPolicy,
) -> tuple[DiseasePhenotypeConfidenceStatus, str]:
    if len(entry.supporting_protein_refs) < policy.high_confidence_min_supporting_protein_count:
        return (
            DiseasePhenotypeConfidenceStatus.LOW_CONFIDENCE,
            (
                f"supporting protein count {len(entry.supporting_protein_refs)} was below "
                f"minimum {policy.high_confidence_min_supporting_protein_count}"
            ),
        )
    if entry.source_name is None or entry.source_accession is None:
        return (
            DiseasePhenotypeConfidenceStatus.LOW_CONFIDENCE,
            "source annotation provenance was incomplete",
        )
    if not _passes_interpretation_filter(entry, policy):
        return (
            DiseasePhenotypeConfidenceStatus.LOW_CONFIDENCE,
            "term did not pass the configured enrichment thresholds",
        )
    return (
        DiseasePhenotypeConfidenceStatus.HIGH_CONFIDENCE,
        "explicit annotation, multi-protein support, and enrichment thresholds were satisfied",
    )


def _passes_interpretation_filter(
    entry: ProteinSetEnrichmentEntry,
    policy: DiseasePhenotypeInterpretationPolicy,
) -> bool:
    return (
        entry.adjusted_p_value is not None
        and entry.adjusted_p_value <= policy.max_adjusted_p_value
        and (
            entry.enrichment_ratio is None
            or entry.enrichment_ratio >= policy.min_enrichment_ratio
        )
    )


def _build_unknown_annotation_entries(
    *,
    foreground_entries: tuple[ProteinReferenceEntry, ...],
    background_entries: tuple[ProteinReferenceEntry, ...],
    protein_set_records: tuple[ProteinSetRecord, ...],
) -> tuple[DiseasePhenotypeUnknownAnnotationEntry, ...]:
    annotated_protein_refs = {
        canonicalize_protein_reference(record.protein_ref) for record in protein_set_records
    }
    seen: set[tuple[DiseasePhenotypeAnnotationScope, str]] = set()
    entries: list[DiseasePhenotypeUnknownAnnotationEntry] = []
    for scope, protein_entries in (
        (DiseasePhenotypeAnnotationScope.FOREGROUND, foreground_entries),
        (DiseasePhenotypeAnnotationScope.BACKGROUND, background_entries),
    ):
        for protein_entry in protein_entries:
            protein_ref = canonicalize_protein_reference(protein_entry.protein_ref)
            key = (scope, protein_ref)
            if protein_ref in annotated_protein_refs or key in seen:
                continue
            seen.add(key)
            entries.append(
                DiseasePhenotypeUnknownAnnotationEntry(
                    annotation_scope=scope,
                    protein_ref=protein_ref,
                    reason=(
                        "no explicit disease_term or phenotype_term annotation was supplied "
                        "for this protein"
                    ),
                )
            )
    return tuple(
        sorted(
            entries,
            key=lambda entry: (entry.annotation_scope.value, entry.protein_ref),
        )
    )


__all__ = [
    "DiseasePhenotypeAnnotationScope",
    "DiseasePhenotypeConfidenceStatus",
    "DiseasePhenotypeInterpretationEntry",
    "DiseasePhenotypeInterpretationPolicy",
    "DiseasePhenotypeInterpretationReport",
    "DiseasePhenotypeInterpretationSummary",
    "DiseasePhenotypeUnknownAnnotationEntry",
    "build_disease_phenotype_interpretation_report",
    "render_disease_phenotype_interpretation_summary_tsv",
    "render_disease_phenotype_interpretation_tsv",
    "render_unknown_disease_phenotype_annotation_tsv",
]
