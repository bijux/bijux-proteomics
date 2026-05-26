# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pathway membership resolution over curated pathway packs."""

from __future__ import annotations

import csv
from collections import defaultdict
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.annotation_packs import AnnotationPack
from bijux_proteomics.interpretation.pathway_enrichment import (
    PathwayMemberKind,
    PathwayMembershipRecord,
)
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.identity.proteins import (
    ProteinIdentityResolutionStatus,
    resolve_protein_ids,
)


class PathwayCoverageConfidenceStatus(StrEnum):
    """Confidence classification derived from matched pathway-member coverage."""

    HIGH_CONFIDENCE = "high_confidence"
    LOW_CONFIDENCE = "low_confidence"


class PathwayCoveragePolicy(JsonModel):
    """Coverage policy for pathway membership confidence."""

    model_config = ConfigDict(extra="forbid")

    minimum_coverage_fraction: float = Field(default=0.5, ge=0.0, le=1.0)


class PathwayMembershipResolutionEntry(JsonModel):
    """One pathway membership resolution row for one curated pathway."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    matched_members: tuple[str, ...] = Field(default_factory=tuple)
    missing_members: tuple[str, ...] = Field(default_factory=tuple)
    coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    unresolved_inputs: tuple[str, ...] = Field(default_factory=tuple)


class PathwayCoverageConfidenceEntry(JsonModel):
    """One coverage-derived confidence row for one pathway."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    matched_member_count: int = Field(..., ge=0)
    total_member_count: int = Field(..., ge=0)
    coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    confidence_status: PathwayCoverageConfidenceStatus


class PathwayMembershipResolutionSummary(JsonModel):
    """Stable summary over pathway membership resolution."""

    model_config = ConfigDict(extra="forbid")

    pathway_count: int = Field(..., ge=0)
    high_confidence_pathway_count: int = Field(..., ge=0)
    low_confidence_pathway_count: int = Field(..., ge=0)
    unresolved_input_count: int = Field(..., ge=0)


class PathwayMembershipResolutionReport(JsonModel):
    """Owned report over resolved pathway coverage and confidence."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PathwayMembershipResolutionEntry, ...] = Field(default_factory=tuple)
    confidence_entries: tuple[PathwayCoverageConfidenceEntry, ...] = Field(
        default_factory=tuple
    )
    summary: PathwayMembershipResolutionSummary
    note: str = Field(..., min_length=1)


def resolve_pathway_members(
    protein_ids: tuple[str, ...],
    pathway_pack: AnnotationPack | tuple[PathwayMembershipRecord, ...],
    *,
    policy: PathwayCoveragePolicy | None = None,
) -> PathwayMembershipResolutionReport:
    """Resolve input proteins onto curated pathway membership rows.

    Inputs:
    ``protein_ids`` are the identifiers to ground, ``pathway_pack`` supplies
    curated pathway membership rows, and ``policy`` optionally overrides the
    owned pathway coverage thresholds.

    Outputs:
    Returns one ``PathwayMembershipResolutionReport`` with matched members,
    missing members, unresolved inputs, and pathway confidence summaries.

    Failure Modes:
    This function does not raise governed public exceptions under normal typed
    input use.

    Scientific Caveats:
    Pathway confidence reflects only curated membership coverage and alias
    resolution; it does not prove pathway activation or causal direction.
    """

    active_policy = policy or PathwayCoveragePolicy()
    pathway_records, annotation_pack = _normalize_pathway_pack(pathway_pack)
    pathway_groups = _group_pathway_records(pathway_records)
    resolved_protein_refs, resolved_gene_symbols, unresolved_inputs = _resolved_inputs(
        protein_ids=protein_ids,
        annotation_pack=annotation_pack,
    )

    entries: list[PathwayMembershipResolutionEntry] = []
    confidence_entries: list[PathwayCoverageConfidenceEntry] = []
    for pathway_id in sorted(pathway_groups):
        records = pathway_groups[pathway_id]
        matched_members: list[str] = []
        missing_members: list[str] = []
        for record in records:
            member_label = _member_label(record)
            if _member_matches(
                record=record,
                resolved_protein_refs=resolved_protein_refs,
                resolved_gene_symbols=resolved_gene_symbols,
            ):
                matched_members.append(member_label)
            else:
                missing_members.append(member_label)

        total_member_count = len(records)
        coverage_fraction = (
            len(matched_members) / total_member_count if total_member_count > 0 else 0.0
        )
        confidence_status = _confidence_status(
            coverage_fraction=coverage_fraction,
            policy=active_policy,
        )
        entries.append(
            PathwayMembershipResolutionEntry(
                pathway_id=pathway_id,
                matched_members=tuple(sorted(matched_members)),
                missing_members=tuple(sorted(missing_members)),
                coverage_fraction=round(coverage_fraction, 4),
                unresolved_inputs=tuple(sorted(unresolved_inputs)),
            )
        )
        confidence_entries.append(
            PathwayCoverageConfidenceEntry(
                pathway_id=pathway_id,
                matched_member_count=len(matched_members),
                total_member_count=total_member_count,
                coverage_fraction=round(coverage_fraction, 4),
                confidence_status=confidence_status,
            )
        )

    return PathwayMembershipResolutionReport(
        entries=tuple(entries),
        confidence_entries=tuple(confidence_entries),
        summary=PathwayMembershipResolutionSummary(
            pathway_count=len(entries),
            high_confidence_pathway_count=sum(
                1
                for entry in confidence_entries
                if entry.confidence_status
                is PathwayCoverageConfidenceStatus.HIGH_CONFIDENCE
            ),
            low_confidence_pathway_count=sum(
                1
                for entry in confidence_entries
                if entry.confidence_status
                is PathwayCoverageConfidenceStatus.LOW_CONFIDENCE
            ),
            unresolved_input_count=len(unresolved_inputs),
        ),
        note=(
            "pathway membership resolution preserves matched and missing pathway "
            "members per pathway, keeps unresolved inputs explicit, and downgrades "
            "sparsely covered pathways to low confidence instead of treating all "
            "pathway hits as equally supported"
        ),
    )


def render_pathway_membership_resolution_tsv(
    entries: tuple[PathwayMembershipResolutionEntry, ...],
) -> str:
    """Render pathway membership resolution rows as TSV.

    Inputs:
    ``entries`` must be the pathway membership rows to serialize.

    Outputs:
    Returns one TSV string with the governed pathway membership columns.

    Failure Modes:
    This function does not raise governed public exceptions under normal typed
    input use.

    Scientific Caveats:
    The TSV preserves computed pathway coverage only; it does not add new
    biological interpretation or pathway scoring.
    """

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "matched_members",
            "missing_members",
            "coverage_fraction",
            "unresolved_inputs",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.pathway_id,
                ";".join(entry.matched_members),
                ";".join(entry.missing_members),
                _format_fraction(entry.coverage_fraction),
                ";".join(entry.unresolved_inputs),
            )
        )
    return handle.getvalue()


def _normalize_pathway_pack(
    pathway_pack: AnnotationPack | tuple[PathwayMembershipRecord, ...],
) -> tuple[tuple[PathwayMembershipRecord, ...], AnnotationPack | None]:
    if isinstance(pathway_pack, AnnotationPack):
        return pathway_pack.pathways, pathway_pack
    return pathway_pack, None


def _group_pathway_records(
    pathway_records: tuple[PathwayMembershipRecord, ...],
) -> dict[str, tuple[PathwayMembershipRecord, ...]]:
    grouped: dict[str, list[PathwayMembershipRecord]] = defaultdict(list)
    for record in pathway_records:
        grouped[record.pathway_id].append(record)
    return {
        pathway_id: tuple(
            sorted(
                records,
                key=lambda record: (
                    record.member_kind.value,
                    record.member_id,
                    record.source_name or "",
                    record.source_accession or "",
                ),
            )
        )
        for pathway_id, records in grouped.items()
    }


def _resolved_inputs(
    *,
    protein_ids: tuple[str, ...],
    annotation_pack: AnnotationPack | None,
) -> tuple[set[str], set[str], set[str]]:
    if annotation_pack is None:
        return (
            {canonicalize_protein_reference(protein_id) for protein_id in protein_ids},
            set(),
            set(),
        )

    entries = resolve_protein_ids(protein_ids, annotation_pack)
    resolved_protein_refs: set[str] = set()
    resolved_gene_symbols: set[str] = set()
    unresolved_inputs: set[str] = set()
    for entry in entries:
        if entry.resolution_status in {
            ProteinIdentityResolutionStatus.UNRESOLVED,
            ProteinIdentityResolutionStatus.AMBIGUOUS_ALIAS,
        }:
            unresolved_inputs.add(entry.input_id)
            continue
        assert entry.resolved_accession is not None
        resolved_protein_refs.add(canonicalize_protein_reference(entry.resolved_accession))
        if entry.gene:
            resolved_gene_symbols.add(entry.gene)
    return resolved_protein_refs, resolved_gene_symbols, unresolved_inputs


def _member_matches(
    *,
    record: PathwayMembershipRecord,
    resolved_protein_refs: set[str],
    resolved_gene_symbols: set[str],
) -> bool:
    if record.member_kind is PathwayMemberKind.PROTEIN:
        return canonicalize_protein_reference(record.member_id) in resolved_protein_refs
    return record.member_id in resolved_gene_symbols


def _member_label(record: PathwayMembershipRecord) -> str:
    return f"{record.member_kind.value}:{record.member_id}"


def _confidence_status(
    *,
    coverage_fraction: float,
    policy: PathwayCoveragePolicy,
) -> PathwayCoverageConfidenceStatus:
    if coverage_fraction >= policy.minimum_coverage_fraction:
        return PathwayCoverageConfidenceStatus.HIGH_CONFIDENCE
    return PathwayCoverageConfidenceStatus.LOW_CONFIDENCE


def _format_fraction(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")
