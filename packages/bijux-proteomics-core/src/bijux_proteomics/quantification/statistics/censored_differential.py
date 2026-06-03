# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Censor-aware two-group differential testing over quantitative matrices."""

from __future__ import annotations

from collections.abc import Mapping
import csv
from enum import StrEnum
from io import StringIO
import math
from typing import Any, cast

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import QuantMatrix as CanonicalQuantMatrix
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    QuantValue,
    _condition_lookup,
    _student_t_two_sided_p_value,
    _welch_t_test,
    coerce_label_free_quant_table,
)
from bijux_proteomics.quantification.missingness.missingness import (
    MissingnessClassificationReport,
    MissingnessLabel,
)
from bijux_proteomics_foundation import JsonModel


class CensoringStatus(StrEnum):
    """Stable censoring states for two-group differential rows."""

    UNCENSORED = "uncensored"
    LEFT_CENSORED_CONDITION_A = "left_censored_condition_a"
    LEFT_CENSORED_CONDITION_B = "left_censored_condition_b"
    CONDITION_SPECIFIC_ABSENCE = "condition_specific_absence"
    OBSERVED_WITH_RANDOM_MISSINGNESS = "observed_with_random_missingness"


class CensoredDifferentialEntry(JsonModel):
    """One censor-aware two-group differential result."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    log2fc_estimate: float
    censored_p_value: float = Field(..., ge=0.0, le=1.0)
    q_value: float = Field(..., ge=0.0, le=1.0)
    censoring_status: CensoringStatus


class CensoredDifferentialReport(JsonModel):
    """Censor-aware differential report over one two-condition contrast."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    entries: tuple[CensoredDifferentialEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def test_censored_two_group(
    matrix: LabelFreeQuantTable | CanonicalQuantMatrix,
    missingness_labels: MissingnessClassificationReport,
    design: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None = None,
    condition_b: str | None = None,
) -> CensoredDifferentialReport:
    """Estimate one two-group differential report while respecting left censoring."""

    table = coerce_label_free_quant_table(matrix)
    if not design:
        raise ValueError("design must not be empty")

    condition_by_sample = _condition_lookup(design)
    conditions = tuple(
        sorted({condition for condition in condition_by_sample.values() if condition})
    )
    if condition_a is None or condition_b is None:
        if len(conditions) != 2:
            raise ValueError(
                "censored differential testing requires exactly two conditions or explicit condition names"
            )
        condition_a, condition_b = conditions
    if condition_a is None or condition_b is None:
        raise RuntimeError(
            "censored differential testing requires resolved condition names after validation"
        )

    samples_a = tuple(
        sample_id
        for sample_id, condition in condition_by_sample.items()
        if condition == condition_a
    )
    samples_b = tuple(
        sample_id
        for sample_id, condition in condition_by_sample.items()
        if condition == condition_b
    )
    if not samples_a or not samples_b:
        raise ValueError("both conditions must contain at least one sample")

    label_by_entity = {
        entry.entity_id: entry.label for entry in missingness_labels.entries
    }
    value_lookup = {(value.entity_id, value.sample_id): value for value in table.values}
    censor_floor = _global_censor_floor(table)
    floor_variance = _floor_variance(table, censor_floor)

    entries: list[CensoredDifferentialEntry] = []
    for entity_id in table.entity_ids:
        values_a = _observed_log2_values(value_lookup, entity_id, samples_a)
        values_b = _observed_log2_values(value_lookup, entity_id, samples_b)
        label = label_by_entity.get(entity_id, MissingnessLabel.RANDOM)
        entry = _build_censored_entry(
            entity_id=entity_id,
            label=label,
            values_a=values_a,
            values_b=values_b,
            expected_count_a=len(samples_a),
            expected_count_b=len(samples_b),
            censor_floor=censor_floor,
            floor_variance=floor_variance,
        )
        entries.append(entry)

    q_values = _benjamini_hochberg(tuple(entry.censored_p_value for entry in entries))
    corrected = tuple(
        entry.model_copy(update={"q_value": q_values[index]})
        for index, entry in enumerate(entries)
    )
    return CensoredDifferentialReport(
        condition_a=condition_a,
        condition_b=condition_b,
        entries=tuple(sorted(corrected, key=lambda entry: entry.entity_id)),
        note=(
            "censor-aware differential testing keeps low-abundance missingness on a "
            "left-censored boundary instead of collapsing it into one fixed imputed "
            "value, so effect sizes and significance can diverge from ordinary "
            "imputation-based testing"
        ),
    )


def render_censored_differential_tsv(report: CensoredDifferentialReport) -> str:
    """Render censor-aware differential rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "log2fc_estimate",
            "censored_p_value",
            "q_value",
            "censoring_status",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.entity_id,
                f"{entry.log2fc_estimate:.6f}",
                f"{entry.censored_p_value:.6f}",
                f"{entry.q_value:.6f}",
                entry.censoring_status.value,
            )
        )
    return buffer.getvalue()


cast(Any, test_censored_two_group).__test__ = False


def _observed_log2_values(
    value_lookup: Mapping[tuple[str, str], QuantValue],
    entity_id: str,
    sample_ids: tuple[str, ...],
) -> np.ndarray:
    values: list[float] = []
    for sample_id in sample_ids:
        abundance = value_lookup[(entity_id, sample_id)].abundance
        if abundance is None:
            continue
        values.append(math.log2(float(abundance) + 1.0))
    return np.array(values, dtype=float)


def _build_censored_entry(
    *,
    entity_id: str,
    label: MissingnessLabel,
    values_a: np.ndarray,
    values_b: np.ndarray,
    expected_count_a: int,
    expected_count_b: int,
    censor_floor: float,
    floor_variance: float,
) -> CensoredDifferentialEntry:
    fully_observed = (
        values_a.size == expected_count_a and values_b.size == expected_count_b
    )
    if values_a.size >= 2 and values_b.size >= 2:
        log2fc, p_value = _welch_t_test(values_a, values_b)
        status = (
            CensoringStatus.UNCENSORED
            if fully_observed
            else CensoringStatus.OBSERVED_WITH_RANDOM_MISSINGNESS
        )
        return CensoredDifferentialEntry(
            entity_id=entity_id,
            log2fc_estimate=round(log2fc, 6),
            censored_p_value=round(p_value, 6),
            q_value=1.0,
            censoring_status=status,
        )

    if (
        values_a.size == 0
        and values_b.size > 0
        and label
        in {
            MissingnessLabel.INTENSITY_CENSORED,
            MissingnessLabel.CONDITION_SPECIFIC,
        }
    ):
        return _fully_censored_condition_entry(
            entity_id=entity_id,
            observed_values=values_b,
            censor_floor=censor_floor,
            floor_variance=floor_variance,
            status=(
                CensoringStatus.CONDITION_SPECIFIC_ABSENCE
                if label is MissingnessLabel.CONDITION_SPECIFIC
                else CensoringStatus.LEFT_CENSORED_CONDITION_A
            ),
            direction=1.0,
        )
    if (
        values_b.size == 0
        and values_a.size > 0
        and label
        in {
            MissingnessLabel.INTENSITY_CENSORED,
            MissingnessLabel.CONDITION_SPECIFIC,
        }
    ):
        return _fully_censored_condition_entry(
            entity_id=entity_id,
            observed_values=values_a,
            censor_floor=censor_floor,
            floor_variance=floor_variance,
            status=(
                CensoringStatus.CONDITION_SPECIFIC_ABSENCE
                if label is MissingnessLabel.CONDITION_SPECIFIC
                else CensoringStatus.LEFT_CENSORED_CONDITION_B
            ),
            direction=-1.0,
        )

    mean_a = float(np.mean(values_a)) if values_a.size else censor_floor
    mean_b = float(np.mean(values_b)) if values_b.size else censor_floor
    log2fc = mean_b - mean_a
    return CensoredDifferentialEntry(
        entity_id=entity_id,
        log2fc_estimate=round(log2fc, 6),
        censored_p_value=1.0,
        q_value=1.0,
        censoring_status=CensoringStatus.OBSERVED_WITH_RANDOM_MISSINGNESS,
    )


def _fully_censored_condition_entry(
    *,
    entity_id: str,
    observed_values: np.ndarray,
    censor_floor: float,
    floor_variance: float,
    status: CensoringStatus,
    direction: float,
) -> CensoredDifferentialEntry:
    observed_mean = float(np.mean(observed_values))
    latent_censored_mean = censor_floor - math.sqrt(max(floor_variance, 1e-6))
    log2fc = direction * (observed_mean - latent_censored_mean)
    observed_variance = (
        float(np.var(observed_values, ddof=1))
        if observed_values.size >= 2
        else floor_variance
    )
    standard_error = math.sqrt(
        observed_variance / max(float(observed_values.size), 1.0) + floor_variance
    )
    p_value = 1.0
    if standard_error > 0.0 and math.isfinite(standard_error):
        t_statistic = abs(log2fc) / standard_error
        degrees_of_freedom = max(float(observed_values.size), 1.0)
        p_value = _student_t_two_sided_p_value(t_statistic, degrees_of_freedom)
    return CensoredDifferentialEntry(
        entity_id=entity_id,
        log2fc_estimate=round(log2fc, 6),
        censored_p_value=round(min(max(p_value, 0.0), 1.0), 6),
        q_value=1.0,
        censoring_status=status,
    )


def _global_censor_floor(table: LabelFreeQuantTable) -> float:
    observed = [
        math.log2(float(value.abundance) + 1.0)
        for value in table.values
        if value.abundance is not None and float(value.abundance) > 0.0
    ]
    if not observed:
        return 0.0
    observed_array = np.array(observed, dtype=float)
    return float(np.quantile(observed_array, 0.1))


def _floor_variance(table: LabelFreeQuantTable, censor_floor: float) -> float:
    low_tail = [
        math.log2(float(value.abundance) + 1.0)
        for value in table.values
        if value.abundance is not None
        and float(value.abundance) > 0.0
        and math.log2(float(value.abundance) + 1.0) <= censor_floor + 0.5
    ]
    if len(low_tail) < 2:
        return 0.1
    return max(float(np.var(np.array(low_tail, dtype=float), ddof=1)), 0.05)


def _benjamini_hochberg(p_values: tuple[float, ...]) -> tuple[float, ...]:
    if not p_values:
        return ()
    adjusted: list[float] = [1.0] * len(p_values)
    running = 1.0
    total = len(p_values)
    ordered = sorted(enumerate(p_values), key=lambda item: item[1])
    for reverse_rank, (index, p_value) in enumerate(reversed(ordered), start=1):
        rank = total - reverse_rank + 1
        candidate = p_value * total / rank
        running = min(running, candidate)
        adjusted[index] = min(max(running, 0.0), 1.0)
    return tuple(adjusted)


__all__ = [
    "CensoredDifferentialEntry",
    "CensoredDifferentialReport",
    "CensoringStatus",
    "render_censored_differential_tsv",
    "test_censored_two_group",
]
