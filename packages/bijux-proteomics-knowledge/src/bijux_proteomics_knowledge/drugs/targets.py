# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Drug-target resolution over curated drug annotation packs."""

from __future__ import annotations

import csv
from enum import StrEnum
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


class DrugTargetRelationshipType(StrEnum):
    """Stable relationship labels for curated drug-protein annotations."""

    DIRECT_TARGET = "direct_target"
    INDIRECT_PATHWAY_NEIGHBOR = "indirect_pathway_neighbor"


class DrugTargetResolutionEntry(JsonModel):
    """One resolved drug-protein relationship row."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    drug: str = Field(..., min_length=1)
    relationship_type: DrugTargetRelationshipType
    direct_target: bool
    annotation_source: str = Field(..., min_length=1)


class DrugTargetResolutionSummary(JsonModel):
    """Stable summary over resolved drug-target relationships."""

    model_config = ConfigDict(extra="forbid")

    protein_count: int = Field(..., ge=0)
    resolved_protein_count: int = Field(..., ge=0)
    drug_count: int = Field(..., ge=0)
    direct_target_count: int = Field(..., ge=0)
    indirect_pathway_neighbor_count: int = Field(..., ge=0)


class DrugTargetResolutionReport(JsonModel):
    """Owned report over curated drug-target relationships."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[DrugTargetResolutionEntry, ...] = Field(default_factory=tuple)
    summary: DrugTargetResolutionSummary
    note: str = Field(..., min_length=1)


def resolve_drug_targets(
    protein_ids: tuple[str, ...],
    drug_pack: AnnotationPack | tuple[BiologicalContextRecord, ...],
) -> DrugTargetResolutionReport:
    """Resolve proteins onto curated drug-target annotations.

    Inputs:
    ``protein_ids`` are the identifiers to ground and ``drug_pack`` supplies
    curated drug-target context rows or an annotation pack.

    Outputs:
    Returns one ``DrugTargetResolutionReport`` with resolved drug-target
    relationships and direct-versus-indirect summary counts.

    Failure Modes:
    This function does not raise governed public exceptions under normal typed
    input use.

    Scientific Caveats:
    The report reflects curated annotation relationships only; it does not prove
    compound activity, dosing relevance, or sample-specific response.
    """

    drug_records, annotation_pack = _normalize_drug_pack(drug_pack)
    direct_lookup: dict[str, list[BiologicalContextRecord]] = {}
    for record in drug_records:
        if record.context_kind is not BiologicalContextKind.DRUG_TARGET:
            continue
        canonical_ref = canonicalize_protein_reference(record.protein_ref)
        direct_lookup.setdefault(canonical_ref, []).append(record)

    entries: list[DrugTargetResolutionEntry] = []
    for protein_id in protein_ids:
        direct_matches = direct_lookup.get(
            canonicalize_protein_reference(protein_id), ()
        )
        if direct_matches:
            entries.extend(
                _build_entries(protein_id=protein_id, matches=tuple(direct_matches))
            )
            continue
        if annotation_pack is None:
            continue
        resolved_entries = resolve_protein_ids((protein_id,), annotation_pack)
        for resolved in resolved_entries:
            if resolved.resolved_accession is None:
                continue
            resolved_matches = direct_lookup.get(
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
                    entry.drug,
                    entry.relationship_type,
                    entry.direct_target,
                    entry.annotation_source,
                ): entry
                for entry in entries
            }.values(),
            key=lambda entry: (
                entry.protein_id,
                entry.drug,
                _relationship_rank(entry.relationship_type),
                entry.annotation_source,
            ),
        )
    )
    return DrugTargetResolutionReport(
        entries=deduplicated_entries,
        summary=DrugTargetResolutionSummary(
            protein_count=len(protein_ids),
            resolved_protein_count=len(
                {entry.protein_id for entry in deduplicated_entries}
            ),
            drug_count=len({entry.drug for entry in deduplicated_entries}),
            direct_target_count=sum(
                1 for entry in deduplicated_entries if entry.direct_target
            ),
            indirect_pathway_neighbor_count=sum(
                1 for entry in deduplicated_entries if not entry.direct_target
            ),
        ),
        note=(
            "drug-target resolution preserves only explicitly direct annotations as "
            "direct_target=true and keeps pathway-neighbor style rows separate as "
            "indirect relationships instead of promoting them into direct targets"
        ),
    )


def render_drug_target_resolution_tsv(
    entries: tuple[DrugTargetResolutionEntry, ...],
) -> str:
    """Render drug-target resolution rows as TSV.

    Inputs:
    ``entries`` must be the drug-target rows to serialize.

    Outputs:
    Returns one TSV string with the governed drug-target resolution columns.

    Failure Modes:
    This function does not raise governed public exceptions under normal typed
    input use.

    Scientific Caveats:
    The TSV serializes previously resolved relationships only; it does not add
    pharmacologic interpretation or ranking.
    """

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_id",
            "drug",
            "relationship_type",
            "direct_target",
            "annotation_source",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.protein_id,
                entry.drug,
                entry.relationship_type.value,
                str(entry.direct_target).lower(),
                entry.annotation_source,
            )
        )
    return handle.getvalue()


def _normalize_drug_pack(
    drug_pack: AnnotationPack | tuple[BiologicalContextRecord, ...],
) -> tuple[tuple[BiologicalContextRecord, ...], AnnotationPack | None]:
    if isinstance(drug_pack, AnnotationPack):
        return drug_pack.drug_targets, drug_pack
    return drug_pack, None


def _build_entries(
    *,
    protein_id: str,
    matches: tuple[BiologicalContextRecord, ...],
) -> tuple[DrugTargetResolutionEntry, ...]:
    direct_pairs = {
        (_drug_name(record), _annotation_source(record))
        for record in matches
        if _relationship_type(record) is DrugTargetRelationshipType.DIRECT_TARGET
    }
    resolved_entries: list[DrugTargetResolutionEntry] = []
    for record in sorted(
        matches,
        key=lambda entry: (
            _drug_name(entry),
            _relationship_rank(_relationship_type(entry)),
            _annotation_source(entry),
        ),
    ):
        relationship_type = _relationship_type(record)
        drug_name = _drug_name(record)
        annotation_source = _annotation_source(record)
        if (
            relationship_type is DrugTargetRelationshipType.INDIRECT_PATHWAY_NEIGHBOR
            and (drug_name, annotation_source) in direct_pairs
        ):
            continue
        resolved_entries.append(
            DrugTargetResolutionEntry(
                protein_id=protein_id,
                drug=drug_name,
                relationship_type=relationship_type,
                direct_target=(
                    relationship_type is DrugTargetRelationshipType.DIRECT_TARGET
                ),
                annotation_source=annotation_source,
            )
        )
    return tuple(resolved_entries)


def _relationship_type(record: BiologicalContextRecord) -> DrugTargetRelationshipType:
    for key in (
        "relationship_type",
        "relationship",
        "target_type",
        "target_relationship",
    ):
        value = record.metadata.get(key)
        if value is None:
            continue
        normalized_value = value.strip().casefold().replace(" ", "_").replace("-", "_")
        if normalized_value in {
            "indirect_pathway_neighbor",
            "pathway_neighbor",
            "indirect_neighbor",
            "neighbor",
        }:
            return DrugTargetRelationshipType.INDIRECT_PATHWAY_NEIGHBOR
        if normalized_value in {
            "direct_target",
            "direct",
        }:
            return DrugTargetRelationshipType.DIRECT_TARGET
    evidence = (record.evidence or "").strip().casefold()
    if "pathway neighbor" in evidence or "indirect neighbor" in evidence:
        return DrugTargetRelationshipType.INDIRECT_PATHWAY_NEIGHBOR
    return DrugTargetRelationshipType.DIRECT_TARGET


def _drug_name(record: BiologicalContextRecord) -> str:
    if record.context_name:
        return record.context_name
    return record.context_id


def _annotation_source(record: BiologicalContextRecord) -> str:
    if record.source_accession:
        return record.source_accession
    if record.source_name:
        return record.source_name
    return "curated_drug_pack"


def _relationship_rank(relationship_type: DrugTargetRelationshipType) -> int:
    ranks = {
        DrugTargetRelationshipType.DIRECT_TARGET: 0,
        DrugTargetRelationshipType.INDIRECT_PATHWAY_NEIGHBOR: 1,
    }
    return ranks[relationship_type]
