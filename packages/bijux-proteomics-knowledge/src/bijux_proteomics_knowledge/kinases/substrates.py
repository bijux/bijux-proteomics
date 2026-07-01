# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Exact kinase-substrate resolution over curated kinase packs."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
import re
from typing import cast

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.annotation_packs import AnnotationPack
from bijux_proteomics.interpretation.regulator_inference import (
    RegulatorEvidenceRecord,
    RegulatorEvidenceType,
)
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.identity.proteins import (
    ProteinIdentityResolutionStatus,
    resolve_protein_ids,
)


class KinaseSubstrateMatchType(StrEnum):
    """Stable kinase-substrate match classes ordered by evidence strength."""

    EXACT_ACCESSION_SITE = "exact_accession_site"
    ANNOTATION_IDENTIFIER_SITE_EQUIVALENT = "annotation_identifier_site_equivalent"
    GENE_SYMBOL_SITE_EQUIVALENT = "gene_symbol_site_equivalent"


class KinaseSubstrateResolutionEntry(JsonModel):
    """One resolved kinase-substrate site annotation row."""

    model_config = ConfigDict(extra="forbid")

    site_id: str = Field(..., min_length=1)
    kinase: str = Field(..., min_length=1)
    match_type: KinaseSubstrateMatchType
    annotation_source: str = Field(..., min_length=1)


class KinaseSubstrateResolutionSummary(JsonModel):
    """Stable summary over exact kinase-substrate resolution."""

    model_config = ConfigDict(extra="forbid")

    site_count: int = Field(..., ge=0)
    resolved_site_count: int = Field(..., ge=0)
    exact_match_count: int = Field(..., ge=0)
    annotation_identifier_match_count: int = Field(..., ge=0)
    gene_symbol_match_count: int = Field(..., ge=0)


class KinaseSubstrateResolutionReport(JsonModel):
    """Owned report over resolved kinase-substrate annotations."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[KinaseSubstrateResolutionEntry, ...] = Field(default_factory=tuple)
    summary: KinaseSubstrateResolutionSummary
    note: str = Field(..., min_length=1)


def resolve_kinase_substrates(
    ptm_sites: tuple[str, ...],
    kinase_pack: AnnotationPack | tuple[RegulatorEvidenceRecord, ...],
) -> KinaseSubstrateResolutionReport:
    """Resolve PTM sites onto curated kinase-substrate evidence rows.

    Inputs:
    ``ptm_sites`` are the PTM site identifiers to ground and ``kinase_pack``
    supplies curated kinase-substrate evidence rows or an annotation pack.

    Outputs:
    Returns one ``KinaseSubstrateResolutionReport`` with resolved kinase-site
    matches and match-type summary counts.

    Failure Modes:
    This function does not raise governed public exceptions under normal typed
    input use.

    Scientific Caveats:
    Matches require exact site-position agreement against the supplied curated
    evidence; they do not prove kinase activity in the measured sample.
    """

    substrate_records, annotation_pack = _normalize_kinase_pack(kinase_pack)
    exact_lookup: dict[tuple[str, int], list[RegulatorEvidenceRecord]] = {}
    for record in substrate_records:
        if record.evidence_type is not RegulatorEvidenceType.KINASE_SUBSTRATE:
            continue
        site_parts = _parse_site_id(record.site_key)
        if site_parts is None:
            continue
        exact_lookup.setdefault(
            (site_parts.canonical_protein_ref, site_parts.position),
            [],
        ).append(record)

    entries: list[KinaseSubstrateResolutionEntry] = []
    for site_id in ptm_sites:
        site_parts = _parse_site_id(site_id)
        if site_parts is None:
            continue
        direct_matches = exact_lookup.get(
            (site_parts.canonical_protein_ref, site_parts.position),
            (),
        )
        if direct_matches:
            entries.extend(
                _build_entries(
                    site_id=site_id,
                    matches=tuple(direct_matches),
                    match_type=KinaseSubstrateMatchType.EXACT_ACCESSION_SITE,
                )
            )
            continue
        if annotation_pack is None:
            continue
        resolved_entries = resolve_protein_ids(
            (site_parts.protein_id,), annotation_pack
        )
        for resolved in resolved_entries:
            if resolved.resolved_accession is None:
                continue
            if (
                resolved.resolution_status
                is ProteinIdentityResolutionStatus.EXACT_ACCESSION
            ):
                continue
            resolved_matches = exact_lookup.get(
                (
                    canonicalize_protein_reference(resolved.resolved_accession),
                    site_parts.position,
                ),
                (),
            )
            if not resolved_matches:
                continue
            match_type = _resolved_match_type(resolved.resolution_status)
            if match_type is None:
                continue
            entries.extend(
                _build_entries(
                    site_id=site_id,
                    matches=tuple(resolved_matches),
                    match_type=match_type,
                )
            )

    sorted_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.site_id,
                _match_rank(entry.match_type),
                entry.kinase,
                entry.annotation_source,
            ),
        )
    )
    return KinaseSubstrateResolutionReport(
        entries=sorted_entries,
        summary=KinaseSubstrateResolutionSummary(
            site_count=len(ptm_sites),
            resolved_site_count=len({entry.site_id for entry in sorted_entries}),
            exact_match_count=sum(
                1
                for entry in sorted_entries
                if entry.match_type is KinaseSubstrateMatchType.EXACT_ACCESSION_SITE
            ),
            annotation_identifier_match_count=sum(
                1
                for entry in sorted_entries
                if entry.match_type
                is KinaseSubstrateMatchType.ANNOTATION_IDENTIFIER_SITE_EQUIVALENT
            ),
            gene_symbol_match_count=sum(
                1
                for entry in sorted_entries
                if entry.match_type
                is KinaseSubstrateMatchType.GENE_SYMBOL_SITE_EQUIVALENT
            ),
        ),
        note=(
            "kinase-substrate resolution requires exact residue-position agreement "
            "and preserves weaker gene-symbol or annotation-identifier equivalents "
            "as lower-confidence match types instead of collapsing them into exact "
            "accession-site evidence"
        ),
    )


def render_kinase_substrate_resolution_tsv(
    entries: tuple[KinaseSubstrateResolutionEntry, ...],
) -> str:
    """Render kinase-substrate resolution rows as TSV.

    Inputs:
    ``entries`` must be the kinase-substrate rows to serialize.

    Outputs:
    Returns one TSV string with the governed kinase-substrate resolution
    columns.

    Failure Modes:
    This function does not raise governed public exceptions under normal typed
    input use.

    Scientific Caveats:
    The TSV serializes resolved kinase-site evidence only; it does not add new
    causal or mechanistic interpretation.
    """

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("site_id", "kinase", "match_type", "annotation_source"))
    for entry in entries:
        writer.writerow(
            (
                entry.site_id,
                entry.kinase,
                entry.match_type.value,
                entry.annotation_source,
            )
        )
    return handle.getvalue()


class _ParsedSiteId(JsonModel):
    model_config = ConfigDict(extra="forbid")

    site_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    canonical_protein_ref: str = Field(..., min_length=1)
    position: int = Field(..., ge=1)


def _normalize_kinase_pack(
    kinase_pack: AnnotationPack | tuple[RegulatorEvidenceRecord, ...],
) -> tuple[tuple[RegulatorEvidenceRecord, ...], AnnotationPack | None]:
    if isinstance(kinase_pack, AnnotationPack):
        return kinase_pack.kinase_substrates, kinase_pack
    return kinase_pack, None


def _parse_site_id(site_id: str | None) -> _ParsedSiteId | None:
    if site_id is None:
        return None
    tokens = [token.strip() for token in site_id.split(":")]
    residue_index = next(
        (
            index
            for index in range(len(tokens) - 1, -1, -1)
            if re.fullmatch(r"[A-Za-z]+(\d+)", tokens[index]) is not None
        ),
        None,
    )
    if residue_index is None or residue_index == 0:
        return None
    protein_id = ":".join(tokens[:residue_index]).strip()
    residue_position = tokens[residue_index]
    if not protein_id:
        return None
    match = re.fullmatch(r"[A-Za-z]+(\d+)", residue_position)
    if match is None:
        return None
    return _ParsedSiteId(
        site_id=site_id,
        protein_id=protein_id,
        canonical_protein_ref=canonicalize_protein_reference(protein_id),
        position=int(match.group(1)),
    )


def _build_entries(
    *,
    site_id: str,
    matches: tuple[RegulatorEvidenceRecord, ...],
    match_type: KinaseSubstrateMatchType,
) -> tuple[KinaseSubstrateResolutionEntry, ...]:
    return tuple(
        KinaseSubstrateResolutionEntry(
            site_id=site_id,
            kinase=match.regulator,
            match_type=match_type,
            annotation_source=_annotation_source(match),
        )
        for match in sorted(
            matches,
            key=lambda entry: (
                entry.regulator,
                entry.source_accession or "",
                entry.source_name or "",
            ),
        )
    )


def _annotation_source(match: RegulatorEvidenceRecord) -> str:
    if match.source_accession:
        return cast(str, match.source_accession)
    if match.source_name:
        return cast(str, match.source_name)
    return "curated_kinase_pack"


def _resolved_match_type(
    status: ProteinIdentityResolutionStatus,
) -> KinaseSubstrateMatchType | None:
    if status is ProteinIdentityResolutionStatus.ANNOTATION_IDENTIFIER:
        return KinaseSubstrateMatchType.ANNOTATION_IDENTIFIER_SITE_EQUIVALENT
    if status is ProteinIdentityResolutionStatus.GENE_SYMBOL:
        return KinaseSubstrateMatchType.GENE_SYMBOL_SITE_EQUIVALENT
    return None


def _match_rank(match_type: KinaseSubstrateMatchType) -> int:
    ranks = {
        KinaseSubstrateMatchType.EXACT_ACCESSION_SITE: 0,
        KinaseSubstrateMatchType.ANNOTATION_IDENTIFIER_SITE_EQUIVALENT: 1,
        KinaseSubstrateMatchType.GENE_SYMBOL_SITE_EQUIVALENT: 2,
    }
    return ranks[match_type]
