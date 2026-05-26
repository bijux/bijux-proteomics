# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Complex membership resolution over curated complex packs."""

from __future__ import annotations

import csv
from collections import defaultdict
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.annotation_packs import AnnotationPack
from bijux_proteomics.interpretation.complex_enrichment import (
    ComplexMemberKind,
    ComplexMembershipRecord,
)
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.identity.proteins import (
    ProteinIdentityResolutionStatus,
    resolve_protein_ids,
)


class ComplexMembershipConfidence(StrEnum):
    """Confidence classification derived from observed complex coverage."""

    HIGH_CONFIDENCE = "high_confidence"
    LOW_CONFIDENCE = "low_confidence"


class ComplexCoveragePolicy(JsonModel):
    """Coverage policy for complex membership confidence."""

    model_config = ConfigDict(extra="forbid")

    minimum_observed_member_count: int = Field(default=2, ge=1)


class ComplexMembershipResolutionEntry(JsonModel):
    """One complex membership resolution row for one curated complex."""

    model_config = ConfigDict(extra="forbid")

    complex_id: str = Field(..., min_length=1)
    observed_members: tuple[str, ...] = Field(default_factory=tuple)
    missing_members: tuple[str, ...] = Field(default_factory=tuple)
    member_coverage: float = Field(..., ge=0.0, le=1.0)
    complex_confidence: ComplexMembershipConfidence


class ComplexMembershipResolutionSummary(JsonModel):
    """Stable summary over complex membership resolution."""

    model_config = ConfigDict(extra="forbid")

    complex_count: int = Field(..., ge=0)
    high_confidence_complex_count: int = Field(..., ge=0)
    low_confidence_complex_count: int = Field(..., ge=0)
    unresolved_input_count: int = Field(..., ge=0)


class ComplexMembershipResolutionReport(JsonModel):
    """Owned report over resolved complex coverage and confidence."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ComplexMembershipResolutionEntry, ...] = Field(default_factory=tuple)
    unresolved_inputs: tuple[str, ...] = Field(default_factory=tuple)
    summary: ComplexMembershipResolutionSummary
    note: str = Field(..., min_length=1)


def resolve_complex_members(
    protein_ids: tuple[str, ...],
    complex_pack: AnnotationPack | tuple[ComplexMembershipRecord, ...],
    *,
    policy: ComplexCoveragePolicy | None = None,
) -> ComplexMembershipResolutionReport:
    """Resolve input proteins onto curated complex membership rows.

    Inputs:
    ``protein_ids`` are the identifiers to ground, ``complex_pack`` supplies
    curated complex membership data, and ``policy`` optionally overrides the
    owned confidence thresholds.

    Outputs:
    Returns one ``ComplexMembershipResolutionReport`` with per-complex observed
    members, missing members, unresolved inputs, and confidence summaries.

    Failure Modes:
    This function does not raise governed public exceptions under normal typed
    input use.

    Scientific Caveats:
    Coverage and confidence reflect only the supplied curated complex pack and
    alias resolution; they do not prove complex assembly in the measured sample.
    """

    active_policy = policy or ComplexCoveragePolicy()
    complex_records, annotation_pack = _normalize_complex_pack(complex_pack)
    complex_groups = _group_complex_records(complex_records)
    resolved_protein_refs, resolved_gene_symbols, unresolved_inputs = _resolved_inputs(
        protein_ids=protein_ids,
        annotation_pack=annotation_pack,
    )

    entries: list[ComplexMembershipResolutionEntry] = []
    for complex_id in sorted(complex_groups):
        records = complex_groups[complex_id]
        observed_members: list[str] = []
        missing_members: list[str] = []
        for record in records:
            member_label = _member_label(record)
            if _member_matches(
                record=record,
                resolved_protein_refs=resolved_protein_refs,
                resolved_gene_symbols=resolved_gene_symbols,
            ):
                observed_members.append(member_label)
            else:
                missing_members.append(member_label)

        total_member_count = len(records)
        observed_member_count = len(observed_members)
        member_coverage = (
            observed_member_count / total_member_count if total_member_count > 0 else 0.0
        )
        entries.append(
            ComplexMembershipResolutionEntry(
                complex_id=complex_id,
                observed_members=tuple(sorted(observed_members)),
                missing_members=tuple(sorted(missing_members)),
                member_coverage=round(member_coverage, 4),
                complex_confidence=_confidence_status(
                    observed_member_count=observed_member_count,
                    policy=active_policy,
                ),
            )
        )

    return ComplexMembershipResolutionReport(
        entries=tuple(entries),
        unresolved_inputs=tuple(sorted(unresolved_inputs)),
        summary=ComplexMembershipResolutionSummary(
            complex_count=len(entries),
            high_confidence_complex_count=sum(
                1
                for entry in entries
                if entry.complex_confidence is ComplexMembershipConfidence.HIGH_CONFIDENCE
            ),
            low_confidence_complex_count=sum(
                1
                for entry in entries
                if entry.complex_confidence is ComplexMembershipConfidence.LOW_CONFIDENCE
            ),
            unresolved_input_count=len(unresolved_inputs),
        ),
        note=(
            "complex membership resolution preserves observed and missing members per "
            "complex, keeps unresolved inputs explicit, and downgrades sparse "
            "complexes to low confidence instead of treating partial complexes as "
            "fully supported assemblies"
        ),
    )


def render_complex_membership_resolution_tsv(
    entries: tuple[ComplexMembershipResolutionEntry, ...],
) -> str:
    """Render complex membership resolution rows as TSV.

    Inputs:
    ``entries`` must be the complex membership rows to serialize.

    Outputs:
    Returns one TSV string with the governed complex membership columns.

    Failure Modes:
    This function does not raise governed public exceptions under normal typed
    input use.

    Scientific Caveats:
    The TSV preserves computed complex coverage only; it does not create new
    evidence beyond the supplied resolution report.
    """

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "complex_id",
            "observed_members",
            "missing_members",
            "member_coverage",
            "complex_confidence",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.complex_id,
                ";".join(entry.observed_members),
                ";".join(entry.missing_members),
                _format_fraction(entry.member_coverage),
                entry.complex_confidence.value,
            )
        )
    return handle.getvalue()


def _normalize_complex_pack(
    complex_pack: AnnotationPack | tuple[ComplexMembershipRecord, ...],
) -> tuple[tuple[ComplexMembershipRecord, ...], AnnotationPack | None]:
    if isinstance(complex_pack, AnnotationPack):
        return complex_pack.complexes, complex_pack
    return complex_pack, None


def _group_complex_records(
    complex_records: tuple[ComplexMembershipRecord, ...],
) -> dict[str, tuple[ComplexMembershipRecord, ...]]:
    grouped: dict[str, list[ComplexMembershipRecord]] = defaultdict(list)
    for record in complex_records:
        grouped[record.complex_id].append(record)
    return {
        complex_id: tuple(
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
        for complex_id, records in grouped.items()
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
    record: ComplexMembershipRecord,
    resolved_protein_refs: set[str],
    resolved_gene_symbols: set[str],
) -> bool:
    if record.member_kind is ComplexMemberKind.PROTEIN:
        return canonicalize_protein_reference(record.member_id) in resolved_protein_refs
    return record.member_id in resolved_gene_symbols


def _member_label(record: ComplexMembershipRecord) -> str:
    return f"{record.member_kind.value}:{record.member_id}"


def _confidence_status(
    *,
    observed_member_count: int,
    policy: ComplexCoveragePolicy,
) -> ComplexMembershipConfidence:
    if observed_member_count >= policy.minimum_observed_member_count:
        return ComplexMembershipConfidence.HIGH_CONFIDENCE
    return ComplexMembershipConfidence.LOW_CONFIDENCE


def _format_fraction(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")
