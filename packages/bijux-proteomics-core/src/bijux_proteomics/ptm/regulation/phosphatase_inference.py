# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Phosphatase inference from exact phosphosite annotations."""

from __future__ import annotations

import csv
import math
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class PtmPhosphataseSiteDirection(StrEnum):
    """Stable site-direction labels carried into phosphatase inference."""

    UPREGULATED = "upregulated"
    DOWNREGULATED = "downregulated"
    UNCHANGED = "unchanged"


class PtmPhosphataseSiteResult(JsonModel):
    """One phosphosite result eligible for exact phosphatase evidence."""

    model_config = ConfigDict(extra="forbid")

    site_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    signed_effect: float


class PtmPhosphataseSubstrateAnnotation(JsonModel):
    """One phosphatase-substrate annotation row.

    Exact site annotations carry ``site_id``. Protein-level-only annotations may carry
    ``substrate_protein_id`` without a site and are intentionally excluded from exact-site
    inference.
    """

    model_config = ConfigDict(extra="forbid")

    phosphatase: str = Field(..., min_length=1)
    site_id: str | None = Field(default=None, min_length=1)
    substrate_protein_id: str | None = Field(default=None, min_length=1)

    def model_post_init(self, __context: object) -> None:
        if self.site_id is None and self.substrate_protein_id is None:
            raise ValueError(
                "phosphatase substrate annotations require site_id or substrate_protein_id"
            )


class PtmPhosphataseInferenceEntry(JsonModel):
    """One inferred phosphatase from exact observed site annotations."""

    model_config = ConfigDict(extra="forbid")

    phosphatase: str = Field(..., min_length=1)
    supporting_sites: tuple[str, ...] = Field(default_factory=tuple)
    site_directions: tuple[PtmPhosphataseSiteDirection, ...] = Field(default_factory=tuple)
    p_value: float = Field(..., ge=0.0, le=1.0)
    q_value: float = Field(..., ge=0.0, le=1.0)
    annotation_coverage: float = Field(..., ge=0.0, le=1.0)


def infer_phosphatases(
    phosphosite_results: tuple[PtmPhosphataseSiteResult, ...],
    phosphatase_substrate_table: tuple[PtmPhosphataseSubstrateAnnotation, ...],
) -> tuple[PtmPhosphataseInferenceEntry, ...]:
    """Infer phosphatases from exact substrate-site evidence only."""

    site_lookup: dict[str, PtmPhosphataseSiteResult] = {}
    for entry in phosphosite_results:
        if entry.site_id in site_lookup:
            raise ValueError(
                "phosphatase inference requires unique site_id phosphosite results"
            )
        site_lookup[entry.site_id] = entry

    exact_annotation_sites_by_phosphatase: dict[str, set[str]] = {}
    observed_exact_sites_by_phosphatase: dict[str, set[str]] = {}
    for annotation_entry in phosphatase_substrate_table:
        if annotation_entry.site_id is None:
            continue
        exact_annotation_sites_by_phosphatase.setdefault(
            annotation_entry.phosphatase, set()
        ).add(
            annotation_entry.site_id
        )
        if annotation_entry.site_id not in site_lookup:
            continue
        if (
            annotation_entry.substrate_protein_id is not None
            and annotation_entry.substrate_protein_id
            != site_lookup[annotation_entry.site_id].protein_id
        ):
            continue
        observed_exact_sites_by_phosphatase.setdefault(
            annotation_entry.phosphatase, set()
        ).add(
            annotation_entry.site_id
        )

    entries: list[PtmPhosphataseInferenceEntry] = []
    raw_p_values: list[float] = []
    ordered_phosphatases = tuple(sorted(observed_exact_sites_by_phosphatase))
    for phosphatase in ordered_phosphatases:
        supporting_sites = tuple(sorted(observed_exact_sites_by_phosphatase[phosphatase]))
        directions = tuple(
            _site_direction(site_lookup[site_id].signed_effect) for site_id in supporting_sites
        )
        p_value = _directional_consistency_p_value(directions)
        exact_annotation_count = len(exact_annotation_sites_by_phosphatase[phosphatase])
        annotation_coverage = 0.0
        if exact_annotation_count > 0:
            annotation_coverage = len(supporting_sites) / exact_annotation_count
        raw_p_values.append(p_value)
        entries.append(
            PtmPhosphataseInferenceEntry(
                phosphatase=phosphatase,
                supporting_sites=supporting_sites,
                site_directions=directions,
                p_value=round(p_value, 12),
                q_value=1.0,
                annotation_coverage=round(annotation_coverage, 6),
            )
        )

    q_values = _benjamini_hochberg(tuple(raw_p_values))
    adjusted_entries = tuple(
        entry.model_copy(update={"q_value": round(q_values[index], 12)})
        for index, entry in enumerate(entries)
    )
    return tuple(
        sorted(
            adjusted_entries,
            key=lambda entry: (
                entry.q_value,
                entry.p_value,
                -len(entry.supporting_sites),
                entry.phosphatase,
            ),
        )
    )


def render_ptm_phosphatase_inference_tsv(
    entries: tuple[PtmPhosphataseInferenceEntry, ...],
) -> str:
    """Render phosphatase inference rows as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "phosphatase",
            "supporting_sites",
            "site_directions",
            "p_value",
            "q_value",
            "annotation_coverage",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.phosphatase,
                ";".join(entry.supporting_sites),
                ";".join(direction.value for direction in entry.site_directions),
                f"{entry.p_value:.12g}",
                f"{entry.q_value:.12g}",
                f"{entry.annotation_coverage:.6f}",
            )
        )
    return buffer.getvalue()


def _site_direction(signed_effect: float) -> PtmPhosphataseSiteDirection:
    if signed_effect > 0.0:
        return PtmPhosphataseSiteDirection.UPREGULATED
    if signed_effect < 0.0:
        return PtmPhosphataseSiteDirection.DOWNREGULATED
    return PtmPhosphataseSiteDirection.UNCHANGED


def _directional_consistency_p_value(
    site_directions: tuple[PtmPhosphataseSiteDirection, ...],
) -> float:
    informative = tuple(
        direction
        for direction in site_directions
        if direction is not PtmPhosphataseSiteDirection.UNCHANGED
    )
    trial_count = len(informative)
    if trial_count <= 1:
        return 1.0
    upregulated_count = sum(
        1 for direction in informative if direction is PtmPhosphataseSiteDirection.UPREGULATED
    )
    downregulated_count = trial_count - upregulated_count
    dominant_count = max(upregulated_count, downregulated_count)
    tail_probability = sum(
        math.comb(trial_count, support_count) / (2**trial_count)
        for support_count in range(dominant_count, trial_count + 1)
    )
    return float(min(1.0, 2.0 * tail_probability))


def _benjamini_hochberg(p_values: tuple[float, ...]) -> tuple[float, ...]:
    if not p_values:
        return ()
    adjusted: list[float] = [1.0] * len(p_values)
    running = 1.0
    total = len(p_values)
    ordered = sorted(enumerate(p_values), key=lambda item: item[1])
    for reverse_rank, (index, p_value) in enumerate(reversed(ordered), start=1):
        rank = total - reverse_rank + 1
        candidate = p_value * total / rank
        running = min(running, candidate)
        adjusted[index] = min(max(running, 0.0), 1.0)
    return tuple(adjusted)


__all__ = [
    "PtmPhosphataseInferenceEntry",
    "PtmPhosphataseSiteDirection",
    "PtmPhosphataseSiteResult",
    "PtmPhosphataseSubstrateAnnotation",
    "infer_phosphatases",
    "render_ptm_phosphatase_inference_tsv",
]
