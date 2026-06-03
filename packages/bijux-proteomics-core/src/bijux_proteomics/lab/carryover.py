# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Run-order carryover detection over peptide and protein intensity matrices."""

from __future__ import annotations

import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class CarryoverRunOrderEntry(JsonModel):
    """One run-order assignment for carryover review."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    run_order: int = Field(..., ge=1)


class CarryoverIntensityEntry(JsonModel):
    """One entity intensity inside one ordered run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)


class CarryoverDetectionEntry(JsonModel):
    """One source-to-affected ordered-run carryover candidate."""

    model_config = ConfigDict(extra="forbid")

    source_run: str = Field(..., min_length=1)
    source_run_order: int = Field(..., ge=1)
    affected_run: str = Field(..., min_length=1)
    affected_run_order: int = Field(..., ge=1)
    entity_id: str = Field(..., min_length=1)
    source_intensity: float = Field(..., ge=0.0)
    affected_intensity: float = Field(..., ge=0.0)
    repeated_signal_fraction: float = Field(..., ge=0.0)
    order_gap: int = Field(..., ge=1)
    carryover_score: float = Field(..., ge=0.0, le=1.0)
    concern_codes: tuple[str, ...] = Field(default_factory=tuple)


def detect_carryover(
    run_order: tuple[CarryoverRunOrderEntry, ...],
    peptide_intensity_matrix: tuple[CarryoverIntensityEntry, ...],
    *,
    high_source_relative_fraction_threshold: float = 0.75,
    low_level_repeated_signal_fraction_threshold: float = 0.1,
) -> tuple[CarryoverDetectionEntry, ...]:
    """Detect ordered-run carryover from repeated low-level entity signal."""

    if not run_order:
        raise ValueError("run_order is required for carryover analysis")
    if not peptide_intensity_matrix:
        raise ValueError("peptide_intensity_matrix must not be empty")
    if high_source_relative_fraction_threshold <= 0.0:
        raise ValueError("high_source_relative_fraction_threshold must be positive")
    if (
        low_level_repeated_signal_fraction_threshold <= 0.0
        or low_level_repeated_signal_fraction_threshold >= 1.0
    ):
        raise ValueError(
            "low_level_repeated_signal_fraction_threshold must be between 0 and 1"
        )

    ordered_runs = _ordered_runs_by_id(run_order)
    missing_run_ids = sorted(
        {
            entry.run_id
            for entry in peptide_intensity_matrix
            if entry.run_id not in ordered_runs
        }
    )
    if missing_run_ids:
        raise ValueError(
            "run_order is required for carryover analysis and is missing for: "
            + ", ".join(missing_run_ids)
        )

    intensity_by_entity_run: dict[str, dict[str, float]] = {}
    for entry in peptide_intensity_matrix:
        intensity_by_entity_run.setdefault(entry.entity_id, {}).setdefault(
            entry.run_id, 0.0
        )
        intensity_by_entity_run[entry.entity_id][entry.run_id] += entry.intensity

    rows: list[CarryoverDetectionEntry] = []
    for entity_id, run_totals in sorted(intensity_by_entity_run.items()):
        if not run_totals:
            continue
        max_intensity = max(run_totals.values())
        if max_intensity <= 0.0:
            continue
        source_threshold = max_intensity * high_source_relative_fraction_threshold
        source_run_ids = {
            run_id
            for run_id, intensity in run_totals.items()
            if intensity >= source_threshold
        }
        if not source_run_ids:
            continue

        for affected_run_id, affected_run in ordered_runs.items():
            affected_intensity = run_totals.get(affected_run_id, 0.0)
            if affected_intensity <= 0.0:
                continue
            source_run_id = _latest_source_run_before(
                ordered_runs=ordered_runs,
                source_run_ids=source_run_ids,
                affected_run_id=affected_run_id,
            )
            if source_run_id is None:
                continue
            source_run = ordered_runs[source_run_id]
            source_intensity = run_totals[source_run_id]
            repeated_signal_fraction = affected_intensity / source_intensity
            if repeated_signal_fraction > low_level_repeated_signal_fraction_threshold:
                continue
            order_gap = affected_run.run_order - source_run.run_order
            if order_gap < 1:
                continue
            rows.append(
                CarryoverDetectionEntry(
                    source_run=source_run_id,
                    source_run_order=source_run.run_order,
                    affected_run=affected_run_id,
                    affected_run_order=affected_run.run_order,
                    entity_id=entity_id,
                    source_intensity=round(source_intensity, 4),
                    affected_intensity=round(affected_intensity, 4),
                    repeated_signal_fraction=round(repeated_signal_fraction, 6),
                    order_gap=order_gap,
                    carryover_score=round(
                        _carryover_score(
                            source_intensity=source_intensity,
                            max_entity_intensity=max_intensity,
                            repeated_signal_fraction=repeated_signal_fraction,
                            low_level_repeated_signal_fraction_threshold=(
                                low_level_repeated_signal_fraction_threshold
                            ),
                            order_gap=order_gap,
                        ),
                        4,
                    ),
                    concern_codes=_concern_codes(order_gap),
                )
            )

    return tuple(
        sorted(
            rows,
            key=lambda entry: (
                entry.affected_run_order,
                entry.entity_id,
                entry.source_run_order,
            ),
        )
    )


def render_carryover_detection_tsv(
    rows: tuple[CarryoverDetectionEntry, ...],
) -> str:
    """Render carryover detection rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "source_run",
            "affected_run",
            "entity_id",
            "source_intensity",
            "affected_intensity",
            "carryover_score",
        )
    )
    for row in rows:
        writer.writerow(
            (
                row.source_run,
                row.affected_run,
                row.entity_id,
                f"{row.source_intensity:g}",
                f"{row.affected_intensity:g}",
                f"{row.carryover_score:.4f}",
            )
        )
    return buffer.getvalue()


def _ordered_runs_by_id(
    run_order: tuple[CarryoverRunOrderEntry, ...],
) -> dict[str, CarryoverRunOrderEntry]:
    duplicate_run_ids = {
        entry.run_id
        for entry in run_order
        if sum(candidate.run_id == entry.run_id for candidate in run_order) > 1
    }
    if duplicate_run_ids:
        raise ValueError(
            "carryover analysis requires unique run_id values and found duplicates for: "
            + ", ".join(sorted(duplicate_run_ids))
        )
    duplicate_run_orders = {
        entry.run_order
        for entry in run_order
        if sum(candidate.run_order == entry.run_order for candidate in run_order) > 1
    }
    if duplicate_run_orders:
        raise ValueError(
            "carryover analysis requires unique run_order values and found duplicates for: "
            + ", ".join(str(value) for value in sorted(duplicate_run_orders))
        )
    return {
        entry.run_id: entry
        for entry in sorted(
            run_order, key=lambda entry: (entry.run_order, entry.run_id)
        )
    }


def _latest_source_run_before(
    *,
    ordered_runs: dict[str, CarryoverRunOrderEntry],
    source_run_ids: set[str],
    affected_run_id: str,
) -> str | None:
    affected_run = ordered_runs[affected_run_id]
    prior_sources = [
        ordered_runs[run_id]
        for run_id in source_run_ids
        if ordered_runs[run_id].run_order < affected_run.run_order
    ]
    if not prior_sources:
        return None
    return max(prior_sources, key=lambda entry: entry.run_order).run_id


def _carryover_score(
    *,
    source_intensity: float,
    max_entity_intensity: float,
    repeated_signal_fraction: float,
    low_level_repeated_signal_fraction_threshold: float,
    order_gap: int,
) -> float:
    source_strength = source_intensity / max_entity_intensity
    low_level_strength = max(
        0.0,
        1.0 - (repeated_signal_fraction / low_level_repeated_signal_fraction_threshold),
    )
    order_proximity = 1.0 / order_gap
    return (source_strength + low_level_strength + order_proximity) / 3.0


def _concern_codes(order_gap: int) -> tuple[str, ...]:
    codes = ["high_intensity_previous_run", "low_level_repeated_signal"]
    if order_gap == 1:
        codes.append("immediate_run_order_followup")
    return tuple(codes)


__all__ = [
    "CarryoverDetectionEntry",
    "CarryoverIntensityEntry",
    "CarryoverRunOrderEntry",
    "detect_carryover",
    "render_carryover_detection_tsv",
]
