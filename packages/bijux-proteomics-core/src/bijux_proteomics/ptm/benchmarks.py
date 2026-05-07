# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scientific benchmark surfaces for PTM credibility."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.ptm import PtmEvidenceRecord, PtmProteinSiteMapping
from bijux_proteomics.ptm.review import build_ptm_site_localization_evidence_graph
from bijux_proteomics_foundation import JsonModel


class PtmLocalizationConfidenceTier(StrEnum):
    """Confidence ladder for PTM site localization claims."""

    DECISIVE = "decisive"
    SUPPORTED = "supported"
    AMBIGUOUS = "ambiguous"
    REFUSED = "refused"


class PtmLocalizationConfidenceBenchmarkEntry(JsonModel):
    """One PTM site classified on the localization confidence ladder."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    localization_probability: float = Field(..., ge=0.0, le=1.0)
    ambiguity_present: bool
    supporting_spectrum_count: int = Field(..., ge=0)
    supporting_peptide_count: int = Field(..., ge=0)
    fragment_ion_count: int = Field(..., ge=0)
    confidence_tier: PtmLocalizationConfidenceTier
    note: str = Field(..., min_length=1)


class PtmLocalizationConfidenceBenchmarkReport(JsonModel):
    """Benchmark report for PTM localization confidence behavior."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PtmLocalizationConfidenceBenchmarkEntry, ...] = Field(
        default_factory=tuple
    )
    decisive_count: int = Field(..., ge=0)
    supported_count: int = Field(..., ge=0)
    ambiguous_count: int = Field(..., ge=0)
    refused_count: int = Field(..., ge=0)
    ready_for_site_level_claims: bool


def build_ptm_localization_confidence_benchmark_report(
    records: tuple[PtmEvidenceRecord, ...],
    mappings: tuple[PtmProteinSiteMapping, ...],
    *,
    fragment_ion_support_by_spectrum: dict[str, tuple[str, ...]] | None = None,
    decisive_probability_threshold: float = 0.95,
    supported_probability_threshold: float = 0.75,
    minimum_fragment_ion_count: int = 2,
) -> PtmLocalizationConfidenceBenchmarkReport:
    """Score PTM localization sites on a public confidence ladder."""

    graph = build_ptm_site_localization_evidence_graph(
        records,
        mappings,
        fragment_ion_support_by_spectrum=fragment_ion_support_by_spectrum,
    )
    entries: list[PtmLocalizationConfidenceBenchmarkEntry] = []
    for node in graph.nodes:
        fragment_ion_count = len(node.fragment_ions)
        if node.ambiguous:
            tier = PtmLocalizationConfidenceTier.AMBIGUOUS
            note = "site remains ambiguous and should not travel as a decisive localization claim"
        elif (
            node.localization_probability >= decisive_probability_threshold
            and fragment_ion_count >= minimum_fragment_ion_count
        ):
            tier = PtmLocalizationConfidenceTier.DECISIVE
            note = "site has high localization support and sufficient fragment-ion evidence"
        elif node.localization_probability >= supported_probability_threshold:
            tier = PtmLocalizationConfidenceTier.SUPPORTED
            note = "site is reviewable but still short of decisive localization evidence"
        else:
            tier = PtmLocalizationConfidenceTier.REFUSED
            note = "site localization remains too weak for site-level claims"
        entries.append(
            PtmLocalizationConfidenceBenchmarkEntry(
                site_key=node.site_key,
                localization_probability=node.localization_probability,
                ambiguity_present=node.ambiguous,
                supporting_spectrum_count=len(node.psm_spectrum_ids),
                supporting_peptide_count=len(node.localized_peptides),
                fragment_ion_count=fragment_ion_count,
                confidence_tier=tier,
                note=note,
            )
        )
    return PtmLocalizationConfidenceBenchmarkReport(
        entries=tuple(entries),
        decisive_count=sum(
            1 for entry in entries if entry.confidence_tier is PtmLocalizationConfidenceTier.DECISIVE
        ),
        supported_count=sum(
            1 for entry in entries if entry.confidence_tier is PtmLocalizationConfidenceTier.SUPPORTED
        ),
        ambiguous_count=sum(
            1 for entry in entries if entry.confidence_tier is PtmLocalizationConfidenceTier.AMBIGUOUS
        ),
        refused_count=sum(
            1 for entry in entries if entry.confidence_tier is PtmLocalizationConfidenceTier.REFUSED
        ),
        ready_for_site_level_claims=all(
            entry.confidence_tier
            in {
                PtmLocalizationConfidenceTier.DECISIVE,
                PtmLocalizationConfidenceTier.SUPPORTED,
            }
            for entry in entries
        ),
    )
