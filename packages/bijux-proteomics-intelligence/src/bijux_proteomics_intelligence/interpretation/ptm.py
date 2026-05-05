# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""PTM-site interpretation owners with motif and occupancy context."""

from __future__ import annotations

from collections import Counter, defaultdict

from pydantic import ConfigDict, Field

from bijux_proteomics.ptm import (
    PtmMotifWindow,
    PtmOccupancyEntry,
    PtmSiteEntry,
    PtmSiteFdrReport,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.interpretation.pathways import (
    AnnotationCategory,
    ProteinAnnotationAssignment,
    _annotation_lookup,
)

class PtmInterpretationSite(JsonModel):
    """One interpreted PTM site signal."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    occupancy_shift: float | None = None
    motif_windows: tuple[str, ...] = Field(default_factory=tuple)
    advisory_terms: tuple[str, ...] = Field(default_factory=tuple)
    accepted: bool

class PtmInterpretationReport(JsonModel):
    """Interpretation report for PTM site signals."""

    model_config = ConfigDict(extra="forbid")

    accepted_site_count: int = Field(..., ge=0)
    changed_sites: tuple[PtmInterpretationSite, ...] = Field(default_factory=tuple)
    advisory_kinases: tuple[str, ...] = Field(default_factory=tuple)
    advisory_pathways: tuple[str, ...] = Field(default_factory=tuple)
    interpretation_summary: str = Field(..., min_length=1)

def interpret_ptm_sites(
    site_table: tuple[PtmSiteEntry, ...],
    fdr_report: PtmSiteFdrReport,
    *,
    motif_windows: tuple[PtmMotifWindow, ...] = (),
    occupancy: tuple[PtmOccupancyEntry, ...] = (),
    annotations: tuple[ProteinAnnotationAssignment, ...] = (),
    occupancy_shift_threshold: float = 0.2,
) -> PtmInterpretationReport:
    """Interpret PTM site evidence with occupancy and motif context."""
    accepted_sites = {entry.site_key for entry in fdr_report.entries if entry.accepted}
    motif_lookup: dict[str, list[str]] = defaultdict(list)
    for motif in motif_windows:
        motif_lookup[motif.site_key].append(motif.window)
    annotation_lookup = _annotation_lookup(annotations)
    occupancy_lookup: dict[str, list[float]] = defaultdict(list)
    for item in occupancy:
        if item.occupancy_fraction is not None:
            occupancy_lookup[item.site_key].append(item.occupancy_fraction)
    changed_sites: list[PtmInterpretationSite] = []
    advisory_kinases: Counter[str] = Counter()
    advisory_pathways: Counter[str] = Counter()
    for site in site_table:
        if site.site_key not in accepted_sites:
            continue
        occupancy_values = occupancy_lookup.get(site.site_key, [])
        occupancy_shift = None
        if occupancy_values:
            occupancy_shift = max(occupancy_values) - min(occupancy_values)
        site_terms = tuple(
            sorted(
                {
                    annotation.term_name
                    for annotation in annotation_lookup.get(site.protein_ref, ())
                    if annotation.category
                    in {AnnotationCategory.KINASE, AnnotationCategory.PATHWAY}
                }
            )
        )
        for annotation in annotation_lookup.get(site.protein_ref, ()):
            if annotation.category is AnnotationCategory.KINASE:
                advisory_kinases[annotation.term_name] += 1
            if annotation.category is AnnotationCategory.PATHWAY:
                advisory_pathways[annotation.term_name] += 1
        if occupancy_shift is None or occupancy_shift >= occupancy_shift_threshold:
            changed_sites.append(
                PtmInterpretationSite(
                    site_key=site.site_key,
                    occupancy_shift=occupancy_shift,
                    motif_windows=tuple(motif_lookup.get(site.site_key, ())),
                    advisory_terms=site_terms,
                    accepted=True,
                )
            )
    return PtmInterpretationReport(
        accepted_site_count=len(accepted_sites),
        changed_sites=tuple(sorted(changed_sites, key=lambda item: item.site_key)),
        advisory_kinases=tuple(term for term, _ in advisory_kinases.most_common()),
        advisory_pathways=tuple(term for term, _ in advisory_pathways.most_common()),
        interpretation_summary=(
            f"{len(changed_sites)} accepted PTM sites show interpretable occupancy or motif signal."
        ),
    )
