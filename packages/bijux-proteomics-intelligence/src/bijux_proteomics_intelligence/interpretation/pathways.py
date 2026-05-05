# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Pathway, enrichment, and differential interpretation owners."""

from __future__ import annotations

from collections import defaultdict
from enum import StrEnum
import math

from pydantic import ConfigDict, Field

from bijux_proteomics.quantification import (
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
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

class ProteinAnnotationAssignment(JsonModel):
    """One protein-to-term annotation with source provenance."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    term_id: str = Field(..., min_length=1)
    term_name: str = Field(..., min_length=1)
    category: AnnotationCategory
    source: str = Field(..., min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

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
        safe_summary = "Pathway-level claims remain blocked; only constrained thematic summaries are safe."
    elif cautions:
        safe_summary = "Pathway summaries are usable only with the listed caution notes kept visible."
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
