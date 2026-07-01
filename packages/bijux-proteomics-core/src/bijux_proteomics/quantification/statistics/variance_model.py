# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Intensity-dependent variance modeling over quantitative matrices."""

from __future__ import annotations

import csv
from io import StringIO
import math
from typing import cast

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import QuantMatrix as CanonicalQuantMatrix
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields
from bijux_proteomics.quantification.contracts.input_models import (
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
)
from bijux_proteomics.quantification.contracts.matrix_building import (
    _matrix_value_index,
    coerce_label_free_quant_table,
)
from bijux_proteomics.quantification.contracts.matrix_models import (
    LabelFreeQuantTable,
    QuantValue,
)
from bijux_proteomics_foundation import JsonModel


class MeanVarianceTrendEntry(JsonModel):
    """One entity-level observed and expected variance row."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    mean_intensity: float = Field(..., ge=0.0)
    observed_variance: float = Field(..., ge=0.0)
    expected_variance: float = Field(..., ge=0.0)
    variance_residual: float
    quantitative_confidence: float = Field(..., ge=0.0, le=1.0)
    observed_sample_count: int = Field(..., ge=2)


class MeanVarianceTrendReport(JsonModel):
    """Intensity-dependent variance trend over one quantitative matrix."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    entries: tuple[MeanVarianceTrendEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def fit_mean_variance_trend(
    matrix: LabelFreeQuantTable | CanonicalQuantMatrix,
    *,
    minimum_observed_samples: int = 2,
    smoothing_window: int = 5,
) -> MeanVarianceTrendReport:
    """Fit one monotone mean-variance trend over observed log2 abundances."""

    table = coerce_label_free_quant_table(matrix)
    if minimum_observed_samples < 2:
        raise ValueError("minimum_observed_samples must be at least 2")
    if smoothing_window < 1:
        raise ValueError("smoothing_window must be positive")

    value_lookup = _matrix_value_index(table)
    raw_entries: list[MeanVarianceTrendEntry] = []
    for entity_id in table.entity_ids:
        observed_values: list[float] = []
        for sample_id in table.sample_ids:
            value: QuantValue = value_lookup[(entity_id, sample_id)]
            abundance = value.abundance
            if abundance is None:
                continue
            observed_values.append(math.log2(abundance + 1.0))
        if len(observed_values) < minimum_observed_samples:
            continue
        values = np.array(observed_values, dtype=float)
        raw_entries.append(
            MeanVarianceTrendEntry(
                entity_id=entity_id,
                mean_intensity=float(np.mean(values)),
                observed_variance=float(np.var(values, ddof=1)),
                expected_variance=0.0,
                variance_residual=0.0,
                quantitative_confidence=0.0,
                observed_sample_count=len(observed_values),
            )
        )

    sorted_entries = sorted(
        raw_entries, key=lambda entry: (entry.mean_intensity, entry.entity_id)
    )
    observed_variances = tuple(entry.observed_variance for entry in sorted_entries)
    smoothed_variances = _running_median(
        observed_variances,
        _effective_window(smoothing_window, len(observed_variances)),
    )
    expected_variances = _enforce_non_increasing(smoothed_variances)

    entries: list[MeanVarianceTrendEntry] = []
    for entry, expected_variance in zip(
        sorted_entries, expected_variances, strict=False
    ):
        variance_residual = entry.observed_variance - expected_variance
        quantitative_confidence = _quantitative_confidence(
            expected_variance=expected_variance,
            variance_residual=variance_residual,
        )
        entries.append(
            entry.model_copy(
                update={
                    "expected_variance": round(expected_variance, 6),
                    "variance_residual": round(variance_residual, 6),
                    "quantitative_confidence": round(quantitative_confidence, 6),
                }
            )
        )

    return MeanVarianceTrendReport(
        entity_level=table.entity_level,
        measure_kind=table.measure_kind,
        aggregation_method=table.aggregation_method,
        entries=cast(
            tuple[MeanVarianceTrendEntry, ...],
            sort_rows_by_fields(tuple(entries), "entity_id"),
        ),
        note=(
            "mean-variance modeling smooths observed log2 variance across intensity "
            "rank and enforces a monotone trend so low-intensity noisy entities "
            "carry lower quantitative confidence than stable high-intensity ones"
        ),
    )


def render_mean_variance_trend_tsv(report: MeanVarianceTrendReport) -> str:
    """Render the required mean-variance trend output table as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "mean_intensity",
            "observed_variance",
            "expected_variance",
            "variance_residual",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.entity_id,
                f"{entry.mean_intensity:.6f}",
                f"{entry.observed_variance:.6f}",
                f"{entry.expected_variance:.6f}",
                f"{entry.variance_residual:.6f}",
            )
        )
    return buffer.getvalue()


def _effective_window(window: int, count: int) -> int:
    if count <= 1:
        return 1
    bounded = min(window, count)
    return bounded if bounded % 2 == 1 else max(1, bounded - 1)


def _running_median(values: tuple[float, ...], window: int) -> tuple[float, ...]:
    if not values:
        return ()
    radius = window // 2
    medians: list[float] = []
    for index in range(len(values)):
        start = max(0, index - radius)
        stop = min(len(values), index + radius + 1)
        medians.append(float(np.median(np.array(values[start:stop], dtype=float))))
    return tuple(medians)


def _enforce_non_increasing(values: tuple[float, ...]) -> tuple[float, ...]:
    running = math.inf
    enforced: list[float] = []
    for value in values:
        running = min(running, value)
        enforced.append(running)
    return tuple(enforced)


def _quantitative_confidence(
    *,
    expected_variance: float,
    variance_residual: float,
) -> float:
    burden = expected_variance + max(0.0, variance_residual)
    return 1.0 / (1.0 + burden)


__all__ = [
    "MeanVarianceTrendEntry",
    "MeanVarianceTrendReport",
    "fit_mean_variance_trend",
    "render_mean_variance_trend_tsv",
]
