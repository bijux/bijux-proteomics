# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Acetylation-specific site analysis over observed PTM rows."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class PtmAcetylationType(StrEnum):
    """Stable acetylation placement classes."""

    N_TERMINAL_ACETYLATION = "n_terminal_acetylation"
    LYSINE_ACETYLATION = "lysine_acetylation"
    NONCANONICAL_RESIDUE_ACETYLATION = "noncanonical_residue_acetylation"


class PtmAcetylSiteCandidate(JsonModel):
    """One acetyl site eligible for site-type and context analysis."""

    model_config = ConfigDict(extra="forbid")

    site_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    raw_site_log2fc: float
    protein_log2fc: float | None = None


class PtmAcetylProteinContext(JsonModel):
    """One protein-region context row used for acetylation site annotation."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    start: int = Field(..., ge=1)
    end: int = Field(..., ge=1)
    domain_context: str = Field(..., min_length=1)


class PtmAcetylSiteAnalysisEntry(JsonModel):
    """One analyzed acetyl site with placement and corrected effect semantics."""

    model_config = ConfigDict(extra="forbid")

    site_id: str = Field(..., min_length=1)
    acetylation_type: PtmAcetylationType
    lysine_position: int | None = Field(default=None, ge=1)
    n_terminal: bool
    domain_context: str
    abundance_corrected_effect: float | None = None


def analyze_acetylation_sites(
    acetyl_site_table: tuple[PtmAcetylSiteCandidate, ...],
    protein_context: tuple[PtmAcetylProteinContext, ...],
) -> tuple[PtmAcetylSiteAnalysisEntry, ...]:
    """Analyze acetylation sites by placement class, region context, and protein correction."""

    site_ids: set[str] = set()
    context_by_protein: dict[str, list[PtmAcetylProteinContext]] = {}
    for entry in protein_context:
        context_by_protein.setdefault(entry.protein_id, []).append(entry)

    analyzed: list[PtmAcetylSiteAnalysisEntry] = []
    for site_candidate in acetyl_site_table:
        if site_candidate.site_id in site_ids:
            raise ValueError("acetylation analysis requires unique site_id rows")
        site_ids.add(site_candidate.site_id)
        acetylation_type = _acetylation_type(site_candidate)
        matched_context = tuple(
            sorted(
                {
                    region.domain_context
                    for region in context_by_protein.get(site_candidate.protein_id, [])
                    if region.start <= site_candidate.position <= region.end
                }
            )
        )
        analyzed.append(
            PtmAcetylSiteAnalysisEntry(
                site_id=site_candidate.site_id,
                acetylation_type=acetylation_type,
                lysine_position=(
                    site_candidate.position
                    if acetylation_type is PtmAcetylationType.LYSINE_ACETYLATION
                    else None
                ),
                n_terminal=site_candidate.position == 1,
                domain_context=";".join(matched_context),
                abundance_corrected_effect=(
                    None
                    if site_candidate.protein_log2fc is None
                    else round(
                        site_candidate.raw_site_log2fc
                        - site_candidate.protein_log2fc,
                        10,
                    )
                ),
            )
        )
    return tuple(
        sorted(
            analyzed,
            key=lambda entry: (
                entry.site_id,
                entry.acetylation_type.value,
            ),
        )
    )


def render_acetylation_site_analysis_tsv(
    entries: tuple[PtmAcetylSiteAnalysisEntry, ...],
) -> str:
    """Render acetylation site analysis rows as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "site_id",
            "acetylation_type",
            "lysine_position",
            "n_terminal",
            "domain_context",
            "abundance_corrected_effect",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.site_id,
                entry.acetylation_type.value,
                "" if entry.lysine_position is None else entry.lysine_position,
                str(entry.n_terminal).lower(),
                entry.domain_context,
                (
                    ""
                    if entry.abundance_corrected_effect is None
                    else entry.abundance_corrected_effect
                ),
            )
        )
    return buffer.getvalue()


def _acetylation_type(entry: PtmAcetylSiteCandidate) -> PtmAcetylationType:
    if entry.position == 1:
        return PtmAcetylationType.N_TERMINAL_ACETYLATION
    if entry.residue == "K":
        return PtmAcetylationType.LYSINE_ACETYLATION
    return PtmAcetylationType.NONCANONICAL_RESIDUE_ACETYLATION


__all__ = [
    "PtmAcetylProteinContext",
    "PtmAcetylSiteAnalysisEntry",
    "PtmAcetylSiteCandidate",
    "PtmAcetylationType",
    "analyze_acetylation_sites",
    "render_acetylation_site_analysis_tsv",
]
