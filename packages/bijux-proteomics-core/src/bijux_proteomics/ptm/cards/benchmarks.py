# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scientific benchmark surfaces for PTM credibility."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.ptm import (
    PtmEvidenceRecord,
    PtmLocalizationConfidenceTier as PtmLocalizationScoringTier,
    PtmMotifBackgroundMode,
    PtmOccupancyCounterpartEvidenceEntry,
    PtmOccupancyUncertainty,
    PtmProteinSiteMapping,
    PtmSiteEntry,
    build_ptm_motif_enrichment_background_provenance_report,
    build_ptm_occupancy_counterpart_report,
)
from bijux_proteomics.ptm.cards.proteoforms import (
    ProteoformEvidenceLevel,
    ProteoformPtmAssignment,
    build_proteoform_identity,
)
from bijux_proteomics.ptm.cards.review import (
    build_acetyl_specific_review_fixture_report,
    build_phospho_specific_review_fixture_report,
    build_ptm_site_localization_evidence_graph,
    build_ubiquitin_remnant_workflow_report,
    evaluate_glycopeptide_support_boundary,
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


class PtmRawSpectrumValidationLaneReport(JsonModel):
    """Raw-spectrum-linked validation lane for one PTM benchmark workflow."""

    model_config = ConfigDict(extra="forbid")

    raw_spectrum_artifact_path: str = Field(..., min_length=1)
    localized_spectrum_count: int = Field(..., ge=0)
    fragment_supported_spectrum_count: int = Field(..., ge=0)
    unsupported_spectrum_ids: tuple[str, ...] = Field(default_factory=tuple)
    ready_for_rescoring_follow_up: bool
    note: str = Field(..., min_length=1)


class PtmFamilyCredibilityDisposition(StrEnum):
    """Scientific credibility posture for one PTM family."""

    SUPPORTED = "supported"
    INTERPRETIVE_ONLY = "interpretive_only"
    REFUSED = "refused"


class PtmFamilyCredibilityTrack(JsonModel):
    """Separate scientific credibility track for one PTM family."""

    model_config = ConfigDict(extra="forbid")

    family_name: str = Field(..., min_length=1)
    disposition: PtmFamilyCredibilityDisposition
    evidence_summary: str = Field(..., min_length=1)
    caveats: tuple[str, ...] = Field(default_factory=tuple)


class PtmFamilyCredibilityTrackReport(JsonModel):
    """Family-specific PTM credibility tracks instead of one blob posture."""

    model_config = ConfigDict(extra="forbid")

    tracks: tuple[PtmFamilyCredibilityTrack, ...] = Field(default_factory=tuple)
    supported_families: tuple[str, ...] = Field(default_factory=tuple)
    interpretive_only_families: tuple[str, ...] = Field(default_factory=tuple)
    refused_families: tuple[str, ...] = Field(default_factory=tuple)


class ProteoformBenchmarkScenario(JsonModel):
    """One proteoform benchmark scenario with ambiguity and PTM combinatorics."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    sequence: str = Field(..., min_length=1)
    protein_origin: str = Field(..., min_length=1)
    evidence_level: ProteoformEvidenceLevel
    ptm_assignments: tuple[ProteoformPtmAssignment, ...] = Field(default_factory=tuple)
    isoform_ambiguous: bool = False
    shared_peptide_pressure: bool = False
    expected_interpretive_only: bool = False


class ProteoformBenchmarkEntry(JsonModel):
    """Observed proteoform benchmark result for one scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    canonical_proteoform_key: str = Field(..., min_length=1)
    assignment_count: int = Field(..., ge=0)
    interpretive_only: bool
    note: str = Field(..., min_length=1)


class ProteoformBenchmarkReport(JsonModel):
    """Benchmark over proteoform ambiguity, shared peptides, and PTM combinatorics."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ProteoformBenchmarkEntry, ...] = Field(default_factory=tuple)
    interpretive_only_count: int = Field(..., ge=0)


class PtmOccupancyStressBenchmarkReport(JsonModel):
    """Occupancy benchmark under missing-feature and replicate variability pressure."""

    model_config = ConfigDict(extra="forbid")

    complete_counterpart_count: int = Field(..., ge=0)
    missing_counterpart_count: int = Field(..., ge=0)
    ambiguous_site_count: int = Field(..., ge=0)
    occupancy_shift_fraction: float = Field(..., ge=0.0, le=1.0)
    stable_under_replicate_variability: bool
    note: str = Field(..., min_length=1)


class GlycopeptideSupportRoadmapReport(JsonModel):
    """Scientific and engineering roadmap required for credible glycopeptide support."""

    model_config = ConfigDict(extra="forbid")

    requested_workflow: str = Field(..., min_length=1)
    current_disposition: str = Field(..., min_length=1)
    required_scientific_work: tuple[str, ...] = Field(default_factory=tuple)
    required_engineering_work: tuple[str, ...] = Field(default_factory=tuple)
    blocking_evidence_fields: tuple[str, ...] = Field(default_factory=tuple)


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
    _ = (
        decisive_probability_threshold,
        supported_probability_threshold,
        minimum_fragment_ion_count,
    )

    graph = build_ptm_site_localization_evidence_graph(
        records,
        mappings,
        fragment_ion_support_by_spectrum=fragment_ion_support_by_spectrum,
    )
    entries: list[PtmLocalizationConfidenceBenchmarkEntry] = []
    for node in graph.nodes:
        fragment_ion_count = len(
            node.supported_site_determining_ions or node.fragment_ions
        )
        if node.localization_tier is PtmLocalizationScoringTier.AMBIGUOUS:
            tier = PtmLocalizationConfidenceTier.AMBIGUOUS
            note = "site remains ambiguous and should not travel as a decisive localization claim"
        elif node.localization_tier is PtmLocalizationScoringTier.HIGH_CONFIDENCE:
            tier = PtmLocalizationConfidenceTier.DECISIVE
            note = (
                "site has high localization support and enough imported probability "
                "or site-determining evidence for a decisive localization call"
            )
        elif node.localization_tier is PtmLocalizationScoringTier.SUPPORTED:
            tier = PtmLocalizationConfidenceTier.SUPPORTED
            note = (
                "site is reviewable but still short of decisive localization evidence"
            )
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
            1
            for entry in entries
            if entry.confidence_tier is PtmLocalizationConfidenceTier.DECISIVE
        ),
        supported_count=sum(
            1
            for entry in entries
            if entry.confidence_tier is PtmLocalizationConfidenceTier.SUPPORTED
        ),
        ambiguous_count=sum(
            1
            for entry in entries
            if entry.confidence_tier is PtmLocalizationConfidenceTier.AMBIGUOUS
        ),
        refused_count=sum(
            1
            for entry in entries
            if entry.confidence_tier is PtmLocalizationConfidenceTier.REFUSED
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
    occupancy_by_site: dict[str, list[PtmOccupancyCounterpartEvidenceEntry]] = {}
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
        background_mode=PtmMotifBackgroundMode.WHOLE_PROTEOME_BACKGROUND,
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
        caveats.append(
            "foreground site count is too small for strong motif biology claims"
        )
    if ambiguous_fraction > maximum_ambiguous_site_fraction:
        caveats.append(
            "site ambiguity fraction is high enough to weaken motif interpretation"
        )
    if dominant_fraction > maximum_dominant_protein_fraction:
        caveats.append("motif signal is concentrated in too few proteins")
    disposition = (
        PtmMotifCredibilityDisposition.CREDIBLE
        if not caveats
        else PtmMotifCredibilityDisposition.INTERPRETIVE_ONLY
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
            rationale.append(
                "modified and unmodified counterpart evidence is incomplete"
            )
        if (
            site_entry.best_q_value is None
            or site_entry.best_q_value > maximum_site_q_value
        ):
            rationale.append("site-level q-value remains too weak for lab targeting")
        disposition = (
            PtmLabTargetingDisposition.TARGETABLE
            if not rationale
            else PtmLabTargetingDisposition.INTERPRETIVE_ONLY
        )
        if not rationale:
            rationale.append(
                "site clears localization, occupancy, and q-value requirements"
            )
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
            1
            for entry in entries
            if entry.disposition is PtmLabTargetingDisposition.TARGETABLE
        ),
        interpretive_only_count=sum(
            1
            for entry in entries
            if entry.disposition is PtmLabTargetingDisposition.INTERPRETIVE_ONLY
        ),
    )


def build_ptm_raw_spectrum_validation_lane_report(
    records: tuple[PtmEvidenceRecord, ...],
    *,
    raw_spectrum_artifact_path: str,
    fragment_ion_support_by_spectrum: dict[str, tuple[str, ...]],
) -> PtmRawSpectrumValidationLaneReport:
    """Link PTM localization review back to raw-spectrum-like fragment support."""

    localized_spectrum_ids = tuple(sorted({record.spectrum_id for record in records}))
    fragment_supported = tuple(
        spectrum_id
        for spectrum_id in localized_spectrum_ids
        if fragment_ion_support_by_spectrum.get(spectrum_id)
    )
    unsupported = tuple(
        spectrum_id
        for spectrum_id in localized_spectrum_ids
        if not fragment_ion_support_by_spectrum.get(spectrum_id)
    )
    ready = len(fragment_supported) == len(localized_spectrum_ids) and bool(
        fragment_supported
    )
    return PtmRawSpectrumValidationLaneReport(
        raw_spectrum_artifact_path=raw_spectrum_artifact_path,
        localized_spectrum_count=len(localized_spectrum_ids),
        fragment_supported_spectrum_count=len(fragment_supported),
        unsupported_spectrum_ids=unsupported,
        ready_for_rescoring_follow_up=ready,
        note=(
            "all localized spectra remain linked to fragment-ion support for rescoring follow-up"
            if ready
            else "some localized spectra still lack raw-spectrum-linked fragment support and remain review-only"
        ),
    )


def build_ptm_family_credibility_track_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    feature_records: tuple[Ms1FeatureRecord, ...],
    protein_sequences: Mapping[str, str],
) -> PtmFamilyCredibilityTrackReport:
    """Build separate credibility tracks for major PTM families."""

    phospho = build_phospho_specific_review_fixture_report(
        site_entries,
        feature_records=feature_records,
        protein_sequences=protein_sequences,
    )
    acetyl = build_acetyl_specific_review_fixture_report(
        site_entries,
        feature_records=feature_records,
        protein_sequences=protein_sequences,
    )
    ubiquitin = build_ubiquitin_remnant_workflow_report(
        site_entries,
        feature_records=feature_records,
    )
    glyco = evaluate_glycopeptide_support_boundary(
        requested_workflow="n_glycopeptide_localization",
        has_glycan_composition=False,
        has_glycosite_localization=False,
        has_oxonium_ion_support=False,
        treats_as_ordinary_modification=True,
    )
    tracks = (
        PtmFamilyCredibilityTrack(
            family_name="phosphorylation",
            disposition=(
                PtmFamilyCredibilityDisposition.INTERPRETIVE_ONLY
                if phospho.ambiguous_site_keys or phospho.caveats
                else PtmFamilyCredibilityDisposition.SUPPORTED
            ),
            evidence_summary="phospho review includes localization, motif windows, and occupancy-linked evidence",
            caveats=phospho.caveats,
        ),
        PtmFamilyCredibilityTrack(
            family_name="acetylation",
            disposition=(
                PtmFamilyCredibilityDisposition.INTERPRETIVE_ONLY
                if acetyl.caveats
                else PtmFamilyCredibilityDisposition.SUPPORTED
            ),
            evidence_summary="acetyl review distinguishes terminal and residue placements with occupancy-linked caveats",
            caveats=acetyl.caveats,
        ),
        PtmFamilyCredibilityTrack(
            family_name="ubiquitin_remnant",
            disposition=(
                PtmFamilyCredibilityDisposition.INTERPRETIVE_ONLY
                if ubiquitin.ambiguous_entry_count or ubiquitin.non_lysine_entry_count
                else PtmFamilyCredibilityDisposition.SUPPORTED
            ),
            evidence_summary="ubiquitin-remnant review checks lysine consistency, ambiguity, and quant-linked sample presence",
            caveats=(
                *(
                    ("contains ambiguous ubiquitin-remnant entries",)
                    if ubiquitin.ambiguous_entry_count
                    else ()
                ),
                *(
                    ("contains non-lysine remnant inconsistencies",)
                    if ubiquitin.non_lysine_entry_count
                    else ()
                ),
            ),
        ),
        PtmFamilyCredibilityTrack(
            family_name="glyco_adjacent",
            disposition=PtmFamilyCredibilityDisposition.REFUSED,
            evidence_summary="glyco-adjacent support remains refused until glyco-specific evidence semantics are implemented",
            caveats=(
                glyco.reason,
                *glyco.notes,
            ),
        ),
    )
    return PtmFamilyCredibilityTrackReport(
        tracks=tracks,
        supported_families=tuple(
            track.family_name
            for track in tracks
            if track.disposition is PtmFamilyCredibilityDisposition.SUPPORTED
        ),
        interpretive_only_families=tuple(
            track.family_name
            for track in tracks
            if track.disposition is PtmFamilyCredibilityDisposition.INTERPRETIVE_ONLY
        ),
        refused_families=tuple(
            track.family_name
            for track in tracks
            if track.disposition is PtmFamilyCredibilityDisposition.REFUSED
        ),
    )


def build_proteoform_benchmark_report(
    scenarios: tuple[ProteoformBenchmarkScenario, ...],
) -> ProteoformBenchmarkReport:
    """Benchmark proteoform interpretation under isoform and PTM-combination pressure."""

    entries: list[ProteoformBenchmarkEntry] = []
    for scenario in scenarios:
        identity = build_proteoform_identity(
            sequence=scenario.sequence,
            protein_origin=scenario.protein_origin,
            evidence_level=scenario.evidence_level,
            ptm_assignments=scenario.ptm_assignments,
            ambiguity_summary=(
                "isoform ambiguity and shared peptide pressure remain active"
                if scenario.isoform_ambiguous or scenario.shared_peptide_pressure
                else None
            ),
        )
        interpretive_only = (
            scenario.expected_interpretive_only
            or scenario.isoform_ambiguous
            or scenario.shared_peptide_pressure
            or len(scenario.ptm_assignments) > 2
        )
        entries.append(
            ProteoformBenchmarkEntry(
                scenario_id=scenario.scenario_id,
                canonical_proteoform_key=identity.canonical_proteoform_key,
                assignment_count=len(identity.ptm_assignments),
                interpretive_only=interpretive_only,
                note=(
                    "proteoform remains interpretive-only because isoform or combinatorial pressure is still unresolved"
                    if interpretive_only
                    else "proteoform identity stays bounded and reviewable under the benchmark scenario"
                ),
            )
        )
    return ProteoformBenchmarkReport(
        entries=tuple(entries),
        interpretive_only_count=sum(1 for entry in entries if entry.interpretive_only),
    )


def build_ptm_occupancy_stress_benchmark_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    baseline_feature_records: tuple[Ms1FeatureRecord, ...],
    stressed_feature_records: tuple[Ms1FeatureRecord, ...],
) -> PtmOccupancyStressBenchmarkReport:
    """Benchmark occupancy behavior under missing-feature and replicate pressure."""

    baseline = build_ptm_occupancy_counterpart_report(
        site_entries,
        feature_records=baseline_feature_records,
    )
    stressed = build_ptm_occupancy_counterpart_report(
        site_entries,
        feature_records=stressed_feature_records,
    )
    baseline_complete = sum(
        1
        for entry in baseline.entries
        if entry.uncertainty is PtmOccupancyUncertainty.NONE
    )
    stressed_complete = sum(
        1
        for entry in stressed.entries
        if entry.uncertainty is PtmOccupancyUncertainty.NONE
    )
    denominator = max(baseline_complete, 1)
    shift_fraction = abs(baseline_complete - stressed_complete) / denominator
    stable = shift_fraction <= 0.5
    return PtmOccupancyStressBenchmarkReport(
        complete_counterpart_count=stressed_complete,
        missing_counterpart_count=stressed.missing_counterpart_count,
        ambiguous_site_count=stressed.ambiguous_site_count,
        occupancy_shift_fraction=round(shift_fraction, 6),
        stable_under_replicate_variability=stable,
        note=(
            "occupancy support stays bounded under replicate variability and missing-feature pressure"
            if stable
            else "occupancy support degrades sharply under missing-feature or replicate pressure"
        ),
    )


def build_glycopeptide_support_roadmap_report(
    *,
    requested_workflow: str,
) -> GlycopeptideSupportRoadmapReport:
    """Define the exact work needed before glycopeptide support becomes credible."""

    boundary = evaluate_glycopeptide_support_boundary(
        requested_workflow=requested_workflow,
        has_glycan_composition=False,
        has_glycosite_localization=False,
        has_oxonium_ion_support=False,
        treats_as_ordinary_modification=True,
    )
    return GlycopeptideSupportRoadmapReport(
        requested_workflow=requested_workflow,
        current_disposition=boundary.disposition.value,
        required_scientific_work=(
            "define glycan-composition evidence semantics instead of flattening glycans into ordinary modifications",
            "require glycosite-localization evidence with oxonium-ion support and glyco-aware false-localization controls",
            "separate glycopeptide family claims from phospho-style site semantics in benchmark and review outputs",
        ),
        required_engineering_work=(
            "build glyco-aware import contracts that preserve glycan composition and site-localization fields together",
            "add glyco-specific benchmark fixtures and rescoring surfaces instead of TSV-only placeholder support",
            "add release-facing review artifacts that state glyco-family scope and unsupported vendor behaviors explicitly",
        ),
        blocking_evidence_fields=boundary.missing_evidence_fields,
    )
