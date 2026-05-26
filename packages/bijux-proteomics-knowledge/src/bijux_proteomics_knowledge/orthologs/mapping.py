# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Cross-species ortholog mapping over curated ortholog packs."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.annotation_packs import AnnotationPack
from bijux_proteomics.interpretation.ortholog_mapping import OrthologRecord
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.identity.proteins import (
    ProteinIdResolutionEntry,
    ProteinIdentityResolutionStatus,
    resolve_protein_ids,
)


class CrossSpeciesOrthologEvidenceStatus(StrEnum):
    """Source-evidence status behind one cross-species ortholog row."""

    EXACT_ACCESSION = "exact_accession"
    CURATED_ALIAS = "curated_alias"
    AMBIGUOUS_SOURCE_IDENTIFIER = "ambiguous_source_identifier"
    UNRESOLVED_SOURCE_IDENTIFIER = "unresolved_source_identifier"


class CrossSpeciesOrthologAmbiguity(StrEnum):
    """Ortholog ambiguity surface for one emitted cross-species row."""

    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"
    UNMAPPED = "unmapped"


class CrossSpeciesOrthologEntry(JsonModel):
    """One curated cross-species ortholog mapping row."""

    model_config = ConfigDict(extra="forbid")

    source_protein: str = Field(..., min_length=1)
    target_ortholog: str | None = None
    evidence_status: CrossSpeciesOrthologEvidenceStatus
    ambiguity: CrossSpeciesOrthologAmbiguity


class CrossSpeciesOrthologSummary(JsonModel):
    """Stable summary over one cross-species ortholog mapping run."""

    model_config = ConfigDict(extra="forbid")

    input_identifier_count: int = Field(..., ge=0)
    emitted_entry_count: int = Field(..., ge=0)
    mapped_entry_count: int = Field(..., ge=0)
    unmapped_entry_count: int = Field(..., ge=0)
    ambiguous_source_identifier_count: int = Field(..., ge=0)
    unresolved_source_identifier_count: int = Field(..., ge=0)
    one_to_many_count: int = Field(..., ge=0)
    many_to_one_count: int = Field(..., ge=0)
    many_to_many_count: int = Field(..., ge=0)


class CrossSpeciesOrthologReport(JsonModel):
    """Owned report over one species-aware ortholog mapping request."""

    model_config = ConfigDict(extra="forbid")

    source_species: str = Field(..., min_length=1)
    target_species: str = Field(..., min_length=1)
    entries: tuple[CrossSpeciesOrthologEntry, ...] = Field(default_factory=tuple)
    summary: CrossSpeciesOrthologSummary
    note: str = Field(..., min_length=1)


def map_cross_species_orthologs(
    protein_ids: tuple[str, ...],
    ortholog_pack: AnnotationPack | tuple[OrthologRecord, ...],
    *,
    source_species: str,
    target_species: str,
) -> CrossSpeciesOrthologReport:
    """Map source-species proteins onto curated target-species ortholog edges.

    Inputs:
    ``protein_ids`` are the source identifiers to map, ``ortholog_pack``
    supplies curated ortholog edges or an annotation pack, and
    ``source_species`` plus ``target_species`` define the mapping direction.

    Outputs:
    Returns one ``CrossSpeciesOrthologReport`` with mapped target orthologs,
    ambiguity states, and evidence-status summaries.

    Failure Modes:
    This function does not raise governed public exceptions under normal typed
    input use.

    Scientific Caveats:
    The mapping depends entirely on the supplied curated ortholog edges and
    alias resolution; it does not prove functional equivalence across species.
    """

    ortholog_records, annotation_pack = _normalize_ortholog_pack(ortholog_pack)
    filtered_records = tuple(
        record
        for record in ortholog_records
        if _normalize_species(record.source_species) == _normalize_species(source_species)
        and _normalize_species(record.target_species) == _normalize_species(target_species)
    )
    source_to_targets: dict[str, tuple[OrthologRecord, ...]] = {}
    target_to_sources: dict[str, set[str]] = {}
    for record in filtered_records:
        source_to_targets.setdefault(record.source_protein_ref, tuple())
        source_to_targets[record.source_protein_ref] = source_to_targets[
            record.source_protein_ref
        ] + (record,)
        target_to_sources.setdefault(record.target_protein_ref, set()).add(
            record.source_protein_ref
        )

    source_entries = _resolve_source_entries(
        protein_ids=protein_ids,
        annotation_pack=annotation_pack,
        source_species=source_species,
    )
    entries: list[CrossSpeciesOrthologEntry] = []
    for source_entry in source_entries:
        source_protein = source_entry.resolved_accession or source_entry.input_id
        evidence_status = _evidence_status(source_entry.resolution_status)
        if source_entry.resolution_status is ProteinIdentityResolutionStatus.UNRESOLVED:
            entries.append(
                CrossSpeciesOrthologEntry(
                    source_protein=source_protein,
                    target_ortholog=None,
                    evidence_status=evidence_status,
                    ambiguity=CrossSpeciesOrthologAmbiguity.UNMAPPED,
                )
            )
            continue

        relationships = tuple(
            sorted(
                source_to_targets.get(source_entry.resolved_accession or "", ()),
                key=lambda record: record.target_protein_ref,
            )
        )
        if not relationships:
            entries.append(
                CrossSpeciesOrthologEntry(
                    source_protein=source_protein,
                    target_ortholog=None,
                    evidence_status=evidence_status,
                    ambiguity=CrossSpeciesOrthologAmbiguity.UNMAPPED,
                )
            )
            continue

        source_match_count = len(relationships)
        for relationship in relationships:
            target_match_count = len(target_to_sources.get(relationship.target_protein_ref, set()))
            entries.append(
                CrossSpeciesOrthologEntry(
                    source_protein=source_protein,
                    target_ortholog=relationship.target_protein_ref,
                    evidence_status=evidence_status,
                    ambiguity=_classify_ambiguity(
                        source_match_count=source_match_count,
                        target_match_count=target_match_count,
                    ),
                )
            )

    return CrossSpeciesOrthologReport(
        source_species=source_species,
        target_species=target_species,
        entries=tuple(entries),
        summary=CrossSpeciesOrthologSummary(
            input_identifier_count=len(protein_ids),
            emitted_entry_count=len(entries),
            mapped_entry_count=sum(1 for entry in entries if entry.target_ortholog),
            unmapped_entry_count=sum(1 for entry in entries if entry.target_ortholog is None),
            ambiguous_source_identifier_count=sum(
                1
                for entry in entries
                if entry.evidence_status
                is CrossSpeciesOrthologEvidenceStatus.AMBIGUOUS_SOURCE_IDENTIFIER
            ),
            unresolved_source_identifier_count=sum(
                1
                for entry in entries
                if entry.evidence_status
                is CrossSpeciesOrthologEvidenceStatus.UNRESOLVED_SOURCE_IDENTIFIER
            ),
            one_to_many_count=sum(
                1
                for entry in entries
                if entry.ambiguity is CrossSpeciesOrthologAmbiguity.ONE_TO_MANY
            ),
            many_to_one_count=sum(
                1
                for entry in entries
                if entry.ambiguity is CrossSpeciesOrthologAmbiguity.MANY_TO_ONE
            ),
            many_to_many_count=sum(
                1
                for entry in entries
                if entry.ambiguity is CrossSpeciesOrthologAmbiguity.MANY_TO_MANY
            ),
        ),
        note=(
            "cross-species ortholog mapping resolves source identifiers within the "
            "declared source species when curated features are available, but it "
            "creates target mappings only from explicit ortholog edges and keeps "
            "one-to-many and many-to-many ambiguity visible instead of collapsing "
            "those relationships into a single winner"
        ),
    )


def render_cross_species_ortholog_tsv(
    entries: tuple[CrossSpeciesOrthologEntry, ...],
) -> str:
    """Render cross-species ortholog rows as TSV.

    Inputs:
    ``entries`` must be the ortholog mapping rows to serialize.

    Outputs:
    Returns one TSV string with the governed cross-species ortholog columns.

    Failure Modes:
    This function does not raise governed public exceptions under normal typed
    input use.

    Scientific Caveats:
    The TSV serializes already classified ortholog relationships only; it does
    not collapse ambiguity or infer conserved function.
    """

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "source_protein",
            "target_ortholog",
            "evidence_status",
            "ambiguity",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.source_protein,
                entry.target_ortholog or "",
                entry.evidence_status.value,
                entry.ambiguity.value,
            )
        )
    return handle.getvalue()


def _normalize_ortholog_pack(
    ortholog_pack: AnnotationPack | tuple[OrthologRecord, ...],
) -> tuple[tuple[OrthologRecord, ...], AnnotationPack | None]:
    if isinstance(ortholog_pack, AnnotationPack):
        return ortholog_pack.orthologs, ortholog_pack
    return ortholog_pack, None


def _resolve_source_entries(
    *,
    protein_ids: tuple[str, ...],
    annotation_pack: AnnotationPack | None,
    source_species: str,
) -> tuple[ProteinIdResolutionEntry, ...]:
    if annotation_pack is not None:
        return resolve_protein_ids(
            protein_ids,
            annotation_pack,
            species=source_species,
        )
    return tuple(
        ProteinIdResolutionEntry(
            input_id=input_id,
            resolved_accession=canonicalize_protein_reference(input_id),
            gene=None,
            species=source_species,
            resolution_status=ProteinIdentityResolutionStatus.EXACT_ACCESSION,
            ambiguity_count=1,
        )
        for input_id in protein_ids
    )


def _evidence_status(
    resolution_status: ProteinIdentityResolutionStatus,
) -> CrossSpeciesOrthologEvidenceStatus:
    if resolution_status is ProteinIdentityResolutionStatus.EXACT_ACCESSION:
        return CrossSpeciesOrthologEvidenceStatus.EXACT_ACCESSION
    if resolution_status is ProteinIdentityResolutionStatus.UNRESOLVED:
        return CrossSpeciesOrthologEvidenceStatus.UNRESOLVED_SOURCE_IDENTIFIER
    if resolution_status is ProteinIdentityResolutionStatus.AMBIGUOUS_ALIAS:
        return CrossSpeciesOrthologEvidenceStatus.AMBIGUOUS_SOURCE_IDENTIFIER
    return CrossSpeciesOrthologEvidenceStatus.CURATED_ALIAS


def _classify_ambiguity(
    *,
    source_match_count: int,
    target_match_count: int,
) -> CrossSpeciesOrthologAmbiguity:
    if source_match_count == 1 and target_match_count == 1:
        return CrossSpeciesOrthologAmbiguity.ONE_TO_ONE
    if source_match_count > 1 and target_match_count > 1:
        return CrossSpeciesOrthologAmbiguity.MANY_TO_MANY
    if source_match_count > 1:
        return CrossSpeciesOrthologAmbiguity.ONE_TO_MANY
    return CrossSpeciesOrthologAmbiguity.MANY_TO_ONE


def _normalize_species(species: str) -> str:
    return " ".join(species.strip().casefold().split())
