# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Cross-species protein effect comparison over explicit ortholog relationships."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path
import re

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.ortholog_mapping import (
    OrthologMappingCardinality,
    OrthologRecord,
)
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics.workflow.cross_study_effect_comparison import (
    CrossStudyEffectDirection,
    CrossStudyProteinEffectObservation,
    CrossStudyProteinStudyInput,
    extract_cross_study_protein_effect_observations,
)
from bijux_proteomics.workflow.study_result import ProteomicsStudyKind
from bijux_proteomics_foundation import JsonModel


class CrossSpeciesOrthologAmbiguityStatus(StrEnum):
    """Stable ortholog ambiguity classes on one cross-species effect comparison row."""

    UNIQUE_ORTHOLOG = "unique_ortholog"
    ONE_TO_MANY_ORTHOLOG = "one_to_many_ortholog"
    MANY_TO_ONE_ORTHOLOG = "many_to_one_ortholog"
    MANY_TO_MANY_ORTHOLOG = "many_to_many_ortholog"
    NO_ORTHOLOG_EVIDENCE = "no_ortholog_evidence"


class CrossSpeciesEffectEvidenceStatus(StrEnum):
    """Stable evidence outcomes over one source-target ortholog comparison row."""

    CONSERVED_EFFECT = "conserved_effect"
    DIVERGENT_EFFECT = "divergent_effect"
    SOURCE_ONLY_EFFECT = "source_only_effect"
    TARGET_ONLY_EFFECT = "target_only_effect"
    HETEROGENEOUS_CONTRASTS = "heterogeneous_contrasts"
    TARGET_ORTHOLOG_NOT_OBSERVED = "target_ortholog_not_observed"
    NO_ORTHOLOG_RELATIONSHIP = "no_ortholog_relationship"
    INSUFFICIENT_SUPPORT = "insufficient_support"


class CrossSpeciesEffectContrastAlignmentStatus(StrEnum):
    """Whether source and target contrasts aligned onto one direction surface."""

    SAME_ORDERED_CONTRAST = "same_ordered_contrast"
    REVERSED_ORDER_NORMALIZED = "reversed_order_normalized"
    HETEROGENEOUS_CONTRASTS = "heterogeneous_contrasts"
    NOT_APPLICABLE = "not_applicable"


class CrossSpeciesEffectUnsupportedStudy(JsonModel):
    """One study result that could not participate in cross-species comparison."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    study_label: str | None = None
    study_kind: ProteomicsStudyKind
    reason: str = Field(..., min_length=1)


class CrossSpeciesEffectComparisonEntry(JsonModel):
    """One source-anchored cross-species effect comparison row."""

    model_config = ConfigDict(extra="forbid")

    comparison_id: str = Field(..., min_length=1)
    source_study_id: str = Field(..., min_length=1)
    source_study_label: str | None = None
    source_study_kind: ProteomicsStudyKind
    source_species: str = Field(..., min_length=1)
    source_observation_id: str = Field(..., min_length=1)
    source_source_kind: str = Field(..., min_length=1)
    source_surface: str = Field(..., min_length=1)
    source_entity_id: str = Field(..., min_length=1)
    source_protein_ref: str = Field(..., min_length=1)
    source_gene_symbol: str | None = None
    source_condition_a: str = Field(..., min_length=1)
    source_condition_b: str = Field(..., min_length=1)
    source_log2_fold_change: float
    source_direction: CrossStudyEffectDirection
    source_significant: bool = False
    target_species: str | None = None
    target_study_id: str | None = None
    target_study_label: str | None = None
    target_study_kind: ProteomicsStudyKind | None = None
    target_observation_id: str | None = None
    target_source_kind: str | None = None
    target_surface: str | None = None
    target_entity_id: str | None = None
    target_protein_ref: str | None = None
    target_gene_symbol: str | None = None
    target_condition_a: str | None = None
    target_condition_b: str | None = None
    target_log2_fold_change: float | None = None
    target_direction: CrossStudyEffectDirection | None = None
    target_significant: bool | None = None
    normalized_target_log2_fold_change: float | None = None
    normalized_target_direction: CrossStudyEffectDirection | None = None
    contrast_alignment_status: CrossSpeciesEffectContrastAlignmentStatus
    ortholog_source_protein_ref: str | None = None
    ortholog_target_protein_ref: str | None = None
    ortholog_evidence: str | None = None
    mapping_cardinality: OrthologMappingCardinality | None = None
    ambiguity_status: CrossSpeciesOrthologAmbiguityStatus
    ambiguous_mapping: bool = False
    evidence_status: CrossSpeciesEffectEvidenceStatus
    note: str = Field(..., min_length=1)


class CrossSpeciesEffectComparisonSummary(JsonModel):
    """Summary over one cross-species effect comparison pass."""

    model_config = ConfigDict(extra="forbid")

    input_study_count: int = Field(..., ge=0)
    supported_study_count: int = Field(..., ge=0)
    unsupported_study_count: int = Field(..., ge=0)
    effect_observation_count: int = Field(..., ge=0)
    comparison_count: int = Field(..., ge=0)
    conserved_effect_count: int = Field(..., ge=0)
    divergent_effect_count: int = Field(..., ge=0)
    source_only_effect_count: int = Field(..., ge=0)
    target_only_effect_count: int = Field(..., ge=0)
    heterogeneous_contrast_count: int = Field(..., ge=0)
    target_ortholog_not_observed_count: int = Field(..., ge=0)
    no_ortholog_relationship_count: int = Field(..., ge=0)
    insufficient_support_count: int = Field(..., ge=0)
    ambiguous_mapping_count: int = Field(..., ge=0)


class CrossSpeciesEffectComparisonReport(JsonModel):
    """Owned report over source-target ortholog effect comparison across species."""

    model_config = ConfigDict(extra="forbid")

    extracted_effects: tuple[CrossStudyProteinEffectObservation, ...] = Field(
        default_factory=tuple
    )
    unsupported_studies: tuple[CrossSpeciesEffectUnsupportedStudy, ...] = Field(
        default_factory=tuple
    )
    comparisons: tuple[CrossSpeciesEffectComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    summary: CrossSpeciesEffectComparisonSummary
    note: str = Field(..., min_length=1)


def build_cross_species_effect_comparison_report(
    studies: tuple[CrossStudyProteinStudyInput, ...],
    *,
    ortholog_records: tuple[OrthologRecord, ...],
    significance_threshold: float = 0.05,
) -> CrossSpeciesEffectComparisonReport:
    """Compare study protein effects across species through explicit ortholog mappings."""

    extraction = extract_cross_study_protein_effect_observations(
        studies,
        significance_threshold=significance_threshold,
    )
    unsupported = [
        CrossSpeciesEffectUnsupportedStudy(
            study_id=entry.study_id,
            study_label=entry.study_label,
            study_kind=entry.study_kind,
            reason=entry.reason,
        )
        for entry in extraction.unsupported_studies
    ]
    supported_effects: list[CrossStudyProteinEffectObservation] = []
    study_ids_with_supported_effects: set[str] = set()
    missing_species_studies: set[str] = set()
    for observation in extraction.observations:
        if _normalize_species(observation.species) is None:
            missing_species_studies.add(observation.study_id)
            continue
        supported_effects.append(observation)
        study_ids_with_supported_effects.add(observation.study_id)
    for study in studies:
        if study.study_id in missing_species_studies:
            unsupported.append(
                CrossSpeciesEffectUnsupportedStudy(
                    study_id=study.study_id,
                    study_label=study.study_label,
                    study_kind=study.study_result.study_kind,
                    reason=(
                        "species-aware comparison requires explicit study species or "
                        "owned observation species metadata"
                    ),
                )
            )
    return build_cross_species_effect_comparison_report_from_observations(
        tuple(supported_effects),
        ortholog_records=ortholog_records,
        unsupported_studies=tuple(_deduplicate_unsupported_studies(unsupported)),
        input_study_count=extraction.summary.input_study_count,
    )


def build_cross_species_effect_comparison_report_from_observations(
    observations: tuple[CrossStudyProteinEffectObservation, ...],
    *,
    ortholog_records: tuple[OrthologRecord, ...],
    unsupported_studies: tuple[CrossSpeciesEffectUnsupportedStudy, ...] = (),
    input_study_count: int | None = None,
) -> CrossSpeciesEffectComparisonReport:
    """Compare extracted study protein effects through explicit ortholog edges."""

    normalized_observations = tuple(
        observation
        for observation in observations
        if _normalize_species(observation.species) is not None
    )
    if not normalized_observations:
        return CrossSpeciesEffectComparisonReport(
            extracted_effects=(),
            unsupported_studies=unsupported_studies,
            comparisons=(),
            summary=CrossSpeciesEffectComparisonSummary(
                input_study_count=0 if input_study_count is None else input_study_count,
                supported_study_count=0,
                unsupported_study_count=len(unsupported_studies),
                effect_observation_count=0,
                comparison_count=0,
                conserved_effect_count=0,
                divergent_effect_count=0,
                source_only_effect_count=0,
                target_only_effect_count=0,
                heterogeneous_contrast_count=0,
                target_ortholog_not_observed_count=0,
                no_ortholog_relationship_count=0,
                insufficient_support_count=0,
                ambiguous_mapping_count=0,
            ),
            note=(
                "cross-species effect comparison did not receive any supported "
                "cross-species effect observations"
            ),
        )

    observed_species = tuple(
        sorted(
            {
                normalized
                for observation in normalized_observations
                if (normalized := _normalize_species(observation.species)) is not None
            }
        )
    )
    species_label_lookup = {
        normalized: observation.species or normalized
        for observation in normalized_observations
        if (normalized := _normalize_species(observation.species)) is not None
    }
    ortholog_index = _build_ortholog_index(ortholog_records)
    target_lookup = _build_target_observation_lookup(normalized_observations)

    comparisons: list[CrossSpeciesEffectComparisonEntry] = []
    for source_observation in sorted(
        normalized_observations,
        key=_observation_sort_key,
    ):
        source_species = _normalize_species(source_observation.species)
        if source_species is None:
            raise RuntimeError(
                "cross-species comparison requires normalized source species for every observation"
            )
        for target_species in observed_species:
            if target_species == source_species:
                continue
            ortholog_edges = _ortholog_edges_for_source(
                source_observation,
                target_species=target_species,
                ortholog_index=ortholog_index,
            )
            if not ortholog_edges:
                comparisons.append(
                    _build_no_ortholog_comparison_entry(
                        source_observation=source_observation,
                        target_species=species_label_lookup[target_species],
                    )
                )
                continue
            for edge in ortholog_edges:
                target_matches = _target_matches_for_edge(
                    edge=edge,
                    target_lookup=target_lookup,
                )
                if not target_matches:
                    comparisons.append(
                        _build_unobserved_target_comparison_entry(
                            source_observation=source_observation,
                            edge=edge,
                        )
                    )
                    continue
                for target_observation in target_matches:
                    comparisons.append(
                        _build_matched_comparison_entry(
                            source_observation=source_observation,
                            target_observation=target_observation,
                            edge=edge,
                        )
                    )

    summary = CrossSpeciesEffectComparisonSummary(
        input_study_count=(
            len({entry.study_id for entry in normalized_observations})
            + len(unsupported_studies)
            if input_study_count is None
            else input_study_count
        ),
        supported_study_count=len({entry.study_id for entry in normalized_observations}),
        unsupported_study_count=len(unsupported_studies),
        effect_observation_count=len(normalized_observations),
        comparison_count=len(comparisons),
        conserved_effect_count=sum(
            entry.evidence_status is CrossSpeciesEffectEvidenceStatus.CONSERVED_EFFECT
            for entry in comparisons
        ),
        divergent_effect_count=sum(
            entry.evidence_status is CrossSpeciesEffectEvidenceStatus.DIVERGENT_EFFECT
            for entry in comparisons
        ),
        source_only_effect_count=sum(
            entry.evidence_status is CrossSpeciesEffectEvidenceStatus.SOURCE_ONLY_EFFECT
            for entry in comparisons
        ),
        target_only_effect_count=sum(
            entry.evidence_status is CrossSpeciesEffectEvidenceStatus.TARGET_ONLY_EFFECT
            for entry in comparisons
        ),
        heterogeneous_contrast_count=sum(
            entry.evidence_status
            is CrossSpeciesEffectEvidenceStatus.HETEROGENEOUS_CONTRASTS
            for entry in comparisons
        ),
        target_ortholog_not_observed_count=sum(
            entry.evidence_status
            is CrossSpeciesEffectEvidenceStatus.TARGET_ORTHOLOG_NOT_OBSERVED
            for entry in comparisons
        ),
        no_ortholog_relationship_count=sum(
            entry.evidence_status
            is CrossSpeciesEffectEvidenceStatus.NO_ORTHOLOG_RELATIONSHIP
            for entry in comparisons
        ),
        insufficient_support_count=sum(
            entry.evidence_status is CrossSpeciesEffectEvidenceStatus.INSUFFICIENT_SUPPORT
            for entry in comparisons
        ),
        ambiguous_mapping_count=sum(entry.ambiguous_mapping for entry in comparisons),
    )
    return CrossSpeciesEffectComparisonReport(
        extracted_effects=normalized_observations,
        unsupported_studies=unsupported_studies,
        comparisons=tuple(comparisons),
        summary=summary,
        note=(
            "cross-species effect comparison links study effects only through explicit "
            "ortholog records, preserves one-to-many and many-to-many ambiguity on "
            "separate rows, and never substitutes gene-symbol overlap for orthology"
        ),
    )


def render_cross_species_effect_comparison_tsv(
    report: CrossSpeciesEffectComparisonReport,
) -> str:
    """Render cross-species effect comparisons as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "comparison_id",
            "source_study_id",
            "source_study_label",
            "source_study_kind",
            "source_species",
            "source_observation_id",
            "source_source_kind",
            "source_surface",
            "source_entity_id",
            "source_protein_ref",
            "source_gene_symbol",
            "source_condition_a",
            "source_condition_b",
            "source_log2_fold_change",
            "source_direction",
            "source_significant",
            "target_species",
            "target_study_id",
            "target_study_label",
            "target_study_kind",
            "target_observation_id",
            "target_source_kind",
            "target_surface",
            "target_entity_id",
            "target_protein_ref",
            "target_gene_symbol",
            "target_condition_a",
            "target_condition_b",
            "target_log2_fold_change",
            "target_direction",
            "target_significant",
            "normalized_target_log2_fold_change",
            "normalized_target_direction",
            "contrast_alignment_status",
            "ortholog_source_protein_ref",
            "ortholog_target_protein_ref",
            "ortholog_evidence",
            "mapping_cardinality",
            "ambiguity_status",
            "ambiguous_mapping",
            "evidence_status",
            "note",
        ]
    )
    for entry in report.comparisons:
        writer.writerow(
            [
                entry.comparison_id,
                entry.source_study_id,
                entry.source_study_label or "",
                entry.source_study_kind.value,
                entry.source_species,
                entry.source_observation_id,
                entry.source_source_kind,
                entry.source_surface,
                entry.source_entity_id,
                entry.source_protein_ref,
                entry.source_gene_symbol or "",
                entry.source_condition_a,
                entry.source_condition_b,
                f"{entry.source_log2_fold_change:.6f}",
                entry.source_direction.value,
                str(entry.source_significant).lower(),
                entry.target_species or "",
                entry.target_study_id or "",
                entry.target_study_label or "",
                "" if entry.target_study_kind is None else entry.target_study_kind.value,
                entry.target_observation_id or "",
                entry.target_source_kind or "",
                entry.target_surface or "",
                entry.target_entity_id or "",
                entry.target_protein_ref or "",
                entry.target_gene_symbol or "",
                entry.target_condition_a or "",
                entry.target_condition_b or "",
                _format_float(entry.target_log2_fold_change),
                "" if entry.target_direction is None else entry.target_direction.value,
                ""
                if entry.target_significant is None
                else str(entry.target_significant).lower(),
                _format_float(entry.normalized_target_log2_fold_change),
                ""
                if entry.normalized_target_direction is None
                else entry.normalized_target_direction.value,
                entry.contrast_alignment_status.value,
                entry.ortholog_source_protein_ref or "",
                entry.ortholog_target_protein_ref or "",
                entry.ortholog_evidence or "",
                "" if entry.mapping_cardinality is None else entry.mapping_cardinality.value,
                entry.ambiguity_status.value,
                str(entry.ambiguous_mapping).lower(),
                entry.evidence_status.value,
                entry.note,
            ]
        )
    return buffer.getvalue()


def export_cross_species_effect_comparison_tsv(
    report: CrossSpeciesEffectComparisonReport,
    path: Path,
) -> None:
    """Write cross-species effect comparisons to TSV."""

    write_output_table_tsv(path, render_cross_species_effect_comparison_tsv(report))


class _OrthologEdge(JsonModel):
    model_config = ConfigDict(extra="forbid")

    source_species: str = Field(..., min_length=1)
    target_species: str = Field(..., min_length=1)
    source_protein_ref: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    evidence: str | None = None
    mapping_cardinality: OrthologMappingCardinality


def _build_ortholog_index(
    ortholog_records: tuple[OrthologRecord, ...],
) -> dict[tuple[str, str, str], tuple[_OrthologEdge, ...]]:
    filtered_records = tuple(
        record
        for record in ortholog_records
        if _normalize_species(record.source_species) is not None
        and _normalize_species(record.target_species) is not None
    )
    source_counts: dict[tuple[str, str, str], set[str]] = {}
    target_counts: dict[tuple[str, str, str], set[str]] = {}
    for record in filtered_records:
        source_species = _normalize_species(record.source_species)
        target_species = _normalize_species(record.target_species)
        if source_species is None or target_species is None:
            raise RuntimeError(
                "ortholog indexing requires normalized source and target species labels"
            )
        source_ref = canonicalize_protein_reference(record.source_protein_ref)
        target_ref = canonicalize_protein_reference(record.target_protein_ref)
        source_counts.setdefault((source_species, source_ref, target_species), set()).add(
            target_ref
        )
        target_counts.setdefault((target_species, target_ref, source_species), set()).add(
            source_ref
        )

    edges_by_key: dict[tuple[str, str, str], list[_OrthologEdge]] = {}
    seen_edges: set[tuple[str, str, str, str]] = set()
    for record in filtered_records:
        source_species = _normalize_species(record.source_species)
        target_species = _normalize_species(record.target_species)
        if source_species is None or target_species is None:
            raise RuntimeError(
                "ortholog edge construction requires normalized source and target species labels"
            )
        source_ref = canonicalize_protein_reference(record.source_protein_ref)
        target_ref = canonicalize_protein_reference(record.target_protein_ref)
        edge_key = (source_species, source_ref, target_species, target_ref)
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)
        mapping_cardinality = _classify_mapping_cardinality(
            source_match_count=len(source_counts[(source_species, source_ref, target_species)]),
            target_match_count=len(target_counts[(target_species, target_ref, source_species)]),
        )
        edge = _OrthologEdge(
            source_species=source_species,
            target_species=target_species,
            source_protein_ref=source_ref,
            target_protein_ref=target_ref,
            evidence=record.evidence,
            mapping_cardinality=mapping_cardinality,
        )
        edges_by_key.setdefault((source_species, source_ref, target_species), []).append(edge)

    return {
        key: tuple(sorted(value, key=lambda entry: entry.target_protein_ref))
        for key, value in edges_by_key.items()
    }


def _build_target_observation_lookup(
    observations: tuple[CrossStudyProteinEffectObservation, ...],
) -> dict[tuple[str, str], tuple[CrossStudyProteinEffectObservation, ...]]:
    grouped: dict[tuple[str, str], list[CrossStudyProteinEffectObservation]] = {}
    for observation in observations:
        species = _normalize_species(observation.species)
        if species is None:
            raise RuntimeError(
                "cross-species target lookup requires normalized species labels"
            )
        for token in _identity_tokens(observation):
            grouped.setdefault((species, token), []).append(observation)
    return {
        key: tuple(sorted(value, key=_observation_sort_key))
        for key, value in grouped.items()
    }


def _ortholog_edges_for_source(
    source_observation: CrossStudyProteinEffectObservation,
    *,
    target_species: str,
    ortholog_index: dict[tuple[str, str, str], tuple[_OrthologEdge, ...]],
) -> tuple[_OrthologEdge, ...]:
    source_species = _normalize_species(source_observation.species)
    if source_species is None:
        raise RuntimeError(
            "ortholog edge lookup requires a normalized source species label"
        )
    matched_edges: dict[tuple[str, str, str, str], _OrthologEdge] = {}
    for token in _identity_tokens(source_observation):
        for edge in ortholog_index.get((source_species, token, target_species), ()):
            matched_edges[
                (
                    edge.source_species,
                    edge.source_protein_ref,
                    edge.target_species,
                    edge.target_protein_ref,
                )
            ] = edge
    return tuple(sorted(matched_edges.values(), key=lambda entry: entry.target_protein_ref))


def _target_matches_for_edge(
    *,
    edge: _OrthologEdge,
    target_lookup: dict[tuple[str, str], tuple[CrossStudyProteinEffectObservation, ...]],
) -> tuple[CrossStudyProteinEffectObservation, ...]:
    return target_lookup.get((edge.target_species, edge.target_protein_ref), ())


def _build_no_ortholog_comparison_entry(
    *,
    source_observation: CrossStudyProteinEffectObservation,
    target_species: str,
) -> CrossSpeciesEffectComparisonEntry:
    return CrossSpeciesEffectComparisonEntry(
        comparison_id=_comparison_id(
            source_observation=source_observation,
            target_species=target_species,
            target_protein_ref="no_ortholog",
            target_observation_id=None,
        ),
        source_study_id=source_observation.study_id,
        source_study_label=source_observation.study_label,
        source_study_kind=source_observation.study_kind,
        source_species=source_observation.species or "",
        source_observation_id=source_observation.observation_id,
        source_source_kind=source_observation.source_kind.value,
        source_surface=source_observation.source_surface,
        source_entity_id=source_observation.source_entity_id,
        source_protein_ref=source_observation.representative_protein_ref,
        source_gene_symbol=source_observation.gene_symbol,
        source_condition_a=source_observation.condition_a,
        source_condition_b=source_observation.condition_b,
        source_log2_fold_change=source_observation.log2_fold_change,
        source_direction=source_observation.direction,
        source_significant=source_observation.significant,
        target_species=target_species,
        contrast_alignment_status=CrossSpeciesEffectContrastAlignmentStatus.NOT_APPLICABLE,
        ambiguity_status=CrossSpeciesOrthologAmbiguityStatus.NO_ORTHOLOG_EVIDENCE,
        ambiguous_mapping=False,
        evidence_status=CrossSpeciesEffectEvidenceStatus.NO_ORTHOLOG_RELATIONSHIP,
        note=(
            "no explicit ortholog relationship linked this source protein effect to the "
            f"observed target species {target_species}"
        ),
    )


def _build_unobserved_target_comparison_entry(
    *,
    source_observation: CrossStudyProteinEffectObservation,
    edge: _OrthologEdge,
) -> CrossSpeciesEffectComparisonEntry:
    ambiguity_status, ambiguous_mapping = _ambiguity_from_cardinality(edge.mapping_cardinality)
    return CrossSpeciesEffectComparisonEntry(
        comparison_id=_comparison_id(
            source_observation=source_observation,
            target_species=edge.target_species,
            target_protein_ref=edge.target_protein_ref,
            target_observation_id=None,
        ),
        source_study_id=source_observation.study_id,
        source_study_label=source_observation.study_label,
        source_study_kind=source_observation.study_kind,
        source_species=source_observation.species or "",
        source_observation_id=source_observation.observation_id,
        source_source_kind=source_observation.source_kind.value,
        source_surface=source_observation.source_surface,
        source_entity_id=source_observation.source_entity_id,
        source_protein_ref=source_observation.representative_protein_ref,
        source_gene_symbol=source_observation.gene_symbol,
        source_condition_a=source_observation.condition_a,
        source_condition_b=source_observation.condition_b,
        source_log2_fold_change=source_observation.log2_fold_change,
        source_direction=source_observation.direction,
        source_significant=source_observation.significant,
        target_species=edge.target_species,
        contrast_alignment_status=CrossSpeciesEffectContrastAlignmentStatus.NOT_APPLICABLE,
        ortholog_source_protein_ref=edge.source_protein_ref,
        ortholog_target_protein_ref=edge.target_protein_ref,
        target_protein_ref=edge.target_protein_ref,
        ortholog_evidence=edge.evidence,
        mapping_cardinality=edge.mapping_cardinality,
        ambiguity_status=ambiguity_status,
        ambiguous_mapping=ambiguous_mapping,
        evidence_status=CrossSpeciesEffectEvidenceStatus.TARGET_ORTHOLOG_NOT_OBSERVED,
        note=(
            "an explicit ortholog relationship exists, but the target ortholog was not "
            "observed on a governed study effect surface"
        ),
    )


def _build_matched_comparison_entry(
    *,
    source_observation: CrossStudyProteinEffectObservation,
    target_observation: CrossStudyProteinEffectObservation,
    edge: _OrthologEdge,
) -> CrossSpeciesEffectComparisonEntry:
    normalized_target_direction, normalized_target_log2_fold_change, alignment_status = (
        _normalize_target_effect_against_source(
            source_observation=source_observation,
            target_observation=target_observation,
        )
    )
    evidence_status, note = _evidence_status_for_pair(
        source_observation=source_observation,
        target_observation=target_observation,
        normalized_target_direction=normalized_target_direction,
        alignment_status=alignment_status,
    )
    ambiguity_status, ambiguous_mapping = _ambiguity_from_cardinality(edge.mapping_cardinality)
    return CrossSpeciesEffectComparisonEntry(
        comparison_id=_comparison_id(
            source_observation=source_observation,
            target_species=edge.target_species,
            target_protein_ref=edge.target_protein_ref,
            target_observation_id=target_observation.observation_id,
        ),
        source_study_id=source_observation.study_id,
        source_study_label=source_observation.study_label,
        source_study_kind=source_observation.study_kind,
        source_species=source_observation.species or "",
        source_observation_id=source_observation.observation_id,
        source_source_kind=source_observation.source_kind.value,
        source_surface=source_observation.source_surface,
        source_entity_id=source_observation.source_entity_id,
        source_protein_ref=source_observation.representative_protein_ref,
        source_gene_symbol=source_observation.gene_symbol,
        source_condition_a=source_observation.condition_a,
        source_condition_b=source_observation.condition_b,
        source_log2_fold_change=source_observation.log2_fold_change,
        source_direction=source_observation.direction,
        source_significant=source_observation.significant,
        target_species=target_observation.species,
        target_study_id=target_observation.study_id,
        target_study_label=target_observation.study_label,
        target_study_kind=target_observation.study_kind,
        target_observation_id=target_observation.observation_id,
        target_source_kind=target_observation.source_kind.value,
        target_surface=target_observation.source_surface,
        target_entity_id=target_observation.source_entity_id,
        target_protein_ref=target_observation.representative_protein_ref,
        target_gene_symbol=target_observation.gene_symbol,
        target_condition_a=target_observation.condition_a,
        target_condition_b=target_observation.condition_b,
        target_log2_fold_change=target_observation.log2_fold_change,
        target_direction=target_observation.direction,
        target_significant=target_observation.significant,
        normalized_target_log2_fold_change=normalized_target_log2_fold_change,
        normalized_target_direction=normalized_target_direction,
        contrast_alignment_status=alignment_status,
        ortholog_source_protein_ref=edge.source_protein_ref,
        ortholog_target_protein_ref=edge.target_protein_ref,
        ortholog_evidence=edge.evidence,
        mapping_cardinality=edge.mapping_cardinality,
        ambiguity_status=ambiguity_status,
        ambiguous_mapping=ambiguous_mapping,
        evidence_status=evidence_status,
        note=note,
    )


def _normalize_target_effect_against_source(
    *,
    source_observation: CrossStudyProteinEffectObservation,
    target_observation: CrossStudyProteinEffectObservation,
) -> tuple[
    CrossStudyEffectDirection | None,
    float | None,
    CrossSpeciesEffectContrastAlignmentStatus,
]:
    if (
        source_observation.condition_a == target_observation.condition_a
        and source_observation.condition_b == target_observation.condition_b
    ):
        return (
            target_observation.direction,
            target_observation.log2_fold_change,
            CrossSpeciesEffectContrastAlignmentStatus.SAME_ORDERED_CONTRAST,
        )
    if (
        source_observation.condition_a == target_observation.condition_b
        and source_observation.condition_b == target_observation.condition_a
    ):
        normalized_log2_fold_change = -target_observation.log2_fold_change
        return (
            _direction_from_fold_change(normalized_log2_fold_change),
            normalized_log2_fold_change,
            CrossSpeciesEffectContrastAlignmentStatus.REVERSED_ORDER_NORMALIZED,
        )
    return (
        None,
        None,
        CrossSpeciesEffectContrastAlignmentStatus.HETEROGENEOUS_CONTRASTS,
    )


def _evidence_status_for_pair(
    *,
    source_observation: CrossStudyProteinEffectObservation,
    target_observation: CrossStudyProteinEffectObservation,
    normalized_target_direction: CrossStudyEffectDirection | None,
    alignment_status: CrossSpeciesEffectContrastAlignmentStatus,
) -> tuple[CrossSpeciesEffectEvidenceStatus, str]:
    if (
        alignment_status
        is CrossSpeciesEffectContrastAlignmentStatus.HETEROGENEOUS_CONTRASTS
    ):
        return (
            CrossSpeciesEffectEvidenceStatus.HETEROGENEOUS_CONTRASTS,
            "source and target effects were measured on different condition contrasts",
        )
    if source_observation.significant and target_observation.significant:
        if normalized_target_direction == source_observation.direction:
            return (
                CrossSpeciesEffectEvidenceStatus.CONSERVED_EFFECT,
                "source and target ortholog effects supported the same direction after contrast normalization",
            )
        return (
            CrossSpeciesEffectEvidenceStatus.DIVERGENT_EFFECT,
            "source and target ortholog effects supported opposite directions after contrast normalization",
        )
    if source_observation.significant and not target_observation.significant:
        return (
            CrossSpeciesEffectEvidenceStatus.SOURCE_ONLY_EFFECT,
            "the source protein effect was significant while the observed target ortholog effect was not",
        )
    if (not source_observation.significant) and target_observation.significant:
        return (
            CrossSpeciesEffectEvidenceStatus.TARGET_ONLY_EFFECT,
            "the observed target ortholog effect was significant while the source protein effect was not",
        )
    return (
        CrossSpeciesEffectEvidenceStatus.INSUFFICIENT_SUPPORT,
        "neither source nor target ortholog effect reached the configured significance surface",
    )


def _ambiguity_from_cardinality(
    mapping_cardinality: OrthologMappingCardinality,
) -> tuple[CrossSpeciesOrthologAmbiguityStatus, bool]:
    if mapping_cardinality is OrthologMappingCardinality.ONE_TO_ONE:
        return CrossSpeciesOrthologAmbiguityStatus.UNIQUE_ORTHOLOG, False
    if mapping_cardinality is OrthologMappingCardinality.ONE_TO_MANY:
        return CrossSpeciesOrthologAmbiguityStatus.ONE_TO_MANY_ORTHOLOG, True
    if mapping_cardinality is OrthologMappingCardinality.MANY_TO_ONE:
        return CrossSpeciesOrthologAmbiguityStatus.MANY_TO_ONE_ORTHOLOG, True
    return CrossSpeciesOrthologAmbiguityStatus.MANY_TO_MANY_ORTHOLOG, True


def _classify_mapping_cardinality(
    *,
    source_match_count: int,
    target_match_count: int,
) -> OrthologMappingCardinality:
    if source_match_count == 1 and target_match_count == 1:
        return OrthologMappingCardinality.ONE_TO_ONE
    if source_match_count > 1 and target_match_count > 1:
        return OrthologMappingCardinality.MANY_TO_MANY
    if source_match_count > 1:
        return OrthologMappingCardinality.ONE_TO_MANY
    return OrthologMappingCardinality.MANY_TO_ONE


def _comparison_id(
    *,
    source_observation: CrossStudyProteinEffectObservation,
    target_species: str | None,
    target_protein_ref: str | None,
    target_observation_id: str | None,
) -> str:
    return (
        f"cross_species_effect_{_stable_token(source_observation.study_id)}_"
        f"{_stable_token(source_observation.representative_protein_ref)}_"
        f"{_stable_token(target_species or 'unspecified_species')}_"
        f"{_stable_token(target_protein_ref or 'no_target_ortholog')}_"
        f"{_stable_token(target_observation_id or 'no_target_observation')}"
    )


def _identity_tokens(
    observation: CrossStudyProteinEffectObservation,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                canonicalize_protein_reference(token)
                for token in (
                    observation.representative_protein_ref,
                    *observation.protein_refs,
                    *observation.accession_aliases,
                )
                if token
            }
        )
    )


def _normalize_species(species: str | None) -> str | None:
    if species is None:
        return None
    normalized = re.sub(r"\s+", " ", species.strip()).lower()
    return normalized or None


def _direction_from_fold_change(log2_fold_change: float) -> CrossStudyEffectDirection:
    if log2_fold_change > 0:
        return CrossStudyEffectDirection.UP
    if log2_fold_change < 0:
        return CrossStudyEffectDirection.DOWN
    return CrossStudyEffectDirection.FLAT


def _observation_sort_key(observation: CrossStudyProteinEffectObservation) -> tuple[str, str]:
    return (observation.study_id, observation.observation_id)


def _stable_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return token or "unspecified"


def _format_float(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


def _deduplicate_unsupported_studies(
    entries: list[CrossSpeciesEffectUnsupportedStudy],
) -> tuple[CrossSpeciesEffectUnsupportedStudy, ...]:
    deduplicated: dict[str, CrossSpeciesEffectUnsupportedStudy] = {}
    for entry in entries:
        deduplicated.setdefault(entry.study_id, entry)
    return tuple(
        deduplicated[key] for key in sorted(deduplicated)
    )


__all__ = [
    "CrossSpeciesEffectComparisonEntry",
    "CrossSpeciesEffectComparisonReport",
    "CrossSpeciesEffectComparisonSummary",
    "CrossSpeciesEffectEvidenceStatus",
    "CrossSpeciesEffectUnsupportedStudy",
    "CrossSpeciesOrthologAmbiguityStatus",
    "build_cross_species_effect_comparison_report",
    "build_cross_species_effect_comparison_report_from_observations",
    "export_cross_species_effect_comparison_tsv",
    "render_cross_species_effect_comparison_tsv",
]
