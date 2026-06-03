# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Exact PTM site-group modeling over localized peptide-to-protein mappings."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.ptm.contracts import PtmProteinSiteMapping, PtmSiteEntry


class PtmSiteGroupAmbiguityClass(StrEnum):
    """Stable exact-versus-group classes for PTM site grouping."""

    EXACT_SITE = "exact_site"
    AMBIGUOUS_SITE_GROUP = "ambiguous_site_group"


class PtmSiteGroupEntry(JsonModel):
    """One PTM site-group row that preserves exact or ambiguous localization scope."""

    model_config = ConfigDict(extra="forbid")

    site_group_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    candidate_sites: tuple[int, ...] = Field(default_factory=tuple)
    localized_site: int | None = Field(default=None, ge=1)
    ambiguity_class: PtmSiteGroupAmbiguityClass


class PtmSiteGroupEvidenceEntry(JsonModel):
    """One grouped PTM site-evidence record when localization remains unresolved."""

    model_config = ConfigDict(extra="forbid")

    group_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    modification_name: str = Field(..., min_length=1)
    candidate_positions: tuple[int, ...] = Field(default_factory=tuple)
    site_keys: tuple[str, ...] = Field(default_factory=tuple)
    spectrum_count: int = Field(..., ge=1)
    peptide_count: int = Field(..., ge=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    unresolved: bool
    note: str = Field(..., min_length=1)


def build_site_groups(
    localized_sites: tuple[PtmProteinSiteMapping, ...],
) -> tuple[PtmSiteGroupEntry, ...]:
    """Group PTM mappings so ambiguous peptide evidence is carried once per site group."""

    exact_groups: dict[tuple[str, str, int], list[PtmProteinSiteMapping]] = {}
    ambiguous_groups: dict[
        tuple[str, str, tuple[int, ...]], list[PtmProteinSiteMapping]
    ] = {}

    for mapping in localized_sites:
        candidate_sites = _candidate_sites(mapping)
        if len(candidate_sites) > 1 or mapping.ambiguous:
            ambiguous_groups.setdefault(
                (mapping.protein_ref, mapping.modification_name, candidate_sites),
                [],
            ).append(mapping)
            continue
        exact_groups.setdefault(
            (mapping.protein_ref, mapping.modification_name, mapping.protein_position),
            [],
        ).append(mapping)

    entries = [
        PtmSiteGroupEntry(
            site_group_id=f"{protein_id}:{modification_name}:{localized_site}",
            protein_id=protein_id,
            candidate_sites=(localized_site,),
            localized_site=localized_site,
            ambiguity_class=PtmSiteGroupAmbiguityClass.EXACT_SITE,
        )
        for protein_id, modification_name, localized_site in sorted(exact_groups)
    ]
    entries.extend(
        PtmSiteGroupEntry(
            site_group_id=(
                f"{protein_id}:{modification_name}:"
                f"{'|'.join(str(site) for site in candidate_sites)}"
            ),
            protein_id=protein_id,
            candidate_sites=candidate_sites,
            localized_site=None,
            ambiguity_class=PtmSiteGroupAmbiguityClass.AMBIGUOUS_SITE_GROUP,
        )
        for protein_id, modification_name, candidate_sites in sorted(ambiguous_groups)
    )
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.protein_id,
                entry.candidate_sites,
                entry.localized_site or 0,
                entry.ambiguity_class.value,
            ),
        )
    )


def build_ptm_site_group_evidence(
    site_entries: tuple[PtmSiteEntry, ...],
) -> tuple[PtmSiteGroupEvidenceEntry, ...]:
    """Group PTM site evidence by candidate-position set when localization stays unresolved."""

    grouped: dict[tuple[str, str, tuple[int, ...]], list[PtmSiteEntry]] = {}
    for entry in site_entries:
        candidate_positions = (
            entry.candidate_positions
            if entry.candidate_positions
            else (entry.position,)
        )
        grouped.setdefault(
            (entry.protein_ref, entry.modification_name, candidate_positions),
            [],
        ).append(entry)

    group_entries: list[PtmSiteGroupEvidenceEntry] = []
    for (protein_ref, modification_name, candidate_positions), bucket in sorted(
        grouped.items()
    ):
        unresolved = len(candidate_positions) > 1 or any(
            entry.ambiguous for entry in bucket
        )
        positions_token = "|".join(str(position) for position in candidate_positions)
        note = (
            "site evidence remains unresolved across multiple candidate positions"
            if unresolved
            else "site evidence resolves to one protein position"
        )
        group_entries.append(
            PtmSiteGroupEvidenceEntry(
                group_key=f"{protein_ref}:{modification_name}:{positions_token}",
                protein_ref=protein_ref,
                modification_name=modification_name,
                candidate_positions=candidate_positions,
                site_keys=tuple(sorted(entry.site_key for entry in bucket)),
                spectrum_count=sum(entry.spectrum_count for entry in bucket),
                peptide_count=sum(entry.peptide_count for entry in bucket),
                sample_ids=tuple(
                    sorted(
                        {
                            sample_id
                            for entry in bucket
                            for sample_id in entry.sample_ids
                        }
                    )
                ),
                unresolved=unresolved,
                note=note,
            )
        )
    return tuple(group_entries)


def render_ptm_site_group_tsv(entries: tuple[PtmSiteGroupEntry, ...]) -> str:
    """Render exact PTM site-group rows as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "site_group_id",
            "protein_id",
            "candidate_sites",
            "localized_site",
            "ambiguity_class",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.site_group_id,
                entry.protein_id,
                ";".join(str(site) for site in entry.candidate_sites),
                "" if entry.localized_site is None else entry.localized_site,
                entry.ambiguity_class.value,
            )
        )
    return buffer.getvalue()


def _candidate_sites(mapping: PtmProteinSiteMapping) -> tuple[int, ...]:
    candidate_sites = tuple(sorted(set(mapping.candidate_protein_positions)))
    if candidate_sites:
        return candidate_sites
    return (mapping.protein_position,)


__all__ = [
    "PtmSiteGroupAmbiguityClass",
    "PtmSiteGroupEvidenceEntry",
    "PtmSiteGroupEntry",
    "build_ptm_site_group_evidence",
    "build_site_groups",
    "render_ptm_site_group_tsv",
]
