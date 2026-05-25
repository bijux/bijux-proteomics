# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned cross-contrast consistency review over multi-condition differential results."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path
from statistics import median

from pydantic import ConfigDict, Field

from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    ImputationMethod,
    MultiConditionDifferentialAbundanceReport,
    NormalizationMethod,
    QuantEntityLevel,
)
from bijux_proteomics_foundation import JsonModel


class MultiContrastMagnitudeConsistencyStatus(StrEnum):
    """Stable magnitude-consistency states over significant contrasts."""

    CONSISTENT = "consistent"
    VARIABLE = "variable"
    INSUFFICIENT_SIGNIFICANT_SUPPORT = "insufficient_significant_support"


class MultiContrastConsistencyComparisonEntry(JsonModel):
    """One entity-level contrast comparison preserved inside the consistency report."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    contrast_label: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    higher_condition: str | None = None
    lower_condition: str | None = None
    log2_fold_change: float
    absolute_log2_fold_change: float = Field(..., ge=0.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    significant: bool = False


class MultiContrastConsistencyEntityEntry(JsonModel):
    """One entity-level consistency summary across a multi-condition contrast set."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    tested_contrast_count: int = Field(..., ge=0)
    significant_contrast_count: int = Field(..., ge=0)
    significant_contrast_labels: tuple[str, ...] = Field(default_factory=tuple)
    contrast_specific_contrast_labels: tuple[str, ...] = Field(default_factory=tuple)
    direction_relations: tuple[str, ...] = Field(default_factory=tuple)
    shared_hit: bool = False
    contrast_specific_hit: bool = False
    direction_conflict: bool = False
    magnitude_consistency_status: MultiContrastMagnitudeConsistencyStatus
    magnitude_consistency_score: float | None = Field(default=None, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float | None = Field(default=None, ge=0.0)
    median_absolute_log2_fold_change: float | None = Field(default=None, ge=0.0)
    max_absolute_log2_fold_change: float | None = Field(default=None, ge=0.0)
    note: str = Field(..., min_length=1)


class MultiContrastConsistencySummary(JsonModel):
    """Compact study-level summary over cross-contrast consistency outcomes."""

    model_config = ConfigDict(extra="forbid")

    entity_count: int = Field(..., ge=0)
    shared_hit_count: int = Field(..., ge=0)
    contrast_specific_hit_count: int = Field(..., ge=0)
    direction_conflict_count: int = Field(..., ge=0)
    magnitude_consistent_count: int = Field(..., ge=0)
    magnitude_variable_count: int = Field(..., ge=0)


class MultiContrastConsistencyReport(JsonModel):
    """Cross-contrast consistency review over a multi-condition DA collection."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    normalization_method: NormalizationMethod
    imputation_method: ImputationMethod = ImputationMethod.NONE
    contrast_count: int = Field(..., ge=1)
    significance_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    comparisons: tuple[MultiContrastConsistencyComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    entities: tuple[MultiContrastConsistencyEntityEntry, ...] = Field(
        default_factory=tuple
    )
    summary: MultiContrastConsistencySummary
    note: str = Field(..., min_length=1)


def build_multi_contrast_consistency_report(
    report: MultiConditionDifferentialAbundanceReport,
    *,
    entity_protein_refs: dict[str, tuple[str, ...]] | None = None,
    significance_threshold: float = 0.05,
    magnitude_consistency_floor: float = 0.67,
) -> MultiContrastConsistencyReport:
    """Compare one entity across all preserved pairwise contrasts."""

    comparison_entries: list[MultiContrastConsistencyComparisonEntry] = []
    comparisons_by_entity: dict[str, list[MultiContrastConsistencyComparisonEntry]] = {}
    for contrast_report in report.reports:
        for entry in contrast_report.entries:
            comparison_entry = _build_comparison_entry(
                contrast_report,
                entry=entry,
                protein_refs=(
                    ()
                    if entity_protein_refs is None
                    else entity_protein_refs.get(entry.entity_id, ())
                ),
                significance_threshold=significance_threshold,
            )
            comparison_entries.append(comparison_entry)
            comparisons_by_entity.setdefault(entry.entity_id, []).append(comparison_entry)

    entity_entries = tuple(
        _build_entity_entry(
            entity_id=entity_id,
            comparisons=tuple(
                sorted(
                    entity_comparisons,
                    key=lambda item: (
                        item.contrast_label,
                        item.condition_a,
                        item.condition_b,
                    ),
                )
            ),
            magnitude_consistency_floor=magnitude_consistency_floor,
        )
        for entity_id, entity_comparisons in sorted(comparisons_by_entity.items())
    )
    summary = MultiContrastConsistencySummary(
        entity_count=len(entity_entries),
        shared_hit_count=sum(entry.shared_hit for entry in entity_entries),
        contrast_specific_hit_count=sum(
            entry.contrast_specific_hit for entry in entity_entries
        ),
        direction_conflict_count=sum(entry.direction_conflict for entry in entity_entries),
        magnitude_consistent_count=sum(
            entry.magnitude_consistency_status
            is MultiContrastMagnitudeConsistencyStatus.CONSISTENT
            for entry in entity_entries
        ),
        magnitude_variable_count=sum(
            entry.magnitude_consistency_status
            is MultiContrastMagnitudeConsistencyStatus.VARIABLE
            for entry in entity_entries
        ),
    )
    return MultiContrastConsistencyReport(
        entity_level=report.entity_level,
        normalization_method=report.normalization_method,
        imputation_method=report.imputation_method,
        contrast_count=len(report.reports),
        significance_threshold=significance_threshold,
        comparisons=tuple(comparison_entries),
        entities=entity_entries,
        summary=summary,
        note=(
            "multi-contrast consistency preserves shared hits, contrast-specific hits, "
            "direction conflicts, and magnitude agreement across pairwise contrasts"
        ),
    )


def render_multi_contrast_consistency_tsv(
    report: MultiContrastConsistencyReport,
) -> str:
    """Render one cross-contrast consistency report as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "entity_id",
            "protein_refs",
            "tested_contrast_count",
            "significant_contrast_count",
            "shared_hit",
            "contrast_specific_hit",
            "significant_contrast_labels",
            "contrast_specific_contrast_labels",
            "direction_conflict",
            "direction_relations",
            "magnitude_consistency_status",
            "magnitude_consistency_score",
            "min_absolute_log2_fold_change",
            "median_absolute_log2_fold_change",
            "max_absolute_log2_fold_change",
            "note",
        ]
    )
    for entry in report.entities:
        writer.writerow(
            [
                entry.entity_id,
                ";".join(entry.protein_refs),
                entry.tested_contrast_count,
                entry.significant_contrast_count,
                str(entry.shared_hit).lower(),
                str(entry.contrast_specific_hit).lower(),
                ";".join(entry.significant_contrast_labels),
                ";".join(entry.contrast_specific_contrast_labels),
                str(entry.direction_conflict).lower(),
                ";".join(entry.direction_relations),
                entry.magnitude_consistency_status.value,
                _format_float(entry.magnitude_consistency_score),
                _format_float(entry.min_absolute_log2_fold_change),
                _format_float(entry.median_absolute_log2_fold_change),
                _format_float(entry.max_absolute_log2_fold_change),
                entry.note,
            ]
        )
    return buffer.getvalue()


def export_multi_contrast_consistency_tsv(
    report: MultiContrastConsistencyReport,
    path: Path,
) -> None:
    """Write one cross-contrast consistency report to a stable TSV artifact."""

    write_output_table_tsv(path, render_multi_contrast_consistency_tsv(report))


def _build_comparison_entry(
    report: DifferentialAbundanceReport,
    *,
    entry: DifferentialAbundanceEntry,
    protein_refs: tuple[str, ...],
    significance_threshold: float,
) -> MultiContrastConsistencyComparisonEntry:
    adjusted_p_value = entry.adjusted_p_value if entry.adjusted_p_value is not None else entry.p_value
    higher_condition: str | None = None
    lower_condition: str | None = None
    if entry.log2_fold_change > 0:
        higher_condition = entry.condition_a
        lower_condition = entry.condition_b
    elif entry.log2_fold_change < 0:
        higher_condition = entry.condition_b
        lower_condition = entry.condition_a
    return MultiContrastConsistencyComparisonEntry(
        entity_id=entry.entity_id,
        protein_refs=protein_refs,
        contrast_label=_contrast_label(report),
        condition_a=entry.condition_a,
        condition_b=entry.condition_b,
        higher_condition=higher_condition,
        lower_condition=lower_condition,
        log2_fold_change=entry.log2_fold_change,
        absolute_log2_fold_change=abs(entry.log2_fold_change),
        adjusted_p_value=adjusted_p_value,
        significant=adjusted_p_value <= significance_threshold,
    )


def _build_entity_entry(
    *,
    entity_id: str,
    comparisons: tuple[MultiContrastConsistencyComparisonEntry, ...],
    magnitude_consistency_floor: float,
) -> MultiContrastConsistencyEntityEntry:
    significant = tuple(entry for entry in comparisons if entry.significant)
    significant_labels = tuple(entry.contrast_label for entry in significant)
    direction_relations = tuple(
        f"{entry.higher_condition}>{entry.lower_condition}"
        for entry in significant
        if entry.higher_condition is not None and entry.lower_condition is not None
    )
    direction_conflict = _has_direction_conflict(direction_relations)
    magnitude_values = tuple(entry.absolute_log2_fold_change for entry in significant)
    magnitude_status, magnitude_score = _magnitude_consistency(
        magnitude_values,
        floor=magnitude_consistency_floor,
    )
    shared_hit = len(significant) >= 2
    contrast_specific_hit = len(significant) == 1
    if direction_conflict:
        note = "significant contrasts imply contradictory condition ordering"
    elif contrast_specific_hit:
        note = "signal is significant in one preserved contrast only"
    elif shared_hit:
        note = "signal is shared across multiple preserved contrasts"
    else:
        note = "signal does not clear the configured adjusted-significance threshold"
    return MultiContrastConsistencyEntityEntry(
        entity_id=entity_id,
        protein_refs=comparisons[0].protein_refs if comparisons else (),
        tested_contrast_count=len(comparisons),
        significant_contrast_count=len(significant),
        significant_contrast_labels=significant_labels,
        contrast_specific_contrast_labels=(
            significant_labels if contrast_specific_hit else ()
        ),
        direction_relations=direction_relations,
        shared_hit=shared_hit,
        contrast_specific_hit=contrast_specific_hit,
        direction_conflict=direction_conflict,
        magnitude_consistency_status=magnitude_status,
        magnitude_consistency_score=magnitude_score,
        min_absolute_log2_fold_change=(
            min(magnitude_values) if magnitude_values else None
        ),
        median_absolute_log2_fold_change=(
            float(median(magnitude_values)) if magnitude_values else None
        ),
        max_absolute_log2_fold_change=(
            max(magnitude_values) if magnitude_values else None
        ),
        note=note,
    )


def _contrast_label(report: DifferentialAbundanceReport) -> str:
    return report.contrast_name or f"{report.condition_a}_vs_{report.condition_b}"


def _has_direction_conflict(direction_relations: tuple[str, ...]) -> bool:
    adjacency: dict[str, set[str]] = {}
    for relation in direction_relations:
        higher_condition, lower_condition = relation.split(">", 1)
        adjacency.setdefault(higher_condition, set()).add(lower_condition)
        adjacency.setdefault(lower_condition, set())
    visiting: set[str] = set()
    visited: set[str] = set()

    def _visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for neighbour in adjacency.get(node, ()):
            if _visit(neighbour):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(_visit(node) for node in adjacency)


def _magnitude_consistency(
    magnitudes: tuple[float, ...],
    *,
    floor: float,
) -> tuple[MultiContrastMagnitudeConsistencyStatus, float | None]:
    if len(magnitudes) < 2:
        return (
            MultiContrastMagnitudeConsistencyStatus.INSUFFICIENT_SIGNIFICANT_SUPPORT,
            None,
        )
    max_value = max(magnitudes)
    if max_value <= 0.0:
        return (MultiContrastMagnitudeConsistencyStatus.CONSISTENT, 1.0)
    score = min(magnitudes) / max_value
    status = (
        MultiContrastMagnitudeConsistencyStatus.CONSISTENT
        if score >= floor
        else MultiContrastMagnitudeConsistencyStatus.VARIABLE
    )
    return status, score


def _format_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6g}"
