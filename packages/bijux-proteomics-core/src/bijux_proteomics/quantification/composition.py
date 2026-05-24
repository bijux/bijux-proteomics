# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned compositional-bias diagnostics for quantitative normalization risk."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.quantification.contracts import LabelFreeQuantTable, QuantValue
from bijux_proteomics_foundation import JsonModel


class CompositionalBiasRisk(StrEnum):
    """Stable risk tiers for total-signal normalization under composition skew."""

    LOW = "low"
    CAUTION = "caution"
    HIGH = "high"


class CompositionalBiasEntry(JsonModel):
    """One sample-level compositional-bias diagnostic row."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    dominant_entity_fraction: float = Field(..., ge=0.0, le=1.0)
    total_signal_skew: float = Field(..., ge=0.0)
    normalization_risk: CompositionalBiasRisk
    dominant_entities: tuple[str, ...] = Field(default_factory=tuple)


class CompositionalBiasReport(JsonModel):
    """Owned report over sample-level composition distortion and normalization risk."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[CompositionalBiasEntry, ...] = Field(default_factory=tuple)
    high_risk_sample_count: int = Field(..., ge=0)
    caution_sample_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


def detect_compositional_bias(
    table: LabelFreeQuantTable,
    *,
    dominant_entity_count: int = 3,
) -> CompositionalBiasReport:
    """Detect samples whose total signal is dominated by a few entities."""

    if dominant_entity_count < 1:
        raise ValueError("dominant_entity_count must be at least one")
    values_by_sample: dict[str, list[QuantValue]] = {sample_id: [] for sample_id in table.sample_ids}
    for value in table.values:
        if value.abundance is None or value.abundance <= 0.0:
            continue
        values_by_sample.setdefault(value.sample_id, []).append(value)
    sample_totals = {
        sample_id: sum(value.abundance or 0.0 for value in sample_values)
        for sample_id, sample_values in values_by_sample.items()
    }
    positive_totals = sorted(total for total in sample_totals.values() if total > 0.0)
    median_total = (
        positive_totals[len(positive_totals) // 2]
        if positive_totals
        else 1.0
    )

    entries = tuple(
        _build_compositional_bias_entry(
            sample_id=sample_id,
            sample_values=values_by_sample.get(sample_id, ()),
            sample_total=sample_totals.get(sample_id, 0.0),
            median_total=median_total,
            dominant_entity_count=dominant_entity_count,
        )
        for sample_id in table.sample_ids
    )
    return CompositionalBiasReport(
        entries=entries,
        high_risk_sample_count=sum(
            entry.normalization_risk is CompositionalBiasRisk.HIGH
            for entry in entries
        ),
        caution_sample_count=sum(
            entry.normalization_risk is CompositionalBiasRisk.CAUTION
            for entry in entries
        ),
        note=(
            "high dominant-entity fractions with inflated total signal warn against "
            "total-signal normalization because a few entities can drive sample scaling"
        ),
    )


def render_compositional_bias_tsv(report: CompositionalBiasReport) -> str:
    """Render one compositional-bias report as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sample_id",
            "dominant_entity_fraction",
            "total_signal_skew",
            "normalization_risk",
            "dominant_entities",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.sample_id,
                entry.dominant_entity_fraction,
                entry.total_signal_skew,
                entry.normalization_risk.value,
                ";".join(entry.dominant_entities),
            )
        )
    return buffer.getvalue()


def _build_compositional_bias_entry(
    *,
    sample_id: str,
    sample_values: list[QuantValue] | tuple[QuantValue, ...],
    sample_total: float,
    median_total: float,
    dominant_entity_count: int,
) -> CompositionalBiasEntry:
    if sample_total <= 0.0 or not sample_values:
        return CompositionalBiasEntry(
            sample_id=sample_id,
            dominant_entity_fraction=0.0,
            total_signal_skew=0.0,
            normalization_risk=CompositionalBiasRisk.LOW,
            dominant_entities=(),
        )
    ordered = tuple(
        sorted(
            sample_values,
            key=lambda value: ((value.abundance or 0.0), value.entity_id),
            reverse=True,
        )
    )
    dominant_values = ordered[:dominant_entity_count]
    dominant_fraction = (dominant_values[0].abundance or 0.0) / sample_total
    total_signal_skew = sample_total / max(median_total, 1e-9)
    return CompositionalBiasEntry(
        sample_id=sample_id,
        dominant_entity_fraction=round(float(dominant_fraction), 4),
        total_signal_skew=round(float(total_signal_skew), 4),
        normalization_risk=_normalization_risk(
            dominant_fraction=dominant_fraction,
            total_signal_skew=total_signal_skew,
        ),
        dominant_entities=tuple(value.entity_id for value in dominant_values),
    )


def _normalization_risk(
    *,
    dominant_fraction: float,
    total_signal_skew: float,
) -> CompositionalBiasRisk:
    if (
        dominant_fraction >= 0.7
        or (dominant_fraction >= 0.55 and total_signal_skew >= 1.5)
    ):
        return CompositionalBiasRisk.HIGH
    if dominant_fraction >= 0.45 or total_signal_skew >= 1.25:
        return CompositionalBiasRisk.CAUTION
    return CompositionalBiasRisk.LOW


__all__ = [
    "CompositionalBiasEntry",
    "CompositionalBiasReport",
    "CompositionalBiasRisk",
    "detect_compositional_bias",
    "render_compositional_bias_tsv",
]
