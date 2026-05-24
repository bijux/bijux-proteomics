# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned study-design diagnostics for blocked analytical contrasts."""

from __future__ import annotations

import csv
from itertools import combinations
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.study.experiment_design import ExperimentDesign, coerce_experiment_design
from bijux_proteomics_foundation import JsonModel


class BatchConditionConfoundingReport(JsonModel):
    """One durable decision about whether batch blocks condition contrasts."""

    model_config = ConfigDict(extra="forbid")

    batch_field: str = Field(..., min_length=1)
    selected_conditions: tuple[str, ...] = Field(default_factory=tuple)
    is_confounded: bool
    confounded_terms: tuple[str, ...] = Field(default_factory=tuple)
    blocked_contrasts: tuple[str, ...] = Field(default_factory=tuple)
    reason: str = Field(..., min_length=1)


def detect_batch_condition_confounding(
    samples: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    batch_field: str = "batch",
    selected_conditions: tuple[str, ...] = (),
) -> BatchConditionConfoundingReport:
    """Detect batch and condition aliasing that blocks differential contrasts."""

    experiment_design = coerce_experiment_design(samples)
    available_conditions = tuple(
        sorted({entry.condition for entry in experiment_design.entries if entry.condition})
    )
    active_conditions = (
        tuple(
            condition
            for condition in selected_conditions
            if condition in available_conditions
        )
        if selected_conditions
        else available_conditions
    )
    if batch_field in ("",):
        raise ValueError("batch_field must not be empty")
    if batch_field is None or len(active_conditions) < 2:
        return BatchConditionConfoundingReport(
            batch_field=batch_field or "batch",
            selected_conditions=active_conditions,
            is_confounded=False,
            reason="batch-condition confounding requires batch metadata and at least two active conditions",
        )

    relevant_entries = tuple(
        entry for entry in experiment_design.entries if entry.condition in active_conditions
    )
    batch_to_conditions: dict[str, set[str]] = {}
    condition_to_batches: dict[str, set[str]] = {}
    for entry in relevant_entries:
        batch = _resolve_entry_value(entry, batch_field)
        if batch in (None, ""):
            continue
        batch_value = str(batch)
        batch_to_conditions.setdefault(batch_value, set()).add(entry.condition)
        condition_to_batches.setdefault(entry.condition, set()).add(batch_value)

    if len(batch_to_conditions) < 2 or len(condition_to_batches) < 2:
        return BatchConditionConfoundingReport(
            batch_field=batch_field,
            selected_conditions=active_conditions,
            is_confounded=False,
            reason="batch-condition confounding requires at least two conditions with explicit batch assignments",
        )

    blocked_contrasts: list[str] = []
    confounded_terms: set[str] = set()
    for condition_a, condition_b in combinations(active_conditions, 2):
        batches_a = condition_to_batches.get(condition_a, set())
        batches_b = condition_to_batches.get(condition_b, set())
        if len(batches_a) != 1 or len(batches_b) != 1:
            continue
        batch_a = next(iter(batches_a))
        batch_b = next(iter(batches_b))
        if batch_a == batch_b:
            continue
        if len(batch_to_conditions.get(batch_a, set())) != 1:
            continue
        if len(batch_to_conditions.get(batch_b, set())) != 1:
            continue
        blocked_contrasts.append(f"{condition_a}_vs_{condition_b}")
        confounded_terms.add(f"{condition_a}:{batch_a}")
        confounded_terms.add(f"{condition_b}:{batch_b}")

    is_confounded = bool(blocked_contrasts)
    if is_confounded:
        reason = (
            "batch assignments are fully aliased with condition labels for "
            + ", ".join(blocked_contrasts)
        )
    else:
        reason = (
            "batch assignments span the active conditions and do not fully block the selected contrasts"
        )
    return BatchConditionConfoundingReport(
        batch_field=batch_field,
        selected_conditions=active_conditions,
        is_confounded=is_confounded,
        confounded_terms=tuple(sorted(confounded_terms)),
        blocked_contrasts=tuple(sorted(blocked_contrasts)),
        reason=reason,
    )


def render_batch_condition_confounding_tsv(
    report: BatchConditionConfoundingReport,
) -> str:
    """Render batch-condition confounding as one stable TSV row."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "batch_field",
            "selected_conditions",
            "is_confounded",
            "confounded_terms",
            "blocked_contrasts",
            "reason",
        )
    )
    writer.writerow(
        (
            report.batch_field,
            ";".join(report.selected_conditions),
            str(report.is_confounded).lower(),
            ";".join(report.confounded_terms),
            ";".join(report.blocked_contrasts),
            report.reason,
        )
    )
    return buffer.getvalue()


def _resolve_entry_value(
    entry: ExperimentalDesignEntry,
    field_name: str,
) -> str | int | float | bool | None:
    if hasattr(entry, field_name):
        return getattr(entry, field_name)
    return entry.metadata.get(field_name)


__all__ = [
    "BatchConditionConfoundingReport",
    "detect_batch_condition_confounding",
    "render_batch_condition_confounding_tsv",
]
