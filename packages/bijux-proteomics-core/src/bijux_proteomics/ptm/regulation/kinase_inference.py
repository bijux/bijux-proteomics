# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Kinase inference from motif support plus exact substrate evidence."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class PtmKinaseConfidenceTier(StrEnum):
    """Stable confidence tiers for kinase inference evidence combinations."""

    MOTIF_PLUS_SUBSTRATE = "motif_plus_substrate"
    SUBSTRATE_ONLY = "substrate_only"
    MOTIF_ONLY = "motif_only"


class PtmKinaseSiteResult(JsonModel):
    """One phosphosite result eligible for kinase inference."""

    model_config = ConfigDict(extra="forbid")

    site_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    signed_effect: float


class PtmKinaseMotifMatch(JsonModel):
    """One kinase motif match against one exact phosphosite result."""

    model_config = ConfigDict(extra="forbid")

    kinase: str = Field(..., min_length=1)
    site_id: str = Field(..., min_length=1)
    motif_score: float = Field(..., ge=0.0, le=1.0)


class PtmKinaseSubstrateMatch(JsonModel):
    """One exact kinase-substrate annotation for one phosphosite result."""

    model_config = ConfigDict(extra="forbid")

    kinase: str = Field(..., min_length=1)
    site_id: str = Field(..., min_length=1)


class PtmKinaseInferenceEntry(JsonModel):
    """One inferred kinase with explicit motif and substrate support counts."""

    model_config = ConfigDict(extra="forbid")

    kinase: str = Field(..., min_length=1)
    motif_support_count: int = Field(..., ge=0)
    known_substrate_support_count: int = Field(..., ge=0)
    combined_score: float = Field(..., ge=0.0)
    supporting_sites: tuple[str, ...] = Field(default_factory=tuple)
    confidence_tier: PtmKinaseConfidenceTier


def infer_kinases(
    phosphosite_results: tuple[PtmKinaseSiteResult, ...],
    motif_table: tuple[PtmKinaseMotifMatch, ...],
    kinase_substrate_table: tuple[PtmKinaseSubstrateMatch, ...],
) -> tuple[PtmKinaseInferenceEntry, ...]:
    """Infer kinases from motif evidence plus exact known substrate support."""

    site_lookup: dict[str, PtmKinaseSiteResult] = {}
    for entry in phosphosite_results:
        if entry.site_id in site_lookup:
            raise ValueError(
                "kinase inference requires unique site_id phosphosite results"
            )
        site_lookup[entry.site_id] = entry

    motif_by_kinase_site: dict[tuple[str, str], float] = {}
    for motif_entry in motif_table:
        if motif_entry.site_id not in site_lookup:
            continue
        key = (motif_entry.kinase, motif_entry.site_id)
        motif_by_kinase_site[key] = max(
            motif_entry.motif_score,
            motif_by_kinase_site.get(key, 0.0),
        )

    substrate_by_kinase: dict[str, set[str]] = {}
    for substrate_entry in kinase_substrate_table:
        if substrate_entry.site_id not in site_lookup:
            continue
        substrate_by_kinase.setdefault(substrate_entry.kinase, set()).add(
            substrate_entry.site_id
        )

    motif_by_kinase: dict[str, dict[str, float]] = {}
    for (kinase, site_id), motif_score in motif_by_kinase_site.items():
        motif_by_kinase.setdefault(kinase, {})[site_id] = motif_score

    all_kinases = tuple(sorted(set(motif_by_kinase) | set(substrate_by_kinase)))
    entries: list[PtmKinaseInferenceEntry] = []
    for kinase in all_kinases:
        motif_sites = motif_by_kinase.get(kinase, {})
        substrate_sites = substrate_by_kinase.get(kinase, set())
        supporting_sites = tuple(sorted(set(motif_sites) | substrate_sites))
        if not supporting_sites:
            continue
        overlap_count = sum(
            1
            for site_id in supporting_sites
            if site_id in motif_sites and site_id in substrate_sites
        )
        motif_component = sum(
            motif_score * _site_effect_weight(site_lookup[site_id])
            for site_id, motif_score in motif_sites.items()
        )
        substrate_component = sum(
            1.5 * _site_effect_weight(site_lookup[site_id])
            for site_id in substrate_sites
        )
        combined_score = round(
            motif_component + substrate_component + (0.5 * overlap_count),
            6,
        )
        entries.append(
            PtmKinaseInferenceEntry(
                kinase=kinase,
                motif_support_count=len(motif_sites),
                known_substrate_support_count=len(substrate_sites),
                combined_score=combined_score,
                supporting_sites=supporting_sites,
                confidence_tier=_confidence_tier(
                    motif_support_count=len(motif_sites),
                    known_substrate_support_count=len(substrate_sites),
                ),
            )
        )
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                -entry.combined_score,
                -entry.known_substrate_support_count,
                -entry.motif_support_count,
                entry.kinase,
            ),
        )
    )


def render_ptm_kinase_inference_tsv(
    entries: tuple[PtmKinaseInferenceEntry, ...],
) -> str:
    """Render kinase inference entries as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "kinase",
            "motif_support_count",
            "known_substrate_support_count",
            "combined_score",
            "supporting_sites",
            "confidence_tier",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.kinase,
                entry.motif_support_count,
                entry.known_substrate_support_count,
                f"{entry.combined_score:.6f}",
                ";".join(entry.supporting_sites),
                entry.confidence_tier.value,
            )
        )
    return buffer.getvalue()


def _site_effect_weight(entry: PtmKinaseSiteResult) -> float:
    return 1.0 + min(abs(entry.signed_effect), 4.0) / 4.0


def _confidence_tier(
    *,
    motif_support_count: int,
    known_substrate_support_count: int,
) -> PtmKinaseConfidenceTier:
    if motif_support_count > 0 and known_substrate_support_count > 0:
        return PtmKinaseConfidenceTier.MOTIF_PLUS_SUBSTRATE
    if known_substrate_support_count > 0:
        return PtmKinaseConfidenceTier.SUBSTRATE_ONLY
    return PtmKinaseConfidenceTier.MOTIF_ONLY


__all__ = [
    "PtmKinaseConfidenceTier",
    "PtmKinaseInferenceEntry",
    "PtmKinaseMotifMatch",
    "PtmKinaseSiteResult",
    "PtmKinaseSubstrateMatch",
    "infer_kinases",
    "render_ptm_kinase_inference_tsv",
]
