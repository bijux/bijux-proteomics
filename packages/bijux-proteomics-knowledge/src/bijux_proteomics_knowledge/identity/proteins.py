# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein identity resolution over curated annotation-pack features."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.annotation_packs import AnnotationPack
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationRecord,
)
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel


class ProteinIdentityResolutionStatus(StrEnum):
    """Stable resolution status for one input protein identifier."""

    EXACT_ACCESSION = "exact_accession"
    ANNOTATION_IDENTIFIER = "annotation_identifier"
    GENE_SYMBOL = "gene_symbol"
    AMBIGUOUS_ALIAS = "ambiguous_alias"
    UNRESOLVED = "unresolved"


class ProteinIdResolutionEntry(JsonModel):
    """One resolved or unresolved protein-identity row."""

    model_config = ConfigDict(extra="forbid")

    input_id: str = Field(..., min_length=1)
    resolved_accession: str | None = None
    gene: str | None = None
    species: str | None = None
    resolution_status: ProteinIdentityResolutionStatus
    ambiguity_count: int = Field(..., ge=0)


def resolve_protein_ids(
    ids: tuple[str, ...],
    annotation_pack: AnnotationPack,
    species: str | None = None,
) -> tuple[ProteinIdResolutionEntry, ...]:
    """Resolve protein ids against curated annotation-pack features."""

    normalized_species = _normalize_species(species)
    features = annotation_pack.protein_features
    by_accession = {
        feature.protein_ref: feature for feature in features
    }
    by_annotation_identifier: dict[str, list[ProteinAnnotationRecord]] = {}
    by_gene_symbol: dict[str, list[ProteinAnnotationRecord]] = {}
    for feature in features:
        if feature.annotation_identifier:
            by_annotation_identifier.setdefault(
                feature.annotation_identifier.strip().casefold(),
                [],
            ).append(feature)
        if feature.gene_symbol:
            by_gene_symbol.setdefault(
                feature.gene_symbol.strip().casefold(),
                [],
            ).append(feature)

    entries: list[ProteinIdResolutionEntry] = []
    for input_id in ids:
        canonical_input = canonicalize_protein_reference(input_id)
        accession_match = by_accession.get(canonical_input)
        if accession_match is not None and _matches_species(
            accession_match,
            normalized_species=normalized_species,
        ):
            entries.append(
                _build_entry(
                    input_id=input_id,
                    feature=accession_match,
                    resolution_status=ProteinIdentityResolutionStatus.EXACT_ACCESSION,
                    ambiguity_count=1,
                )
            )
            continue

        annotation_matches = _filter_species(
            by_annotation_identifier.get(input_id.strip().casefold(), ()),
            normalized_species=normalized_species,
        )
        if annotation_matches:
            entries.extend(
                _matched_entries(
                    input_id=input_id,
                    matches=annotation_matches,
                    singular_status=ProteinIdentityResolutionStatus.ANNOTATION_IDENTIFIER,
                )
            )
            continue

        gene_matches = _filter_species(
            by_gene_symbol.get(input_id.strip().casefold(), ()),
            normalized_species=normalized_species,
        )
        if gene_matches:
            entries.extend(
                _matched_entries(
                    input_id=input_id,
                    matches=gene_matches,
                    singular_status=ProteinIdentityResolutionStatus.GENE_SYMBOL,
                )
            )
            continue

        entries.append(
            ProteinIdResolutionEntry(
                input_id=input_id,
                resolved_accession=None,
                gene=None,
                species=species,
                resolution_status=ProteinIdentityResolutionStatus.UNRESOLVED,
                ambiguity_count=0,
            )
        )
    return tuple(entries)


def render_protein_id_resolution_tsv(
    entries: tuple[ProteinIdResolutionEntry, ...],
) -> str:
    """Render protein-id resolution rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "input_id",
            "resolved_accession",
            "gene",
            "species",
            "resolution_status",
            "ambiguity_count",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.input_id,
                entry.resolved_accession or "",
                entry.gene or "",
                entry.species or "",
                entry.resolution_status.value,
                entry.ambiguity_count,
            )
        )
    return handle.getvalue()


def _matched_entries(
    *,
    input_id: str,
    matches: tuple[ProteinAnnotationRecord, ...],
    singular_status: ProteinIdentityResolutionStatus,
) -> tuple[ProteinIdResolutionEntry, ...]:
    ambiguity_count = len(matches)
    status = (
        singular_status
        if ambiguity_count == 1
        else ProteinIdentityResolutionStatus.AMBIGUOUS_ALIAS
    )
    return tuple(
        _build_entry(
            input_id=input_id,
            feature=feature,
            resolution_status=status,
            ambiguity_count=ambiguity_count,
        )
        for feature in matches
    )


def _build_entry(
    *,
    input_id: str,
    feature: ProteinAnnotationRecord,
    resolution_status: ProteinIdentityResolutionStatus,
    ambiguity_count: int,
) -> ProteinIdResolutionEntry:
    return ProteinIdResolutionEntry(
        input_id=input_id,
        resolved_accession=feature.protein_ref,
        gene=feature.gene_symbol,
        species=feature.organism,
        resolution_status=resolution_status,
        ambiguity_count=ambiguity_count,
    )


def _filter_species(
    features: list[ProteinAnnotationRecord] | tuple[ProteinAnnotationRecord, ...],
    *,
    normalized_species: str | None,
) -> tuple[ProteinAnnotationRecord, ...]:
    if normalized_species is None:
        return tuple(features)
    return tuple(
        feature
        for feature in features
        if _matches_species(feature, normalized_species=normalized_species)
    )


def _matches_species(
    feature: ProteinAnnotationRecord,
    *,
    normalized_species: str | None,
) -> bool:
    if normalized_species is None:
        return True
    return _normalize_species(feature.organism) == normalized_species


def _normalize_species(species: str | None) -> str | None:
    if species is None:
        return None
    cleaned = species.strip()
    if cleaned == "":
        return None
    return " ".join(cleaned.casefold().split())
