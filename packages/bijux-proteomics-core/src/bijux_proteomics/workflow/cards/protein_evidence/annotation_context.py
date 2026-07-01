# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Annotation, biological-context, and pathway helpers for protein cards."""

from __future__ import annotations

from collections import defaultdict

from bijux_proteomics.interpretation import (
    BiologicalContextMappingReport,
    ComplexEnrichmentEntry,
    ComplexEnrichmentReport,
    PathwayEnrichmentEntry,
    PathwayEnrichmentReport,
    ProteinAnnotationMappingReport,
    ProteinAnnotationResultEntry,
    ProteinAnnotationStatus,
)
from bijux_proteomics.workflow.cards.protein_evidence.models import (
    ProteinEvidenceCardAnnotation,
    ProteinEvidenceCardContextEntry,
    ProteinEvidenceCardPathwayEntry,
    ProteinEvidenceCardPathwayEntryKind,
)


def build_annotation_payload(
    representative_protein_ref: str,
    *,
    annotation_entries: tuple[ProteinAnnotationResultEntry, ...],
) -> ProteinEvidenceCardAnnotation:
    annotated_entries = tuple(
        entry
        for entry in annotation_entries
        if entry.annotation_status is ProteinAnnotationStatus.ANNOTATED
    )
    primary_entry = (
        next(
            (
                entry
                for entry in annotated_entries
                if entry.protein_ref == representative_protein_ref
            ),
            None,
        )
        or (annotated_entries[0] if annotated_entries else None)
        or (annotation_entries[0] if annotation_entries else None)
    )
    if primary_entry is None:
        return ProteinEvidenceCardAnnotation(
            annotation_status=ProteinAnnotationStatus.UNMAPPED,
        )
    return ProteinEvidenceCardAnnotation(
        annotation_status=primary_entry.annotation_status,
        gene_symbol=primary_entry.gene_symbol,
        description=primary_entry.description,
        organism=primary_entry.organism,
        annotation_identifiers=tuple(
            sorted(
                {
                    entry.annotation_identifier
                    for entry in annotated_entries
                    if entry.annotation_identifier
                }
            )
        ),
        accession_aliases=tuple(
            sorted(
                {
                    alias
                    for entry in annotation_entries
                    for alias in entry.accession_aliases
                }
            )
        ),
        custom_annotation=dict(sorted(primary_entry.custom_annotation.items())),
    )


def group_annotations_by_entity(
    report: ProteinAnnotationMappingReport,
) -> dict[str, tuple[ProteinAnnotationResultEntry, ...]]:
    grouped: dict[str, list[ProteinAnnotationResultEntry]] = defaultdict(list)
    for entry in report.result_entries:
        grouped[(entry.source_row_id or entry.protein_ref)].append(entry)
    return {
        entity_id: tuple(sorted(entries, key=lambda entry: entry.protein_ref))
        for entity_id, entries in grouped.items()
    }


def group_context_entries_by_protein(
    report: BiologicalContextMappingReport | None,
) -> dict[str, tuple[ProteinEvidenceCardContextEntry, ...]]:
    if report is None:
        return {}
    grouped: dict[str, list[ProteinEvidenceCardContextEntry]] = defaultdict(list)
    for entry in report.term_entries:
        context_entry = ProteinEvidenceCardContextEntry(
            context_kind=entry.context_kind,
            context_id=entry.context_id,
            context_name=entry.context_name,
            source_name=entry.source_name,
            source_accession=entry.source_accession,
        )
        for protein_ref in entry.supporting_protein_refs:
            grouped[protein_ref].append(context_entry)
    return {
        protein_ref: tuple(
            sorted(
                entries,
                key=lambda entry: (entry.context_kind.value, entry.context_id),
            )
        )
        for protein_ref, entries in grouped.items()
    }


def group_pathway_entries_by_member(
    pathway_report: PathwayEnrichmentReport | None,
    complex_report: ComplexEnrichmentReport | None,
) -> dict[str, tuple[ProteinEvidenceCardPathwayEntry, ...]]:
    grouped: dict[str, list[ProteinEvidenceCardPathwayEntry]] = defaultdict(list)
    if pathway_report is not None:
        for entry in pathway_report.entries:
            card_entry = _pathway_card_entry(entry)
            for member_id in entry.foreground_member_ids:
                grouped[member_id].append(card_entry)
    if complex_report is not None:
        for entry in complex_report.entries:
            card_entry = _complex_card_entry(entry)
            for member_id in entry.foreground_member_ids:
                grouped[member_id].append(card_entry)
    return {
        member_id: tuple(
            sorted(
                entries,
                key=lambda entry: (entry.entry_kind.value, entry.entry_id),
            )
        )
        for member_id, entries in grouped.items()
    }


def select_representative_protein_ref(
    protein_refs: tuple[str, ...],
    *,
    annotation_entries: tuple[ProteinAnnotationResultEntry, ...],
    protein_sequences: dict[str, str],
) -> str:
    annotated_refs = {
        entry.protein_ref
        for entry in annotation_entries
        if entry.annotation_status is ProteinAnnotationStatus.ANNOTATED
    }
    for protein_ref in protein_refs:
        if protein_ref in annotated_refs and protein_ref in protein_sequences:
            return protein_ref
    for protein_ref in protein_refs:
        if protein_ref in annotated_refs:
            return protein_ref
    for protein_ref in protein_refs:
        if protein_ref in protein_sequences:
            return protein_ref
    return protein_refs[0]


def select_context_entries(
    protein_refs: tuple[str, ...],
    *,
    by_protein: dict[str, tuple[ProteinEvidenceCardContextEntry, ...]],
) -> tuple[ProteinEvidenceCardContextEntry, ...]:
    entries = {
        (
            entry.context_kind.value,
            entry.context_id,
            entry.source_accession or "",
        ): entry
        for protein_ref in protein_refs
        for entry in by_protein.get(protein_ref, ())
    }
    return tuple(
        sorted(
            entries.values(),
            key=lambda entry: (entry.context_kind.value, entry.context_id),
        )
    )


def select_pathway_entries(
    protein_refs: tuple[str, ...],
    *,
    annotation_entries: tuple[ProteinAnnotationResultEntry, ...],
    by_member: dict[str, tuple[ProteinEvidenceCardPathwayEntry, ...]],
) -> tuple[ProteinEvidenceCardPathwayEntry, ...]:
    gene_symbols = {
        entry.gene_symbol for entry in annotation_entries if entry.gene_symbol
    }
    entries = {
        (
            entry.entry_kind.value,
            entry.entry_id,
            entry.source_accession or "",
        ): entry
        for member_id in (*protein_refs, *sorted(gene_symbols))
        for entry in by_member.get(member_id, ())
    }
    return tuple(
        sorted(
            entries.values(),
            key=lambda entry: (entry.entry_kind.value, entry.entry_id),
        )
    )


def _pathway_card_entry(
    entry: PathwayEnrichmentEntry,
) -> ProteinEvidenceCardPathwayEntry:
    return ProteinEvidenceCardPathwayEntry(
        entry_kind=ProteinEvidenceCardPathwayEntryKind.PATHWAY,
        entry_id=entry.pathway_id,
        entry_name=entry.pathway_name,
        source_name=entry.source_name,
        source_accession=entry.source_accession,
        adjusted_p_value=entry.adjusted_p_value,
        enrichment_ratio=entry.enrichment_ratio,
    )


def _complex_card_entry(
    entry: ComplexEnrichmentEntry,
) -> ProteinEvidenceCardPathwayEntry:
    return ProteinEvidenceCardPathwayEntry(
        entry_kind=ProteinEvidenceCardPathwayEntryKind.COMPLEX,
        entry_id=entry.complex_id,
        entry_name=entry.complex_name,
        source_name=entry.source_name,
        source_accession=entry.source_accession,
        adjusted_p_value=entry.adjusted_p_value,
        enrichment_ratio=entry.enrichment_ratio,
    )


__all__ = [
    "build_annotation_payload",
    "group_annotations_by_entity",
    "group_context_entries_by_protein",
    "group_pathway_entries_by_member",
    "select_context_entries",
    "select_pathway_entries",
    "select_representative_protein_ref",
]
