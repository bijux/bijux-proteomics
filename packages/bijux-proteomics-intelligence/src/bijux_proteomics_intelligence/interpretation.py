# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Interpretation and enrichment contracts over proteomics evidence."""

from __future__ import annotations

from collections import Counter, defaultdict
from enum import StrEnum
import math

from pydantic import ConfigDict, Field

from bijux_proteomics import (
    BatchEffectAdvisoryReport,
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    ExperimentalDesignEntry,
    InstrumentBatchQcReport,
    LabelFreeQuantTable,
    LcmsRunQcReport,
    MissingValueKind,
    PtmMotifWindow,
    PtmOccupancyEntry,
    PtmSiteEntry,
    PtmSiteFdrReport,
    QcAssessmentSeverity,
    QcRunAssessmentReport,
    ReplicateCorrelationReport,
)
from bijux_proteomics_foundation import JsonModel


class AnnotationCategory(StrEnum):
    """Interpretation-level categories for protein annotations."""

    PATHWAY = "pathway"
    COMPARTMENT = "compartment"
    KINASE = "kinase"
    THEME = "theme"


class SignalDirection(StrEnum):
    """Direction of one biological or statistical signal."""

    UP = "up"
    DOWN = "down"
    MIXED = "mixed"


class PathwayInterpretationCautionCode(StrEnum):
    """Caution codes that block pathway-level overclaiming."""

    LOW_SIGNIFICANT_ENTITY_COUNT = "low_significant_entity_count"
    THEME_ONLY_SUPPORT = "theme_only_support"
    MIXED_SIGNAL_DIRECTION = "mixed_signal_direction"
    NO_ENRICHMENT_SUPPORT = "no_enrichment_support"


class AnalyticalContrastRejectionReason(StrEnum):
    """Reasons an analytical contrast recommendation is not valid yet."""

    INSUFFICIENT_REPLICATES = "insufficient_replicates"
    BATCH_CONFOUNDED = "batch_confounded"
    SINGLE_CONDITION = "single_condition"


class MissingnessPatternLabel(StrEnum):
    """Advisory pattern labels for missing-value structure."""

    MOSTLY_OBSERVED = "mostly_observed"
    CONDITION_LINKED = "condition_linked_missingness"
    MNAR_LIKE_LOW_SIGNAL = "mnar_like_low_signal"
    FILTER_DOMINATED = "filter_dominated"
    MAR_LIKE = "mar_like_random"
    MIXED = "mixed"


class OutlierInterpretationClass(StrEnum):
    """Classification of whether an outlier looks technical or biological."""

    TECHNICAL_ANOMALY = "technical_anomaly"
    PLAUSIBLE_BIOLOGICAL_EFFECT = "plausible_biological_effect"
    MIXED_SIGNAL = "mixed_signal"


class ProteinAnnotationAssignment(JsonModel):
    """One protein-to-term annotation with source provenance."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    term_id: str = Field(..., min_length=1)
    term_name: str = Field(..., min_length=1)
    category: AnnotationCategory
    source: str = Field(..., min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class RunInterpretationSignal(JsonModel):
    """One compact run-level interpretation signal."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    severity: QcAssessmentSeverity
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)


class RunInterpretationSummary(JsonModel):
    """Reviewable summary of one proteomics run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition: str | None = None
    spectrum_count: int = Field(..., ge=0)
    identified_spectrum_count: int = Field(..., ge=0)
    psm_count: int = Field(..., ge=0)
    quantified_entity_count: int = Field(..., ge=0)
    qc_blocked: bool
    major_signals: tuple[RunInterpretationSignal, ...] = Field(default_factory=tuple)
    interpretation_summary: str = Field(..., min_length=1)


class DifferentialConditionSignal(JsonModel):
    """One differential-abundance signal for a single entity."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    direction: SignalDirection
    log2_fold_change: float
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    annotation_terms: tuple[str, ...] = Field(default_factory=tuple)


class DifferentialStatisticalProvenance(JsonModel):
    """Statistical provenance for a differential interpretation."""

    model_config = ConfigDict(extra="forbid")

    entity_level: str = Field(..., min_length=1)
    normalization_method: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    significance_threshold: float = Field(..., ge=0.0, le=1.0)
    tested_entity_count: int = Field(..., ge=0)
    significant_entity_count: int = Field(..., ge=0)
    enrichment_method: str = Field(..., min_length=1)
    multiple_testing_method: str = Field(..., min_length=1)


class ProteinSetEnrichmentEntry(JsonModel):
    """One term-level overrepresentation result."""

    model_config = ConfigDict(extra="forbid")

    term_id: str = Field(..., min_length=1)
    term_name: str = Field(..., min_length=1)
    category: AnnotationCategory
    source: str = Field(..., min_length=1)
    overlap_count: int = Field(..., ge=0)
    query_size: int = Field(..., ge=0)
    annotated_background_count: int = Field(..., ge=0)
    background_size: int = Field(..., ge=0)
    overlap_proteins: tuple[str, ...] = Field(default_factory=tuple)
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    odds_ratio: float = Field(..., ge=0.0)


class EnrichmentProvenance(JsonModel):
    """Explicit background and multiple-testing provenance for enrichment."""

    model_config = ConfigDict(extra="forbid")

    background_proteins: tuple[str, ...] = Field(default_factory=tuple)
    tested_term_count: int = Field(..., ge=0)
    enrichment_method: str = Field(..., min_length=1)
    multiple_testing_method: str = Field(..., min_length=1)
    annotation_source_count: int = Field(..., ge=0)


class ProteinSetEnrichmentReport(JsonModel):
    """Overrepresentation report for one protein set."""

    model_config = ConfigDict(extra="forbid")

    query_protein_count: int = Field(..., ge=0)
    background_protein_count: int = Field(..., ge=0)
    provenance: EnrichmentProvenance
    entries: tuple[ProteinSetEnrichmentEntry, ...] = Field(default_factory=tuple)


class BiologicalTheme(JsonModel):
    """One extracted biological theme over a protein set."""

    model_config = ConfigDict(extra="forbid")

    term_id: str = Field(..., min_length=1)
    term_name: str = Field(..., min_length=1)
    category: AnnotationCategory
    source: str = Field(..., min_length=1)
    member_proteins: tuple[str, ...] = Field(default_factory=tuple)
    score: float
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)


class BiologicalThemeExtraction(JsonModel):
    """Top biological themes for one interpreted protein set."""

    model_config = ConfigDict(extra="forbid")

    query_protein_count: int = Field(..., ge=0)
    enrichment_provenance: EnrichmentProvenance
    themes: tuple[BiologicalTheme, ...] = Field(default_factory=tuple)


class PathwayInterpretationCaution(JsonModel):
    """One caution that keeps enrichment summaries from becoming overclaims."""

    model_config = ConfigDict(extra="forbid")

    code: PathwayInterpretationCautionCode
    blocked_claim: bool
    summary: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    recommended_next_step: str = Field(..., min_length=1)


class PathwayInterpretationCautionReport(JsonModel):
    """Caution report for pathway and thematic interpretation claims."""

    model_config = ConfigDict(extra="forbid")

    blocked: bool
    caution_items: tuple[PathwayInterpretationCaution, ...] = Field(
        default_factory=tuple
    )
    safe_summary: str = Field(..., min_length=1)


class DifferentialAbundanceInterpretation(JsonModel):
    """Differential-abundance interpretation with enrichment and provenance."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    top_upregulated: tuple[DifferentialConditionSignal, ...] = Field(
        default_factory=tuple
    )
    top_downregulated: tuple[DifferentialConditionSignal, ...] = Field(
        default_factory=tuple
    )
    enriched_terms: tuple[ProteinSetEnrichmentEntry, ...] = Field(default_factory=tuple)
    theme_summary: tuple[BiologicalTheme, ...] = Field(default_factory=tuple)
    caution_report: PathwayInterpretationCautionReport
    statistical_provenance: DifferentialStatisticalProvenance
    interpretation_summary: str = Field(..., min_length=1)


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


class ContaminantArtifactFinding(JsonModel):
    """One likely contaminant or workflow artifact explanation."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    severity: QcAssessmentSeverity
    supporting_metrics: dict[str, float] = Field(default_factory=dict)
    suggested_action: str = Field(..., min_length=1)


class ContaminantArtifactIntelligence(JsonModel):
    """Interpretation of likely contamination or acquisition artifacts."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    findings: tuple[ContaminantArtifactFinding, ...] = Field(default_factory=tuple)
    interpretation_summary: str = Field(..., min_length=1)


class AnalyticalContrastRecommendation(JsonModel):
    """One recommended or rejected analytical contrast."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    valid: bool
    replicate_counts: dict[str, int] = Field(default_factory=dict)
    shared_batches: tuple[str, ...] = Field(default_factory=tuple)
    rejection_reasons: tuple[AnalyticalContrastRejectionReason, ...] = Field(
        default_factory=tuple
    )
    rationale: str = Field(..., min_length=1)


class AnalyticalContrastRecommendationReport(JsonModel):
    """Recommended and rejected analytical contrasts over a design table."""

    model_config = ConfigDict(extra="forbid")

    condition_count: int = Field(..., ge=0)
    valid_contrasts: tuple[AnalyticalContrastRecommendation, ...] = Field(default_factory=tuple)
    rejected_contrasts: tuple[AnalyticalContrastRecommendation, ...] = Field(
        default_factory=tuple
    )


class MissingnessPatternEntry(JsonModel):
    """Pattern summary for one quantified entity."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    label: MissingnessPatternLabel
    observed_count: int = Field(..., ge=0)
    missing_count: int = Field(..., ge=0)
    condition_missing_counts: dict[str, int] = Field(default_factory=dict)
    note: str = Field(..., min_length=1)


class MissingnessPatternAnalysis(JsonModel):
    """Advisory classification of missingness behavior."""

    model_config = ConfigDict(extra="forbid")

    entity_level: str = Field(..., min_length=1)
    overall_label: MissingnessPatternLabel
    entries: tuple[MissingnessPatternEntry, ...] = Field(default_factory=tuple)
    interpretation_summary: str = Field(..., min_length=1)


class OutlierSampleExplanation(JsonModel):
    """Explanation for a sample or run flagged as an outlier."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    batch_id: str | None = None
    classification: OutlierInterpretationClass
    reasons: tuple[str, ...] = Field(default_factory=tuple)
    technical_reasons: tuple[str, ...] = Field(default_factory=tuple)
    biological_reasons: tuple[str, ...] = Field(default_factory=tuple)
    supporting_metrics: dict[str, float] = Field(default_factory=dict)
    recommended_follow_up: str = Field(..., min_length=1)
    interpretation_summary: str = Field(..., min_length=1)


class QuantQcEvidenceIntegrationReport(JsonModel):
    """Joint missingness, outlier, and QC interpretation over one quant surface."""

    model_config = ConfigDict(extra="forbid")

    entity_level: str = Field(..., min_length=1)
    missingness: MissingnessPatternAnalysis
    outliers: tuple[OutlierSampleExplanation, ...] = Field(default_factory=tuple)
    blocked_run_ids: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class RankedEntityScore(JsonModel):
    """One ranked entity for GSEA-style enrichment."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    score: float


class RankedEnrichmentEntry(JsonModel):
    """One ranked-set enrichment result."""

    model_config = ConfigDict(extra="forbid")

    term_id: str = Field(..., min_length=1)
    term_name: str = Field(..., min_length=1)
    category: AnnotationCategory
    source: str = Field(..., min_length=1)
    enrichment_score: float
    direction: SignalDirection
    hit_count: int = Field(..., ge=0)
    leading_edge: tuple[str, ...] = Field(default_factory=tuple)


class RankedEnrichmentReport(JsonModel):
    """GSEA-style ranked enrichment report."""

    model_config = ConfigDict(extra="forbid")

    entity_count: int = Field(..., ge=0)
    entries: tuple[RankedEnrichmentEntry, ...] = Field(default_factory=tuple)


def _bh_adjust(p_values: list[float]) -> list[float]:
    if not p_values:
        return []
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    total = len(indexed)
    adjusted = [0.0] * total
    running = 1.0
    for rank, (index, value) in enumerate(reversed(indexed), start=1):
        factor = total / (total - rank + 1)
        running = min(running, value * factor)
        adjusted[index] = min(1.0, running)
    return adjusted


def _annotation_lookup(
    annotations: tuple[ProteinAnnotationAssignment, ...],
) -> dict[str, list[ProteinAnnotationAssignment]]:
    lookup: dict[str, list[ProteinAnnotationAssignment]] = defaultdict(list)
    for annotation in annotations:
        lookup[annotation.protein_ref].append(annotation)
    return lookup


def _category_priority(category: AnnotationCategory) -> int:
    if category is AnnotationCategory.PATHWAY:
        return 0
    if category is AnnotationCategory.KINASE:
        return 1
    if category is AnnotationCategory.THEME:
        return 2
    return 3


def _term_lookup(
    annotations: tuple[ProteinAnnotationAssignment, ...],
) -> dict[tuple[str, AnnotationCategory, str, str], set[str]]:
    lookup: dict[tuple[str, AnnotationCategory, str, str], set[str]] = defaultdict(set)
    for annotation in annotations:
        key = (
            annotation.term_id,
            annotation.category,
            annotation.term_name,
            annotation.source,
        )
        lookup[key].add(annotation.protein_ref)
    return lookup


def _hypergeometric_tail(
    population_size: int, successes: int, draws: int, overlap: int
) -> float:
    denominator = math.comb(population_size, draws)
    tail = 0.0
    upper = min(successes, draws)
    for hits in range(overlap, upper + 1):
        tail += (
            math.comb(successes, hits)
            * math.comb(population_size - successes, draws - hits)
            / denominator
        )
    return min(1.0, tail)


def _odds_ratio(
    overlap: int,
    query_size: int,
    annotated_background_count: int,
    background_size: int,
) -> float:
    a = overlap + 0.5
    b = max(query_size - overlap, 0) + 0.5
    c = max(annotated_background_count - overlap, 0) + 0.5
    d = (
        max(background_size - query_size - annotated_background_count + overlap, 0)
        + 0.5
    )
    return (a * d) / (b * c)


def build_run_interpretation_summary(
    run_report: LcmsRunQcReport,
    run_assessment: QcRunAssessmentReport,
    *,
    quant_table: LabelFreeQuantTable | None = None,
) -> RunInterpretationSummary:
    """Build a concise run-level interpretation with QC-aware signals."""
    signals: list[RunInterpretationSignal] = []
    quant_entity_count = 0 if quant_table is None else len(quant_table.entity_ids)
    if run_assessment.blocked:
        signals.append(
            RunInterpretationSignal(
                code="qc-blocked",
                summary="QC policy blocks routine downstream interpretation for this run.",
                severity=QcAssessmentSeverity.FAILED,
                evidence_refs=("qc_run_assessment_report",),
            )
        )
    elif run_report.identification_rate >= 0.2:
        signals.append(
            RunInterpretationSignal(
                code="identification-ready",
                summary="Identification rate is high enough for routine interpretation.",
                severity=QcAssessmentSeverity.PASSED,
                evidence_refs=("lcms_run_qc_report.identification_rate",),
            )
        )
    if run_report.contaminant_summary.contaminant_psm_fraction >= 0.1:
        signals.append(
            RunInterpretationSignal(
                code="contaminant-pressure",
                summary="Contaminant burden is high enough to color biological interpretation.",
                severity=QcAssessmentSeverity.WARNING,
                evidence_refs=("lcms_run_qc_report.contaminant_summary",),
            )
        )
    if quant_table is not None and quant_table.entity_ids:
        signals.append(
            RunInterpretationSignal(
                code="quant-available",
                summary=f"{len(quant_table.entity_ids)} quantified entities are available for follow-on interpretation.",
                severity=QcAssessmentSeverity.PASSED,
                evidence_refs=("label_free_quant_table",),
            )
        )
    if not signals:
        signals.append(
            RunInterpretationSignal(
                code="interpretation-limited",
                summary="Run has limited stable signal and should be interpreted cautiously.",
                severity=QcAssessmentSeverity.NOT_ASSESSED,
                evidence_refs=("lcms_run_qc_report",),
            )
        )
    return RunInterpretationSummary(
        run_id=run_report.run_id,
        sample_id=run_report.sample_id,
        condition=run_report.condition,
        spectrum_count=run_report.spectrum_count,
        identified_spectrum_count=run_report.identified_spectrum_count,
        psm_count=run_report.psm_count,
        quantified_entity_count=quant_entity_count,
        qc_blocked=run_assessment.blocked,
        major_signals=tuple(signals),
        interpretation_summary=signals[0].summary,
    )


def compute_protein_set_enrichment(
    query_proteins: tuple[str, ...],
    background_proteins: tuple[str, ...],
    annotations: tuple[ProteinAnnotationAssignment, ...],
) -> ProteinSetEnrichmentReport:
    """Compute hypergeometric enrichment over protein annotations."""
    query = tuple(dict.fromkeys(query_proteins))
    background = tuple(dict.fromkeys(background_proteins))
    background_set = set(background)
    query_set = set(query)
    entries: list[ProteinSetEnrichmentEntry] = []
    tested_term_count = 0
    term_lookup = _term_lookup(annotations)
    for (term_id, category, term_name, source), proteins in term_lookup.items():
        annotated_background = tuple(
            sorted(protein for protein in proteins if protein in background_set)
        )
        if annotated_background:
            tested_term_count += 1
        overlap_proteins = tuple(
            sorted(protein for protein in annotated_background if protein in query_set)
        )
        if not overlap_proteins:
            continue
        p_value = _hypergeometric_tail(
            population_size=len(background_set),
            successes=len(annotated_background),
            draws=len(query_set),
            overlap=len(overlap_proteins),
        )
        entries.append(
            ProteinSetEnrichmentEntry(
                term_id=term_id,
                term_name=term_name,
                category=category,
                source=source,
                overlap_count=len(overlap_proteins),
                query_size=len(query_set),
                annotated_background_count=len(annotated_background),
                background_size=len(background_set),
                overlap_proteins=overlap_proteins,
                p_value=p_value,
                odds_ratio=_odds_ratio(
                    len(overlap_proteins),
                    len(query_set),
                    len(annotated_background),
                    len(background_set),
                ),
            )
        )
    adjusted = _bh_adjust([entry.p_value for entry in entries])
    ordered = sorted(
        entries,
        key=lambda item: (
            item.p_value,
            -(item.adjusted_p_value or item.p_value),
            -item.overlap_count,
            _category_priority(item.category),
            item.term_id,
        ),
    )
    finalized = tuple(
        entry.model_copy(update={"adjusted_p_value": adjusted[index]})
        for index, entry in enumerate(ordered)
    )
    return ProteinSetEnrichmentReport(
        query_protein_count=len(query_set),
        background_protein_count=len(background_set),
        provenance=EnrichmentProvenance(
            background_proteins=background,
            tested_term_count=tested_term_count,
            enrichment_method="hypergeometric-upper-tail",
            multiple_testing_method="benjamini-hochberg",
            annotation_source_count=len(
                {annotation.source for annotation in annotations}
            ),
        ),
        entries=finalized,
    )


def extract_biological_themes(
    query_proteins: tuple[str, ...],
    background_proteins: tuple[str, ...],
    annotations: tuple[ProteinAnnotationAssignment, ...],
    *,
    max_terms: int = 5,
) -> BiologicalThemeExtraction:
    """Extract top biological themes from enriched annotations."""
    enrichment = compute_protein_set_enrichment(
        query_proteins, background_proteins, annotations
    )
    themes = tuple(
        BiologicalTheme(
            term_id=entry.term_id,
            term_name=entry.term_name,
            category=entry.category,
            source=entry.source,
            member_proteins=entry.overlap_proteins,
            score=-math.log10(max(entry.adjusted_p_value or entry.p_value, 1e-12)),
            adjusted_p_value=entry.adjusted_p_value,
        )
        for entry in enrichment.entries[:max_terms]
    )
    return BiologicalThemeExtraction(
        query_protein_count=len(query_proteins),
        enrichment_provenance=enrichment.provenance,
        themes=themes,
    )


def _build_pathway_interpretation_caution_report(
    significant_entries: list[DifferentialAbundanceEntry],
    enriched_terms: tuple[ProteinSetEnrichmentEntry, ...],
    themes: tuple[BiologicalTheme, ...],
) -> PathwayInterpretationCautionReport:
    cautions: list[PathwayInterpretationCaution] = []
    directions = {
        SignalDirection.UP if entry.log2_fold_change > 0 else SignalDirection.DOWN
        for entry in significant_entries
        if entry.log2_fold_change != 0
    }
    if len(significant_entries) < 3:
        cautions.append(
            PathwayInterpretationCaution(
                code=PathwayInterpretationCautionCode.LOW_SIGNIFICANT_ENTITY_COUNT,
                blocked_claim=True,
                summary=(
                    "Too few significant entities support a durable pathway-level claim."
                ),
                evidence_refs=("differential_abundance_report.entries",),
                recommended_next_step=(
                    "collect more decisive differential evidence before elevating pathway claims"
                ),
            )
        )
    if not enriched_terms:
        cautions.append(
            PathwayInterpretationCaution(
                code=PathwayInterpretationCautionCode.NO_ENRICHMENT_SUPPORT,
                blocked_claim=True,
                summary="No enriched terms remain after significance filtering.",
                evidence_refs=("protein_set_enrichment_report.entries",),
                recommended_next_step=(
                    "avoid pathway language until term-level enrichment is reproducible"
                ),
            )
        )
    elif themes and all(
        theme.category in {AnnotationCategory.THEME, AnnotationCategory.COMPARTMENT}
        for theme in themes
    ):
        cautions.append(
            PathwayInterpretationCaution(
                code=PathwayInterpretationCautionCode.THEME_ONLY_SUPPORT,
                blocked_claim=True,
                summary=(
                    "Thematic or compartment summaries alone do not justify a pathway mechanism claim."
                ),
                evidence_refs=("biological_theme_extraction.themes",),
                recommended_next_step=(
                    "require pathway- or kinase-level support before making a mechanism claim"
                ),
            )
        )
    if len(directions) > 1:
        cautions.append(
            PathwayInterpretationCaution(
                code=PathwayInterpretationCautionCode.MIXED_SIGNAL_DIRECTION,
                blocked_claim=False,
                summary=(
                    "Up- and down-regulated signals both remain, so direction-specific pathway claims need caution."
                ),
                evidence_refs=("differential_abundance_report.entries",),
                recommended_next_step=(
                    "separate pathway language by direction or condition-specific subgroup"
                ),
            )
        )
    blocked = any(caution.blocked_claim for caution in cautions)
    if blocked:
        safe_summary = (
            "Pathway-level claims remain blocked; only constrained thematic summaries are safe."
        )
    elif cautions:
        safe_summary = (
            "Pathway summaries are usable only with the listed caution notes kept visible."
        )
    else:
        safe_summary = "Pathway interpretation has enough support for cautious use."
    return PathwayInterpretationCautionReport(
        blocked=blocked,
        caution_items=tuple(cautions),
        safe_summary=safe_summary,
    )


def interpret_differential_abundance(
    report: DifferentialAbundanceReport,
    annotations: tuple[ProteinAnnotationAssignment, ...],
    *,
    significance_threshold: float = 0.05,
    max_entities: int = 5,
    max_terms: int = 5,
) -> DifferentialAbundanceInterpretation:
    """Interpret differential abundance with term enrichment and provenance."""
    annotation_lookup = _annotation_lookup(annotations)
    significant = [
        entry
        for entry in report.entries
        if (
            entry.adjusted_p_value
            if entry.adjusted_p_value is not None
            else entry.p_value
        )
        <= significance_threshold
    ]
    ordered_up = sorted(
        (entry for entry in significant if entry.log2_fold_change > 0),
        key=lambda item: (-item.log2_fold_change, item.entity_id),
    )[:max_entities]
    ordered_down = sorted(
        (entry for entry in significant if entry.log2_fold_change < 0),
        key=lambda item: (item.log2_fold_change, item.entity_id),
    )[:max_entities]

    def _signal(entry: DifferentialAbundanceEntry) -> DifferentialConditionSignal:
        return DifferentialConditionSignal(
            entity_id=entry.entity_id,
            direction=SignalDirection.UP
            if entry.log2_fold_change > 0
            else SignalDirection.DOWN,
            log2_fold_change=entry.log2_fold_change,
            adjusted_p_value=entry.adjusted_p_value,
            annotation_terms=tuple(
                sorted(
                    {
                        annotation.term_name
                        for annotation in annotation_lookup.get(entry.entity_id, ())
                    }
                )
            ),
        )

    query_proteins = tuple(entry.entity_id for entry in significant)
    background_proteins = tuple(entry.entity_id for entry in report.entries)
    enrichment = compute_protein_set_enrichment(
        query_proteins, background_proteins, annotations
    )
    themes = extract_biological_themes(
        query_proteins,
        background_proteins,
        annotations,
        max_terms=max_terms,
    )
    caution_report = _build_pathway_interpretation_caution_report(
        significant,
        enrichment.entries[:max_terms],
        themes.themes,
    )
    summary = (
        f"{len(significant)} entities pass the significance threshold between "
        f"{report.condition_a} and {report.condition_b}."
    )
    if caution_report.blocked:
        summary += f" {caution_report.safe_summary}"
    return DifferentialAbundanceInterpretation(
        condition_a=report.condition_a,
        condition_b=report.condition_b,
        top_upregulated=tuple(_signal(entry) for entry in ordered_up),
        top_downregulated=tuple(_signal(entry) for entry in ordered_down),
        enriched_terms=enrichment.entries[:max_terms],
        theme_summary=themes.themes,
        caution_report=caution_report,
        statistical_provenance=DifferentialStatisticalProvenance(
            entity_level=report.entity_level.value,
            normalization_method=report.normalization_method.value,
            condition_a=report.condition_a,
            condition_b=report.condition_b,
            significance_threshold=significance_threshold,
            tested_entity_count=len(report.entries),
            significant_entity_count=len(significant),
            enrichment_method="hypergeometric-upper-tail",
            multiple_testing_method=enrichment.provenance.multiple_testing_method,
        ),
        interpretation_summary=summary,
    )


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


def interpret_contaminant_artifacts(
    run_report: LcmsRunQcReport,
    run_assessment: QcRunAssessmentReport,
) -> ContaminantArtifactIntelligence:
    """Explain likely contaminants or workflow artifacts from QC metrics."""
    findings: list[ContaminantArtifactFinding] = []
    if run_report.contaminant_summary.contaminant_psm_fraction >= 0.1:
        findings.append(
            ContaminantArtifactFinding(
                code="contaminant-burden",
                summary="Contaminant burden is high enough to suggest sample carryover or cleanup failure.",
                severity=QcAssessmentSeverity.WARNING,
                supporting_metrics={
                    "contaminant_psm_fraction": run_report.contaminant_summary.contaminant_psm_fraction,
                },
                suggested_action="inspect sample cleanup, wash steps, and contaminant database composition",
            )
        )
    if run_report.missed_cleavage_rate >= 0.2:
        findings.append(
            ContaminantArtifactFinding(
                code="digestion-specificity-loss",
                summary="Missed-cleavage pressure suggests incomplete digestion or protease mismatch.",
                severity=QcAssessmentSeverity.WARNING,
                supporting_metrics={
                    "missed_cleavage_rate": run_report.missed_cleavage_rate
                },
                suggested_action="inspect digestion conditions and enzyme configuration",
            )
        )
    if (
        run_report.mass_error.median_abs_ppm is not None
        and run_report.mass_error.median_abs_ppm >= 10.0
    ):
        findings.append(
            ContaminantArtifactFinding(
                code="mass-calibration-drift",
                summary="Precursor error is elevated enough to suggest calibration or alignment drift.",
                severity=QcAssessmentSeverity.FAILED
                if run_assessment.blocked
                else QcAssessmentSeverity.WARNING,
                supporting_metrics={
                    "median_abs_mass_error_ppm": run_report.mass_error.median_abs_ppm
                },
                suggested_action="inspect instrument calibration and precursor matching settings",
            )
        )
    if run_report.identification_rate < 0.2:
        findings.append(
            ContaminantArtifactFinding(
                code="low-identification-rate",
                summary="Low identification rate suggests acquisition or search-configuration mismatch.",
                severity=QcAssessmentSeverity.FAILED
                if run_assessment.blocked
                else QcAssessmentSeverity.WARNING,
                supporting_metrics={
                    "identification_rate": run_report.identification_rate
                },
                suggested_action="review search parameters, database choice, and acquisition quality",
            )
        )
    if not findings:
        findings.append(
            ContaminantArtifactFinding(
                code="no-major-artifact",
                summary="No dominant contaminant or acquisition artifact stands out from the QC surface.",
                severity=QcAssessmentSeverity.PASSED,
                supporting_metrics={},
                suggested_action="continue with biological interpretation",
            )
        )
    return ContaminantArtifactIntelligence(
        run_id=run_report.run_id,
        findings=tuple(findings),
        interpretation_summary=findings[0].summary,
    )


def recommend_experimental_contrasts(
    entries: tuple[ExperimentalDesignEntry, ...],
    *,
    min_replicates: int = 2,
) -> AnalyticalContrastRecommendationReport:
    """Recommend valid pairwise contrasts from an experimental design."""
    conditions = sorted({entry.condition for entry in entries})
    if len(conditions) < 2:
        rejected_contrast = AnalyticalContrastRecommendation(
            condition_a=conditions[0] if conditions else "condition-a",
            condition_b=conditions[0] if conditions else "condition-b",
            valid=False,
            replicate_counts=dict.fromkeys(conditions, 0),
            shared_batches=(),
            rejection_reasons=(AnalyticalContrastRejectionReason.SINGLE_CONDITION,),
            rationale="at least two conditions are required for a contrast",
        )
        return AnalyticalContrastRecommendationReport(
            condition_count=len(conditions),
            valid_contrasts=(),
            rejected_contrasts=(rejected_contrast,),
        )
    grouped: dict[str, list[ExperimentalDesignEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.condition].append(entry)
    valid: list[AnalyticalContrastRecommendation] = []
    rejected_contrasts: list[AnalyticalContrastRecommendation] = []
    for index, left in enumerate(conditions):
        for right in conditions[index + 1 :]:
            left_entries = grouped[left]
            right_entries = grouped[right]
            left_batches = {entry.batch for entry in left_entries if entry.batch}
            right_batches = {entry.batch for entry in right_entries if entry.batch}
            shared_batches = tuple(sorted(left_batches & right_batches))
            reasons: list[AnalyticalContrastRejectionReason] = []
            if (
                len(left_entries) < min_replicates
                or len(right_entries) < min_replicates
            ):
                reasons.append(
                    AnalyticalContrastRejectionReason.INSUFFICIENT_REPLICATES
                )
            if left_batches and right_batches and not shared_batches:
                reasons.append(AnalyticalContrastRejectionReason.BATCH_CONFOUNDED)
            recommendation = AnalyticalContrastRecommendation(
                condition_a=left,
                condition_b=right,
                valid=not reasons,
                replicate_counts={left: len(left_entries), right: len(right_entries)},
                shared_batches=shared_batches,
                rejection_reasons=tuple(reasons),
                rationale=(
                    "replicates and batch overlap support a valid contrast"
                    if not reasons
                    else ", ".join(reason.value for reason in reasons)
                ),
            )
            if recommendation.valid:
                valid.append(recommendation)
            else:
                rejected_contrasts.append(recommendation)
    return AnalyticalContrastRecommendationReport(
        condition_count=len(conditions),
        valid_contrasts=tuple(valid),
        rejected_contrasts=tuple(rejected_contrasts),
    )


def analyze_missingness_patterns(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> MissingnessPatternAnalysis:
    """Classify missingness patterns from a quantification matrix and design."""
    condition_lookup = {entry.sample_id: entry.condition for entry in design_entries}
    entity_values: dict[str, list[tuple[str, MissingValueKind, float | None]]] = (
        defaultdict(list)
    )
    observed_values: list[float] = []
    for value in table.values:
        entity_values[value.entity_id].append(
            (value.sample_id, value.missing_value_kind, value.abundance)
        )
        if value.abundance is not None:
            observed_values.append(value.abundance)
    abundance_median = (
        sorted(observed_values)[len(observed_values) // 2] if observed_values else 0.0
    )
    entries: list[MissingnessPatternEntry] = []
    label_counts: Counter[MissingnessPatternLabel] = Counter()
    for entity_id, values in sorted(entity_values.items()):
        observed_count = sum(
            1
            for _, kind, _ in values
            if kind in {MissingValueKind.OBSERVED, MissingValueKind.ZERO}
        )
        missing_count = len(values) - observed_count
        condition_missing_counts: Counter[str] = Counter()
        filtered_count = 0
        observed_abundances = [
            abundance
            for _, kind, abundance in values
            if kind is MissingValueKind.OBSERVED and abundance is not None
        ]
        for sample_id, kind, _ in values:
            if kind in {MissingValueKind.NOT_OBSERVED, MissingValueKind.FILTERED}:
                condition_missing_counts[
                    condition_lookup.get(sample_id, sample_id)
                ] += 1
            if kind is MissingValueKind.FILTERED:
                filtered_count += 1
        if missing_count == 0:
            label = MissingnessPatternLabel.MOSTLY_OBSERVED
            note = "entity is observed across all samples"
        elif filtered_count == missing_count and missing_count > 0:
            label = MissingnessPatternLabel.FILTER_DOMINATED
            note = "missingness is dominated by feature-level filtering"
        elif (
            len([count for count in condition_missing_counts.values() if count > 0])
            == 1
        ):
            label = MissingnessPatternLabel.CONDITION_LINKED
            note = "missingness is concentrated in one condition"
        elif observed_abundances and max(observed_abundances) <= abundance_median:
            label = MissingnessPatternLabel.MNAR_LIKE_LOW_SIGNAL
            note = "missingness follows low-abundance behavior and looks MNAR-like"
        elif missing_count > 0:
            label = MissingnessPatternLabel.MAR_LIKE
            note = "missingness is spread across conditions without a dominant low-signal pattern"
        else:
            label = MissingnessPatternLabel.MIXED
            note = "mixed missingness pattern"
        label_counts[label] += 1
        entries.append(
            MissingnessPatternEntry(
                entity_id=entity_id,
                label=label,
                observed_count=observed_count,
                missing_count=missing_count,
                condition_missing_counts=dict(condition_missing_counts),
                note=note,
            )
        )
    if not label_counts:
        overall = MissingnessPatternLabel.MIXED
    else:
        non_observed_counts = {
            label: count
            for label, count in label_counts.items()
            if label is not MissingnessPatternLabel.MOSTLY_OBSERVED
        }
        if not non_observed_counts:
            overall = MissingnessPatternLabel.MOSTLY_OBSERVED
        elif label_counts[MissingnessPatternLabel.MOSTLY_OBSERVED] > 0:
            overall = MissingnessPatternLabel.MIXED
        else:
            overall = max(
                non_observed_counts.items(),
                key=lambda item: (item[1], item[0].value),
            )[0]
    return MissingnessPatternAnalysis(
        entity_level=table.entity_level.value,
        overall_label=overall,
        entries=tuple(entries),
        interpretation_summary=f"{label_counts[overall]} entities primarily show {overall.value}.",
    )


def explain_outlier_samples(
    batch_report: InstrumentBatchQcReport,
    replicate_report: ReplicateCorrelationReport,
    *,
    low_correlation_threshold: float = 0.85,
) -> tuple[OutlierSampleExplanation, ...]:
    """Explain outlier samples from batch QC and replicate-correlation signals."""
    within_condition_correlations: dict[str, list[float]] = defaultdict(list)
    between_condition_correlations: dict[str, list[float]] = defaultdict(list)
    for entry in replicate_report.entries:
        target_map = (
            within_condition_correlations
            if entry.condition_a == entry.condition_b
            else between_condition_correlations
        )
        target_map[entry.sample_a].append(entry.correlation)
        target_map[entry.sample_b].append(entry.correlation)
    explanations: list[OutlierSampleExplanation] = []
    technical_reason_codes = {
        "low_identification_rate",
        "high_mass_error",
        "retention_time_shift",
        "low_replicate_correlation",
    }
    for run in batch_report.runs:
        reasons = list(run.outlier_reasons)
        supporting_metrics = {
            "spectrum_count": float(run.spectrum_count),
            "identification_rate": run.identification_rate,
        }
        if run.median_abs_mass_error_ppm is not None:
            supporting_metrics["median_abs_mass_error_ppm"] = (
                run.median_abs_mass_error_ppm
            )
        sample_id = run.sample_id or run.run_id
        within_condition = within_condition_correlations.get(sample_id, [])
        between_condition = between_condition_correlations.get(sample_id, [])
        if within_condition and min(within_condition) < low_correlation_threshold:
            reasons.append("low_replicate_correlation")
            supporting_metrics["min_replicate_correlation"] = min(within_condition)
        technical_reasons = {
            reason for reason in reasons if reason in technical_reason_codes
        }
        biological_reasons: set[str] = set()
        if (
            not technical_reasons
            and between_condition
            and min(between_condition) < low_correlation_threshold
            and run.run_id in batch_report.outlier_run_ids
            and run.identification_rate >= batch_report.median_identification_rate
            and (
                run.median_abs_mass_error_ppm is None
                or run.median_abs_mass_error_ppm <= batch_report.median_abs_mass_error_ppm
            )
        ):
            biological_reasons.add("condition_separation_without_qc_failure")
            supporting_metrics["min_between_condition_correlation"] = min(
                between_condition
            )
        if reasons:
            if technical_reasons and biological_reasons:
                classification = OutlierInterpretationClass.MIXED_SIGNAL
                follow_up = (
                    "repeat QC checks and verify whether the condition shift persists in orthogonal assays"
                )
            elif technical_reasons:
                classification = OutlierInterpretationClass.TECHNICAL_ANOMALY
                follow_up = (
                    "treat the sample as a technical anomaly until acquisition or preparation issues are resolved"
                )
            else:
                classification = (
                    OutlierInterpretationClass.PLAUSIBLE_BIOLOGICAL_EFFECT
                )
                follow_up = (
                    "preserve the sample for biological follow-up and confirm the shift with orthogonal evidence"
                )
            explanations.append(
                OutlierSampleExplanation(
                    sample_id=sample_id,
                    batch_id=run.batch,
                    classification=classification,
                    reasons=tuple(dict.fromkeys(reasons)),
                    technical_reasons=tuple(sorted(technical_reasons)),
                    biological_reasons=tuple(sorted(biological_reasons)),
                    supporting_metrics=supporting_metrics,
                    recommended_follow_up=follow_up,
                    interpretation_summary=(
                        f"{sample_id} is classified as {classification.value} because "
                        + ", ".join(dict.fromkeys(reasons or biological_reasons))
                    ),
                )
            )
        elif biological_reasons:
            explanations.append(
                OutlierSampleExplanation(
                    sample_id=sample_id,
                    batch_id=run.batch,
                    classification=OutlierInterpretationClass.PLAUSIBLE_BIOLOGICAL_EFFECT,
                    reasons=tuple(sorted(biological_reasons)),
                    technical_reasons=(),
                    biological_reasons=tuple(sorted(biological_reasons)),
                    supporting_metrics=supporting_metrics,
                    recommended_follow_up=(
                        "preserve the sample for biological follow-up and confirm the shift with orthogonal evidence"
                    ),
                    interpretation_summary=(
                        f"{sample_id} separates by condition without a matching QC failure."
                    ),
                )
            )
    return tuple(explanations)


def integrate_quant_qc_evidence(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    batch_report: InstrumentBatchQcReport,
    replicate_report: ReplicateCorrelationReport,
    *,
    run_assessments: tuple[QcRunAssessmentReport, ...] = (),
) -> QuantQcEvidenceIntegrationReport:
    """Integrate quant missingness and QC outlier evidence into one report."""
    missingness = analyze_missingness_patterns(table, design_entries)
    outliers = explain_outlier_samples(batch_report, replicate_report)
    blocked_run_ids = tuple(
        sorted(
            assessment.run_id for assessment in run_assessments if assessment.blocked
        )
    )
    notes: list[str] = []
    if outliers:
        technical_count = sum(
            1
            for outlier in outliers
            if outlier.classification is OutlierInterpretationClass.TECHNICAL_ANOMALY
        )
        biological_count = sum(
            1
            for outlier in outliers
            if outlier.classification
            is OutlierInterpretationClass.PLAUSIBLE_BIOLOGICAL_EFFECT
        )
        notes.append(f"{len(outliers)} samples show QC-supported outlier behavior")
        if technical_count:
            notes.append(f"{technical_count} outliers look technical")
        if biological_count:
            notes.append(f"{biological_count} outliers may reflect biology")
    if missingness.overall_label is not MissingnessPatternLabel.MOSTLY_OBSERVED:
        notes.append(
            f"missingness remains {missingness.overall_label.value} at the {table.entity_level.value} level"
        )
    if blocked_run_ids:
        notes.append("blocked QC runs: " + ", ".join(blocked_run_ids))
    if not notes:
        notes.append(
            "quant and QC evidence are jointly consistent for this analysis surface"
        )
    return QuantQcEvidenceIntegrationReport(
        entity_level=table.entity_level.value,
        missingness=missingness,
        outliers=outliers,
        blocked_run_ids=blocked_run_ids,
        notes=tuple(notes),
    )


def compute_ranked_enrichment(
    ranked_entities: tuple[RankedEntityScore, ...],
    annotations: tuple[ProteinAnnotationAssignment, ...],
) -> RankedEnrichmentReport:
    """Compute a simple GSEA-style running-sum enrichment over ranked entities."""
    ranked = tuple(ranked_entities)
    total_entities = len(ranked)
    entries: list[RankedEnrichmentEntry] = []
    for (term_id, category, term_name, source), proteins in _term_lookup(
        annotations
    ).items():
        hits = [entry for entry in ranked if entry.entity_id in proteins]
        if not hits:
            continue
        hit_ids = {entry.entity_id for entry in hits}
        hit_weight = sum(abs(entry.score) for entry in hits) or 1.0
        miss_penalty = 1.0 / max(total_entities - len(hits), 1)
        running = 0.0
        best_abs = 0.0
        best_score = 0.0
        leading_edge: list[str] = []
        current_edge: list[str] = []
        for entry in ranked:
            if entry.entity_id in hit_ids:
                increment = abs(entry.score) / hit_weight
                running += increment
                current_edge.append(entry.entity_id)
            else:
                running -= miss_penalty
            if abs(running) > best_abs:
                best_abs = abs(running)
                best_score = running
                leading_edge = list(current_edge)
        entries.append(
            RankedEnrichmentEntry(
                term_id=term_id,
                term_name=term_name,
                category=category,
                source=source,
                enrichment_score=best_score,
                direction=SignalDirection.UP
                if best_score >= 0
                else SignalDirection.DOWN,
                hit_count=len(hits),
                leading_edge=tuple(leading_edge),
            )
        )
    return RankedEnrichmentReport(
        entity_count=total_entities,
        entries=tuple(
            sorted(
                entries,
                key=lambda item: (
                    -abs(item.enrichment_score),
                    -item.hit_count,
                    _category_priority(item.category),
                    item.term_id,
                ),
            )
        ),
    )


def _annotation_terms_for_entity(
    entity_id: str,
    annotations: tuple[ProteinAnnotationAssignment, ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                annotation.term_name
                for annotation in annotations
                if annotation.protein_ref == entity_id
            }
        )
    )


def extract_contaminant_theme(
    batch_report: BatchEffectAdvisoryReport,
) -> str | None:
    """Return the dominant batch shift as one compact theme if present."""
    flagged = [entry for entry in batch_report.batches if entry.flagged]
    if not flagged:
        return None
    largest = max(flagged, key=lambda entry: abs(entry.shift_from_global))
    return f"{largest.batch_id} shows the strongest batch-level intensity shift"
