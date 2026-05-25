# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM hotspot detection over protein-mapped site results."""

from __future__ import annotations

import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class PtmHotspotSiteResult(JsonModel):
    """One protein-mapped PTM site result eligible for hotspot clustering."""

    model_config = ConfigDict(extra="forbid")

    site_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    position: int = Field(..., ge=1)
    signed_effect: float


class PtmHotspotEntry(JsonModel):
    """One clustered PTM hotspot over nearby sites on one protein."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    cluster_start: int = Field(..., ge=1)
    cluster_end: int = Field(..., ge=1)
    site_ids: tuple[str, ...] = Field(default_factory=tuple)
    direction_consistency: float = Field(..., ge=0.0, le=1.0)
    hotspot_score: float = Field(..., ge=0.0)


def detect_ptm_hotspots(
    site_results: tuple[PtmHotspotSiteResult, ...],
    protein_length: int | dict[str, int],
    max_distance: int,
) -> tuple[PtmHotspotEntry, ...]:
    """Detect nearby multi-site PTM hotspots on one or more proteins."""

    if max_distance < 0:
        raise ValueError("hotspot detection requires max_distance >= 0")

    length_by_protein = _resolve_protein_lengths(site_results, protein_length)
    site_ids: set[str] = set()
    grouped: dict[str, list[PtmHotspotSiteResult]] = {}
    for result in site_results:
        if result.site_id in site_ids:
            raise ValueError("hotspot detection requires unique site_id rows")
        site_ids.add(result.site_id)
        protein_length_value = length_by_protein[result.protein_id]
        if result.position > protein_length_value:
            raise ValueError(
                "hotspot detection requires site positions to be within protein_length"
            )
        grouped.setdefault(result.protein_id, []).append(result)

    hotspots: list[PtmHotspotEntry] = []
    for protein_id, entries in sorted(grouped.items()):
        ordered = sorted(entries, key=lambda entry: (entry.position, entry.site_id))
        current_cluster: list[PtmHotspotSiteResult] = []
        previous_position: int | None = None
        for entry in ordered:
            if (
                previous_position is not None
                and entry.position - previous_position > max_distance
            ):
                hotspot = _build_hotspot_entry(
                    protein_id,
                    current_cluster,
                    protein_length=length_by_protein[protein_id],
                )
                if hotspot is not None:
                    hotspots.append(hotspot)
                current_cluster = []
            current_cluster.append(entry)
            previous_position = entry.position
        hotspot = _build_hotspot_entry(
            protein_id,
            current_cluster,
            protein_length=length_by_protein[protein_id],
        )
        if hotspot is not None:
            hotspots.append(hotspot)
    return tuple(hotspots)


def render_ptm_hotspots_tsv(entries: tuple[PtmHotspotEntry, ...]) -> str:
    """Render PTM hotspot calls as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_id",
            "cluster_start",
            "cluster_end",
            "site_ids",
            "direction_consistency",
            "hotspot_score",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.protein_id,
                entry.cluster_start,
                entry.cluster_end,
                ";".join(entry.site_ids),
                f"{entry.direction_consistency:.6f}",
                f"{entry.hotspot_score:.6f}",
            )
        )
    return buffer.getvalue()


def _resolve_protein_lengths(
    site_results: tuple[PtmHotspotSiteResult, ...],
    protein_length: int | dict[str, int],
) -> dict[str, int]:
    protein_ids = tuple(sorted({entry.protein_id for entry in site_results}))
    if isinstance(protein_length, int):
        if protein_length < 1:
            raise ValueError("hotspot detection requires protein_length >= 1")
        if len(protein_ids) > 1:
            raise ValueError(
                "hotspot detection requires per-protein lengths when multiple proteins are present"
            )
        return {protein_id: protein_length for protein_id in protein_ids}
    resolved: dict[str, int] = {}
    for protein_id in protein_ids:
        length_value = protein_length.get(protein_id)
        if length_value is None:
            raise ValueError(
                f"hotspot detection requires protein_length for protein {protein_id}"
            )
        if length_value < 1:
            raise ValueError("hotspot detection requires protein_length >= 1")
        resolved[protein_id] = length_value
    return resolved


def _build_hotspot_entry(
    protein_id: str,
    cluster: list[PtmHotspotSiteResult],
    *,
    protein_length: int,
) -> PtmHotspotEntry | None:
    if len(cluster) < 2:
        return None
    cluster_start = cluster[0].position
    cluster_end = cluster[-1].position
    span = max(cluster_end - cluster_start, 0)
    direction_consistency = _direction_consistency(tuple(entry.signed_effect for entry in cluster))
    mean_absolute_effect = sum(abs(entry.signed_effect) for entry in cluster) / len(cluster)
    density_factor = len(cluster) / (1.0 + span)
    compactness_factor = 1.0 - (span / float(max(protein_length, 1)))
    hotspot_score = round(
        mean_absolute_effect * direction_consistency * density_factor * compactness_factor,
        6,
    )
    return PtmHotspotEntry(
        protein_id=protein_id,
        cluster_start=cluster_start,
        cluster_end=cluster_end,
        site_ids=tuple(entry.site_id for entry in cluster),
        direction_consistency=round(direction_consistency, 6),
        hotspot_score=max(hotspot_score, 0.0),
    )


def _direction_consistency(signed_effects: tuple[float, ...]) -> float:
    positive = sum(1 for effect in signed_effects if effect > 0.0)
    negative = sum(1 for effect in signed_effects if effect < 0.0)
    informative = positive + negative
    if informative == 0:
        return 0.0
    return max(positive, negative) / float(informative)


__all__ = [
    "PtmHotspotEntry",
    "PtmHotspotSiteResult",
    "detect_ptm_hotspots",
    "render_ptm_hotspots_tsv",
]
