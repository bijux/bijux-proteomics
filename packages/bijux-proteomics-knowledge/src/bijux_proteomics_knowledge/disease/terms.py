# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Disease and phenotype term resolution over curated annotation packs."""

from __future__ import annotations

import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.annotation_packs import AnnotationPack
from bijux_proteomics.interpretation.biological_context_mapping import (
    BiologicalContextKind,
    BiologicalContextRecord,
)
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.identity.proteins import resolve_protein_ids


class DiseaseTermResolutionEntry(JsonModel):
    """One resolved disease or phenotype annotation row."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    term_id: str = Field(..., min_length=1)
    term_name: str | None = None
    source: str = Field(..., min_length=1)
    evidence_type: str = Field(..., min_length=1)


class DiseaseTermResolutionSummary(JsonModel):
    """Stable summary over disease and phenotype term resolution."""

    model_config = ConfigDict(extra="forbid")

    protein_count: int = Field(..., ge=0)
    resolved_protein_count: int = Field(..., ge=0)
    term_count: int = Field(..., ge=0)
    disease_term_count: int = Field(..., ge=0)
    phenotype_term_count: int = Field(..., ge=0)
    source_filtered_row_count: int = Field(..., ge=0)


class DiseaseTermResolutionReport(JsonModel):
    """Owned report over disease and phenotype term annotations."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[DiseaseTermResolutionEntry, ...] = Field(default_factory=tuple)
    summary: DiseaseTermResolutionSummary
    note: str = Field(..., min_length=1)


def resolve_disease_terms(
    protein_ids: tuple[str, ...],
    disease_pack: AnnotationPack | tuple[BiologicalContextRecord, ...],
) -> DiseaseTermResolutionReport:
    """Resolve proteins onto curated disease and phenotype term annotations."""

    disease_records, annotation_pack = _normalize_disease_pack(disease_pack)
    lookup: dict[str, list[BiologicalContextRecord]] = {}
    source_filtered_row_count = 0
    for record in disease_records:
        if record.context_kind not in {
            BiologicalContextKind.DISEASE_TERM,
            BiologicalContextKind.PHENOTYPE_TERM,
        }:
            continue
        if _source_value(record) is None:
            source_filtered_row_count += 1
            continue
        canonical_ref = canonicalize_protein_reference(record.protein_ref)
        lookup.setdefault(canonical_ref, []).append(record)

    entries: list[DiseaseTermResolutionEntry] = []
    for protein_id in protein_ids:
        direct_matches = lookup.get(canonicalize_protein_reference(protein_id), ())
        if direct_matches:
            entries.extend(_build_entries(protein_id=protein_id, matches=tuple(direct_matches)))
            continue
        if annotation_pack is None:
            continue
        resolved_entries = resolve_protein_ids((protein_id,), annotation_pack)
        for resolved in resolved_entries:
            if resolved.resolved_accession is None:
                continue
            resolved_matches = lookup.get(
                canonicalize_protein_reference(resolved.resolved_accession),
                (),
            )
            if not resolved_matches:
                continue
            entries.extend(
                _build_entries(
                    protein_id=protein_id,
                    matches=tuple(resolved_matches),
                )
            )

    deduplicated_entries = tuple(
        sorted(
            {
                (
                    entry.protein_id,
                    entry.term_id,
                    entry.term_name,
                    entry.source,
                    entry.evidence_type,
                ): entry
                for entry in entries
            }.values(),
            key=lambda entry: (
                entry.protein_id,
                entry.term_id,
                entry.source,
                entry.evidence_type,
            ),
        )
    )
    return DiseaseTermResolutionReport(
        entries=deduplicated_entries,
        summary=DiseaseTermResolutionSummary(
            protein_count=len(protein_ids),
            resolved_protein_count=len({entry.protein_id for entry in deduplicated_entries}),
            term_count=len({(entry.term_id, entry.source) for entry in deduplicated_entries}),
            disease_term_count=sum(
                1 for entry in deduplicated_entries if entry.evidence_type == "disease_term"
            ),
            phenotype_term_count=sum(
                1
                for entry in deduplicated_entries
                if entry.evidence_type == "phenotype_term"
            ),
            source_filtered_row_count=source_filtered_row_count,
        ),
        note=(
            "disease and phenotype resolution preserves only explicitly sourced "
            "annotations, keeps phenotype and disease evidence types separate, "
            "and refuses to emit source-less rows as reviewable biological terms"
        ),
    )


def render_disease_term_resolution_tsv(
    entries: tuple[DiseaseTermResolutionEntry, ...],
) -> str:
    """Render disease and phenotype resolution rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("protein_id", "term_id", "term_name", "source", "evidence_type"))
    for entry in entries:
        writer.writerow(
            (
                entry.protein_id,
                entry.term_id,
                entry.term_name or "",
                entry.source,
                entry.evidence_type,
            )
        )
    return handle.getvalue()


def _normalize_disease_pack(
    disease_pack: AnnotationPack | tuple[BiologicalContextRecord, ...],
) -> tuple[tuple[BiologicalContextRecord, ...], AnnotationPack | None]:
    if isinstance(disease_pack, AnnotationPack):
        return disease_pack.disease_terms, disease_pack
    return disease_pack, None


def _build_entries(
    *,
    protein_id: str,
    matches: tuple[BiologicalContextRecord, ...],
) -> tuple[DiseaseTermResolutionEntry, ...]:
    return tuple(
        DiseaseTermResolutionEntry(
            protein_id=protein_id,
            term_id=record.context_id,
            term_name=record.context_name,
            source=_source_value(record) or "",
            evidence_type=record.context_kind.value,
        )
        for record in sorted(
            matches,
            key=lambda entry: (
                entry.context_id,
                entry.context_kind.value,
                _source_value(entry) or "",
            ),
        )
    )


def _source_value(record: BiologicalContextRecord) -> str | None:
    if record.source_accession:
        return record.source_accession
    if record.source_name:
        return record.source_name
    return None
