# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned cross-method agreement diagnostics for differential quantification results."""

from __future__ import annotations

import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.quantification.contracts.differential import (
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
)
from bijux_proteomics.quantification.contracts.input_models import QuantRollupMethod
from bijux_proteomics_foundation import JsonModel


class QuantMethodDifferentialResult(JsonModel):
    """One named differential result table produced by a quantification method."""

    model_config = ConfigDict(extra="forbid")

    method_id: str = Field(..., min_length=1)
    rollup_method: QuantRollupMethod | None = None
    differential_report: DifferentialAbundanceReport


class QuantMethodAgreementEntry(JsonModel):
    """One entity-level stability summary across multiple quantification methods."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    methods_significant_count: int = Field(..., ge=0)
    direction_agreement: float = Field(..., ge=0.0, le=1.0)
    effect_range: float = Field(..., ge=0.0)
    method_sensitive: bool


class QuantMethodAgreementReport(JsonModel):
    """Stable agreement report over differential results from multiple methods."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    compared_method_ids: tuple[str, ...] = Field(default_factory=tuple)
    significance_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    effect_range_tolerance: float = Field(default=1.0, ge=0.0)
    entries: tuple[QuantMethodAgreementEntry, ...] = Field(default_factory=tuple)
    stable_hit_count: int = Field(..., ge=0)
    method_sensitive_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


def compare_quant_methods(
    result_tables: tuple[QuantMethodDifferentialResult, ...],
    *,
    significance_threshold: float = 0.05,
    effect_range_tolerance: float = 1.0,
) -> QuantMethodAgreementReport:
    """Compare differential-result stability across rollup and normalization methods."""

    if len(result_tables) < 2:
        raise ValueError(
            "method agreement requires at least two differential result tables"
        )
    if effect_range_tolerance < 0.0:
        raise ValueError("effect_range_tolerance must be non-negative")

    reference = result_tables[0].differential_report
    for result in result_tables[1:]:
        _require_comparable_differential_reports(reference, result.differential_report)

    entry_lookup_by_method = {
        result.method_id: {
            entry.entity_id: entry for entry in result.differential_report.entries
        }
        for result in result_tables
    }
    entity_ids = tuple(
        sorted(
            {
                entity_id
                for lookup in entry_lookup_by_method.values()
                for entity_id in lookup
            }
        )
    )
    compared_method_ids = tuple(result.method_id for result in result_tables)
    entries = tuple(
        _build_method_agreement_entry(
            entity_id=entity_id,
            compared_method_ids=compared_method_ids,
            entry_lookup_by_method=entry_lookup_by_method,
            significance_threshold=significance_threshold,
            effect_range_tolerance=effect_range_tolerance,
        )
        for entity_id in entity_ids
    )
    stable_hit_count = sum(
        entry.methods_significant_count == len(compared_method_ids)
        and not entry.method_sensitive
        for entry in entries
    )
    method_sensitive_count = sum(entry.method_sensitive for entry in entries)
    return QuantMethodAgreementReport(
        condition_a=reference.condition_a,
        condition_b=reference.condition_b,
        compared_method_ids=compared_method_ids,
        significance_threshold=significance_threshold,
        effect_range_tolerance=effect_range_tolerance,
        entries=entries,
        stable_hit_count=stable_hit_count,
        method_sensitive_count=method_sensitive_count,
        note=(
            "method agreement compares differential significance and effect direction "
            "across quantification methods so stable hits remain distinct from "
            "method-sensitive hits"
        ),
    )


def render_quant_method_agreement_tsv(report: QuantMethodAgreementReport) -> str:
    """Render method-agreement rows as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "methods_significant_count",
            "direction_agreement",
            "effect_range",
            "method_sensitive",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.entity_id,
                entry.methods_significant_count,
                f"{entry.direction_agreement:.6f}",
                f"{entry.effect_range:.6f}",
                str(entry.method_sensitive).lower(),
            )
        )
    return buffer.getvalue()


def _build_method_agreement_entry(
    *,
    entity_id: str,
    compared_method_ids: tuple[str, ...],
    entry_lookup_by_method: dict[str, dict[str, DifferentialAbundanceEntry]],
    significance_threshold: float,
    effect_range_tolerance: float,
) -> QuantMethodAgreementEntry:
    significant_entries = tuple(
        entry
        for method_id in compared_method_ids
        if (entry := entry_lookup_by_method.get(method_id, {}).get(entity_id))
        is not None
        and _is_significant(entry, threshold=significance_threshold)
    )
    methods_significant_count = len(significant_entries)
    direction_agreement = _direction_agreement(significant_entries)
    effect_range = _effect_range(significant_entries)
    method_sensitive = _method_sensitive(
        significant_entries=significant_entries,
        total_method_count=len(compared_method_ids),
        direction_agreement=direction_agreement,
        effect_range=effect_range,
        effect_range_tolerance=effect_range_tolerance,
    )
    return QuantMethodAgreementEntry(
        entity_id=entity_id,
        methods_significant_count=methods_significant_count,
        direction_agreement=round(direction_agreement, 6),
        effect_range=round(effect_range, 6),
        method_sensitive=method_sensitive,
    )


def _direction_agreement(
    significant_entries: tuple[DifferentialAbundanceEntry, ...],
) -> float:
    if not significant_entries:
        return 1.0
    positive = sum(entry.log2_fold_change >= 0.0 for entry in significant_entries)
    negative = len(significant_entries) - positive
    return max(positive, negative) / len(significant_entries)


def _effect_range(
    significant_entries: tuple[DifferentialAbundanceEntry, ...],
) -> float:
    if len(significant_entries) < 2:
        return 0.0
    fold_changes = [entry.log2_fold_change for entry in significant_entries]
    return max(fold_changes) - min(fold_changes)


def _method_sensitive(
    *,
    significant_entries: tuple[DifferentialAbundanceEntry, ...],
    total_method_count: int,
    direction_agreement: float,
    effect_range: float,
    effect_range_tolerance: float,
) -> bool:
    if not significant_entries:
        return False
    if len(significant_entries) != total_method_count:
        return True
    if direction_agreement < 1.0:
        return True
    return effect_range > effect_range_tolerance


def _is_significant(
    entry: DifferentialAbundanceEntry,
    *,
    threshold: float,
) -> bool:
    value = (
        entry.adjusted_p_value if entry.adjusted_p_value is not None else entry.p_value
    )
    return value <= threshold


def _require_comparable_differential_reports(
    reference: DifferentialAbundanceReport,
    candidate: DifferentialAbundanceReport,
) -> None:
    if reference.entity_level is not candidate.entity_level:
        raise ValueError("method agreement requires matching entity levels")
    if reference.condition_a != candidate.condition_a:
        raise ValueError("method agreement requires matching condition_a labels")
    if reference.condition_b != candidate.condition_b:
        raise ValueError("method agreement requires matching condition_b labels")
    if reference.contrast_name != candidate.contrast_name:
        raise ValueError("method agreement requires matching contrast names")


__all__ = [
    "QuantMethodAgreementEntry",
    "QuantMethodAgreementReport",
    "QuantMethodDifferentialResult",
    "compare_quant_methods",
    "render_quant_method_agreement_tsv",
]
