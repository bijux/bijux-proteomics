# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Generic protein-set enrichment surfaces over explicit protein foregrounds."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
import json
import math

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinReferenceEntry,
)
from bijux_proteomics.interpretation.protein_set_scoring import (
    ProteinSetImportReport,
    ProteinSetRecord,
)
from bijux_proteomics_foundation import JsonModel


class ProteinSetEnrichmentMissingBackgroundPolicy(StrEnum):
    """Policy when no explicit background protein table is supplied."""

    REJECT = "reject"
    MEMBERSHIP_UNIVERSE = "membership_universe"


class ProteinSetEnrichmentBackgroundSource(StrEnum):
    """Actual background source used during one enrichment run."""

    EXPLICIT_INPUT = "explicit_input"
    MEMBERSHIP_UNIVERSE = "membership_universe"


class ProteinSetUniverseGapEntry(JsonModel):
    """One protein that could not be placed inside the enrichment universe."""

    model_config = ConfigDict(extra="forbid")

    set_role: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class ProteinSetEnrichmentEntry(JsonModel):
    """One evaluated protein set."""

    model_config = ConfigDict(extra="forbid")

    set_id: str = Field(..., min_length=1)
    set_name: str | None = None
    set_category: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    foreground_overlap_count: int = Field(..., ge=0)
    background_member_count: int = Field(..., ge=0)
    foreground_size: int = Field(..., ge=0)
    background_size: int = Field(..., ge=0)
    expected_overlap_count: float = Field(..., ge=0.0)
    enrichment_ratio: float | None = Field(default=None, ge=0.0)
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    supporting_protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class ProteinSetEnrichmentSummary(JsonModel):
    """Stable summary over one protein-set enrichment run."""

    model_config = ConfigDict(extra="forbid")

    foreground_size: int = Field(..., ge=0)
    background_size: int = Field(..., ge=0)
    background_source: ProteinSetEnrichmentBackgroundSource
    evaluated_set_count: int = Field(..., ge=0)
    enriched_set_count: int = Field(..., ge=0)
    category_counts: dict[str, int] = Field(default_factory=dict)
    foreground_universe_gap_count: int = Field(..., ge=0)
    background_universe_gap_count: int = Field(..., ge=0)


class ProteinSetEnrichmentPolicy(JsonModel):
    """Selection and background policy for protein-set enrichment."""

    model_config = ConfigDict(extra="forbid")

    missing_background_policy: ProteinSetEnrichmentMissingBackgroundPolicy = (
        ProteinSetEnrichmentMissingBackgroundPolicy.REJECT
    )
    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_enrichment_ratio: float = Field(default=1.0, ge=0.0)


class ProteinSetEnrichmentReport(JsonModel):
    """Owned generic enrichment report over custom protein-set memberships."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ProteinSetEnrichmentEntry, ...] = Field(default_factory=tuple)
    universe_gap_entries: tuple[ProteinSetUniverseGapEntry, ...] = Field(
        default_factory=tuple
    )
    summary: ProteinSetEnrichmentSummary
    note: str = Field(..., min_length=1)


def build_protein_set_enrichment_report(
    foreground_entries: tuple[ProteinReferenceEntry, ...],
    protein_set_records: tuple[ProteinSetRecord, ...],
    *,
    background_entries: tuple[ProteinReferenceEntry, ...] | None = None,
    policy: ProteinSetEnrichmentPolicy | None = None,
) -> ProteinSetEnrichmentReport:
    """Run generic hypergeometric enrichment over protein-set memberships."""

    active_policy = policy or ProteinSetEnrichmentPolicy()
    foreground = {entry.protein_ref for entry in foreground_entries}
    if not foreground:
        raise ValueError("foreground protein set must contain at least one protein")

    if background_entries is None:
        if (
            active_policy.missing_background_policy
            is ProteinSetEnrichmentMissingBackgroundPolicy.REJECT
        ):
            raise ValueError(
                "explicit background protein set is required unless missing_background_policy is membership_universe"
            )
        background = {record.protein_ref for record in protein_set_records}
        background_source = ProteinSetEnrichmentBackgroundSource.MEMBERSHIP_UNIVERSE
    else:
        background = {entry.protein_ref for entry in background_entries}
        background_source = ProteinSetEnrichmentBackgroundSource.EXPLICIT_INPUT

    if not background:
        raise ValueError("background protein set must contain at least one protein")

    if background_source is ProteinSetEnrichmentBackgroundSource.EXPLICIT_INPUT:
        if not foreground <= background:
            missing = sorted(foreground - background)
            raise ValueError(
                "foreground proteins must be present in the background set: "
                + ", ".join(missing)
            )
    else:
        background |= foreground

    grouped_sets: dict[str, list[ProteinSetRecord]] = {}
    for record in protein_set_records:
        grouped_sets.setdefault(record.set_id, []).append(record)

    universe_gap_entries = _build_universe_gap_entries(
        foreground=foreground,
        background=background,
        membership_universe={record.protein_ref for record in protein_set_records},
    )

    entries: list[ProteinSetEnrichmentEntry] = []
    for set_id in sorted(grouped_sets):
        records = grouped_sets[set_id]
        first = records[0]
        members = {record.protein_ref for record in records} & background
        foreground_members = members & foreground
        if not foreground_members:
            continue
        foreground_size = len(foreground)
        background_size = len(background)
        expected_overlap_count = foreground_size * len(members) / background_size
        enrichment_ratio = (
            len(foreground_members) / expected_overlap_count
            if expected_overlap_count > 0.0
            else None
        )
        entries.append(
            ProteinSetEnrichmentEntry(
                set_id=set_id,
                set_name=first.set_name,
                set_category=first.set_category,
                source_name=first.source_name,
                source_accession=first.source_accession,
                foreground_overlap_count=len(foreground_members),
                background_member_count=len(members),
                foreground_size=foreground_size,
                background_size=background_size,
                expected_overlap_count=round(expected_overlap_count, 6),
                enrichment_ratio=(
                    None if enrichment_ratio is None else round(enrichment_ratio, 6)
                ),
                p_value=_hypergeometric_sf(
                    overlap_count=len(foreground_members),
                    term_background_count=len(members),
                    foreground_size=foreground_size,
                    background_size=background_size,
                ),
                supporting_protein_refs=tuple(sorted(foreground_members)),
            )
        )

    adjusted_p_values = _benjamini_hochberg(tuple(entry.p_value for entry in entries))
    corrected_entries = tuple(
        ProteinSetEnrichmentEntry.model_validate(
            entry.model_copy(
                update={
                    "adjusted_p_value": round(adjusted_p_value, 6),
                }
            )
        )
        for entry, adjusted_p_value in zip(entries, adjusted_p_values, strict=False)
        if adjusted_p_value <= active_policy.max_adjusted_p_value
        and (
            entry.enrichment_ratio is None
            or entry.enrichment_ratio >= active_policy.min_enrichment_ratio
        )
    )

    category_counts: dict[str, int] = {}
    for entry in corrected_entries:
        category = entry.set_category or "uncategorized"
        category_counts[category] = category_counts.get(category, 0) + 1

    return ProteinSetEnrichmentReport(
        entries=tuple(
            sorted(
                corrected_entries,
                key=lambda entry: (
                    entry.adjusted_p_value
                    if entry.adjusted_p_value is not None
                    else 1.0,
                    entry.p_value,
                    entry.set_id,
                ),
            )
        ),
        universe_gap_entries=tuple(universe_gap_entries),
        summary=ProteinSetEnrichmentSummary(
            foreground_size=len(foreground),
            background_size=len(background),
            background_source=background_source,
            evaluated_set_count=len(entries),
            enriched_set_count=len(corrected_entries),
            category_counts=dict(sorted(category_counts.items())),
            foreground_universe_gap_count=sum(
                1 for entry in universe_gap_entries if entry.set_role == "foreground"
            ),
            background_universe_gap_count=sum(
                1 for entry in universe_gap_entries if entry.set_role == "background"
            ),
        ),
        note=(
            "generic protein-set enrichment preserves explicit foreground and background policy, "
            "supports compartment and custom set categories, and keeps proteins outside the membership universe reviewable"
        ),
    )


def render_protein_set_enrichment_summary_tsv(
    report: ProteinSetEnrichmentReport,
) -> str:
    """Render one compact protein-set enrichment summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "foreground_size",
            "background_size",
            "background_source",
            "evaluated_set_count",
            "enriched_set_count",
            "foreground_universe_gap_count",
            "background_universe_gap_count",
            "category_counts",
        )
    )
    writer.writerow(
        (
            report.summary.foreground_size,
            report.summary.background_size,
            report.summary.background_source.value,
            report.summary.evaluated_set_count,
            report.summary.enriched_set_count,
            report.summary.foreground_universe_gap_count,
            report.summary.background_universe_gap_count,
            _category_counts_tsv(report.summary.category_counts),
        )
    )
    return buffer.getvalue()


def render_protein_set_enrichment_tsv(report: ProteinSetEnrichmentReport) -> str:
    """Render enriched protein-set rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "set_id",
            "set_name",
            "set_category",
            "source_name",
            "source_accession",
            "foreground_overlap_count",
            "background_member_count",
            "foreground_size",
            "background_size",
            "expected_overlap_count",
            "enrichment_ratio",
            "p_value",
            "adjusted_p_value",
            "supporting_protein_refs",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.set_id,
                entry.set_name or "",
                entry.set_category or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.foreground_overlap_count,
                entry.background_member_count,
                entry.foreground_size,
                entry.background_size,
                f"{entry.expected_overlap_count:.6f}",
                ""
                if entry.enrichment_ratio is None
                else f"{entry.enrichment_ratio:.6f}",
                f"{entry.p_value:.6f}",
                ""
                if entry.adjusted_p_value is None
                else f"{entry.adjusted_p_value:.6f}",
                ";".join(entry.supporting_protein_refs),
            )
        )
    return buffer.getvalue()


def render_protein_set_universe_gap_tsv(report: ProteinSetEnrichmentReport) -> str:
    """Render proteins outside the membership universe as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("set_role", "protein_ref", "reason"))
    for entry in report.universe_gap_entries:
        writer.writerow((entry.set_role, entry.protein_ref, entry.reason))
    return buffer.getvalue()


def render_rejected_protein_set_membership_tsv(report: ProteinSetImportReport) -> str:
    """Render rejected protein-set membership rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "values", "reason"))
    for row in report.rejected_rows:
        writer.writerow((row.row_number, _metadata_json(row.values), row.reason))
    return buffer.getvalue()


def _build_universe_gap_entries(
    *,
    foreground: set[str],
    background: set[str],
    membership_universe: set[str],
) -> tuple[ProteinSetUniverseGapEntry, ...]:
    entries: list[ProteinSetUniverseGapEntry] = []
    for protein_ref in sorted(foreground - membership_universe):
        entries.append(
            ProteinSetUniverseGapEntry(
                set_role="foreground",
                protein_ref=protein_ref,
                reason="protein was not present in the membership universe",
            )
        )
    for protein_ref in sorted((background - foreground) - membership_universe):
        entries.append(
            ProteinSetUniverseGapEntry(
                set_role="background",
                protein_ref=protein_ref,
                reason="protein was not present in the membership universe",
            )
        )
    return tuple(entries)


def _hypergeometric_sf(
    *,
    overlap_count: int,
    term_background_count: int,
    foreground_size: int,
    background_size: int,
) -> float:
    maximum_overlap = min(term_background_count, foreground_size)
    denominator = math.comb(background_size, foreground_size)
    p_value = 0.0
    for overlap in range(overlap_count, maximum_overlap + 1):
        p_value += (
            math.comb(term_background_count, overlap)
            * math.comb(
                background_size - term_background_count,
                foreground_size - overlap,
            )
            / denominator
        )
    return min(max(p_value, 0.0), 1.0)


def _benjamini_hochberg(p_values: tuple[float, ...]) -> tuple[float, ...]:
    if not p_values:
        return ()
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [0.0] * len(p_values)
    running_min = 1.0
    total = len(p_values)
    for rank, (index, p_value) in enumerate(reversed(indexed), start=1):
        adjusted_value = min(1.0, p_value * total / (total - rank + 1))
        running_min = min(running_min, adjusted_value)
        adjusted[index] = running_min
    return tuple(adjusted)


def _category_counts_tsv(category_counts: dict[str, int]) -> str:
    return ";".join(
        f"{category}:{count}" for category, count in sorted(category_counts.items())
    )


def _metadata_json(values: dict[str, str]) -> str:
    return json.dumps(
        values,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


__all__ = (
    "ProteinSetEnrichmentBackgroundSource",
    "ProteinSetEnrichmentEntry",
    "ProteinSetEnrichmentMissingBackgroundPolicy",
    "ProteinSetEnrichmentPolicy",
    "ProteinSetEnrichmentReport",
    "ProteinSetEnrichmentSummary",
    "ProteinSetUniverseGapEntry",
    "build_protein_set_enrichment_report",
    "render_protein_set_enrichment_summary_tsv",
    "render_protein_set_enrichment_tsv",
    "render_protein_set_universe_gap_tsv",
    "render_rejected_protein_set_membership_tsv",
)
