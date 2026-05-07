# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scientific benchmark surfaces for PTM credibility."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.ptm import (
    PtmEvidenceRecord,
    PtmOccupancyUncertainty,
    PtmProteinSiteMapping,
    PtmSiteEntry,
)
from bijux_proteomics.ptm.review import (
    build_ptm_motif_enrichment_background_provenance_report,
    build_ptm_occupancy_counterpart_report,
    build_ptm_site_localization_evidence_graph,
)
from bijux_proteomics.quantification import Ms1FeatureRecord
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


class PtmAmbiguityPropagationBenchmarkEntry(JsonModel):
    """How site ambiguity propagates into downstream PTM quant interpretation."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    localization_ambiguous: bool
    occupancy_sample_count: int = Field(..., ge=0)
    ambiguous_occupancy_count: int = Field(..., ge=0)
    missing_counterpart_count: int = Field(..., ge=0)
    propagated_to_quant: bool
    interpretive_only: bool
    note: str = Field(..., min_length=1)


class PtmAmbiguityPropagationBenchmarkReport(JsonModel):
    """Benchmark whether PTM ambiguity truly downgrades downstream interpretation."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PtmAmbiguityPropagationBenchmarkEntry, ...] = Field(
        default_factory=tuple
    )
    propagated_site_count: int = Field(..., ge=0)
    interpretive_only_count: int = Field(..., ge=0)


class PtmMotifCredibilityDisposition(StrEnum):
    """Whether a PTM motif result is credible enough for biological reading."""

    CREDIBLE = "credible"
    INTERPRETIVE_ONLY = "interpretive_only"


class PtmMotifCredibilityBenchmarkReport(JsonModel):
    """Benchmark report that prevents overreading PTM motif enrichment output."""

    model_config = ConfigDict(extra="forbid")

    modification_name: str = Field(..., min_length=1)
    foreground_site_count: int = Field(..., ge=0)
    background_site_count: int = Field(..., ge=0)
    ambiguous_site_fraction: float = Field(..., ge=0.0, le=1.0)
    dominant_protein_fraction: float = Field(..., ge=0.0, le=1.0)
    disposition: PtmMotifCredibilityDisposition
    caveats: tuple[str, ...] = Field(default_factory=tuple)


class PtmLabTargetingDisposition(StrEnum):
    """Disposition for downstream lab targeting of PTM evidence."""

    TARGETABLE = "targetable"
    INTERPRETIVE_ONLY = "interpretive_only"


class PtmLabTargetingRubricEntry(JsonModel):
    """One PTM site evaluated against the public lab-targeting rubric."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    localization_confidence_tier: PtmLocalizationConfidenceTier
    occupancy_complete: bool
    ambiguous_site: bool
    best_q_value: float | None = Field(default=None, ge=0.0)
    disposition: PtmLabTargetingDisposition
    rationale: tuple[str, ...] = Field(default_factory=tuple)


class PtmLabTargetingRubricReport(JsonModel):
    """Public rubric for when PTM evidence is ready for lab targeting."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PtmLabTargetingRubricEntry, ...] = Field(default_factory=tuple)
    targetable_count: int = Field(..., ge=0)
    interpretive_only_count: int = Field(..., ge=0)


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


def build_ptm_ambiguity_propagation_benchmark_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    feature_records: tuple[Ms1FeatureRecord, ...],
) -> PtmAmbiguityPropagationBenchmarkReport:
    """Benchmark how unresolved PTM localization propagates into occupancy claims."""

    occupancy_report = build_ptm_occupancy_counterpart_report(
        site_entries,
        feature_records=feature_records,
    )
    occupancy_by_site: dict[str, list] = {}
    for entry in occupancy_report.entries:
        occupancy_by_site.setdefault(entry.site_key, []).append(entry)
    report_entries: list[PtmAmbiguityPropagationBenchmarkEntry] = []
    for site_entry in site_entries:
        occupancy_entries = occupancy_by_site.get(site_entry.site_key, [])
        ambiguous_occupancy_count = sum(
            1
            for entry in occupancy_entries
            if entry.uncertainty is PtmOccupancyUncertainty.AMBIGUOUS_SITE
        )
        missing_counterpart_count = sum(
            1
            for entry in occupancy_entries
            if entry.uncertainty is PtmOccupancyUncertainty.MISSING_COUNTERPART
        )
        propagated = site_entry.ambiguous and ambiguous_occupancy_count > 0
        interpretive_only = site_entry.ambiguous or missing_counterpart_count > 0
        report_entries.append(
            PtmAmbiguityPropagationBenchmarkEntry(
                site_key=site_entry.site_key,
                localization_ambiguous=site_entry.ambiguous,
                occupancy_sample_count=len(occupancy_entries),
                ambiguous_occupancy_count=ambiguous_occupancy_count,
                missing_counterpart_count=missing_counterpart_count,
                propagated_to_quant=propagated,
                interpretive_only=interpretive_only,
                note=(
                    "localization ambiguity propagated into occupancy uncertainty"
                    if propagated
                    else "site-level occupancy remains usable only within its explicit caveats"
                    if interpretive_only
                    else "site-level occupancy remains aligned with resolved localization"
                ),
            )
        )
    return PtmAmbiguityPropagationBenchmarkReport(
        entries=tuple(report_entries),
        propagated_site_count=sum(
            1 for entry in report_entries if entry.propagated_to_quant
        ),
        interpretive_only_count=sum(
            1 for entry in report_entries if entry.interpretive_only
        ),
    )


def build_ptm_motif_credibility_benchmark_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    protein_sequences: dict[str, str],
    modification_name: str,
    minimum_foreground_site_count: int = 3,
    maximum_ambiguous_site_fraction: float = 0.25,
    maximum_dominant_protein_fraction: float = 0.6,
) -> PtmMotifCredibilityBenchmarkReport:
    """Check whether a PTM motif signal is strong enough for biological reading."""

    report = build_ptm_motif_enrichment_background_provenance_report(
        site_entries,
        protein_sequences=protein_sequences,
        modification_name=modification_name,
        background_universe="all_modified_residue_candidates_in_observed_proteins",
        applied_filters=(
            "preserve_site_level_ambiguity",
            "preserve_site_level_decoy_state",
        ),
    )
    relevant_sites = tuple(
        entry for entry in site_entries if entry.modification_name == modification_name
    )
    foreground_count = len(relevant_sites)
    ambiguous_fraction = (
        sum(1 for entry in relevant_sites if entry.ambiguous) / foreground_count
        if foreground_count
        else 0.0
    )
    protein_counts: dict[str, int] = {}
    for entry in relevant_sites:
        protein_counts[entry.protein_ref] = protein_counts.get(entry.protein_ref, 0) + 1
    dominant_fraction = (
        max(protein_counts.values()) / foreground_count if protein_counts else 0.0
    )
    caveats: list[str] = list(report.caveats)
    if foreground_count < minimum_foreground_site_count:
        caveats.append("foreground site count is too small for strong motif biology claims")
    if ambiguous_fraction > maximum_ambiguous_site_fraction:
        caveats.append("site ambiguity fraction is high enough to weaken motif interpretation")
    if dominant_fraction > maximum_dominant_protein_fraction:
        caveats.append("motif signal is concentrated in too few proteins")
    disposition = (
        PtmMotifCredibilityDisposition.CREDIBLE if not caveats else PtmMotifCredibilityDisposition.INTERPRETIVE_ONLY
    )
    return PtmMotifCredibilityBenchmarkReport(
        modification_name=modification_name,
        foreground_site_count=foreground_count,
        background_site_count=report.background_site_count,
        ambiguous_site_fraction=round(ambiguous_fraction, 6),
        dominant_protein_fraction=round(dominant_fraction, 6),
        disposition=disposition,
        caveats=tuple(caveats),
    )


def build_ptm_lab_targeting_rubric_report(
    records: tuple[PtmEvidenceRecord, ...],
    mappings: tuple[PtmProteinSiteMapping, ...],
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    feature_records: tuple[Ms1FeatureRecord, ...],
    fragment_ion_support_by_spectrum: dict[str, tuple[str, ...]] | None = None,
    maximum_site_q_value: float = 0.05,
) -> PtmLabTargetingRubricReport:
    """Apply one public rubric to PTM sites before lab-targeting claims."""

    localization = build_ptm_localization_confidence_benchmark_report(
        records,
        mappings,
        fragment_ion_support_by_spectrum=fragment_ion_support_by_spectrum,
    )
    localization_by_site = {entry.site_key: entry for entry in localization.entries}
    occupancy = build_ptm_occupancy_counterpart_report(
        site_entries,
        feature_records=feature_records,
    )
    incomplete_occupancy_sites = {
        entry.site_key
        for entry in occupancy.entries
        if entry.uncertainty is not PtmOccupancyUncertainty.NONE
    }
    entries: list[PtmLabTargetingRubricEntry] = []
    for site_entry in site_entries:
        localization_entry = localization_by_site.get(site_entry.site_key)
        localization_tier = (
            localization_entry.confidence_tier
            if localization_entry is not None
            else PtmLocalizationConfidenceTier.REFUSED
        )
        occupancy_complete = site_entry.site_key not in incomplete_occupancy_sites
        rationale: list[str] = []
        if localization_tier is not PtmLocalizationConfidenceTier.DECISIVE:
            rationale.append("localization confidence is not decisive")
        if site_entry.ambiguous:
            rationale.append("site localization remains ambiguous")
        if not occupancy_complete:
            rationale.append("modified and unmodified counterpart evidence is incomplete")
        if site_entry.best_q_value is None or site_entry.best_q_value > maximum_site_q_value:
            rationale.append("site-level q-value remains too weak for lab targeting")
        disposition = (
            PtmLabTargetingDisposition.TARGETABLE
            if not rationale
            else PtmLabTargetingDisposition.INTERPRETIVE_ONLY
        )
        if not rationale:
            rationale.append("site clears localization, occupancy, and q-value requirements")
        entries.append(
            PtmLabTargetingRubricEntry(
                site_key=site_entry.site_key,
                localization_confidence_tier=localization_tier,
                occupancy_complete=occupancy_complete,
                ambiguous_site=site_entry.ambiguous,
                best_q_value=site_entry.best_q_value,
                disposition=disposition,
                rationale=tuple(rationale),
            )
        )
    return PtmLabTargetingRubricReport(
        entries=tuple(entries),
        targetable_count=sum(
            1 for entry in entries if entry.disposition is PtmLabTargetingDisposition.TARGETABLE
        ),
        interpretive_only_count=sum(
            1
            for entry in entries
            if entry.disposition is PtmLabTargetingDisposition.INTERPRETIVE_ONLY
        ),
    )
