# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Contrast resolution and entity selection for biological report workflows."""

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import DifferentialAbundanceReport
from bijux_proteomics.study import ExperimentDesign, coerce_experiment_design
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)


def _resolve_contrast(
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None,
    condition_b: str | None,
) -> tuple[str, str]:
    experiment_design = coerce_experiment_design(design_entries)
    if bool(condition_a) ^ bool(condition_b):
        raise ValueError("both condition_a and condition_b are required together")
    if condition_a is not None and condition_b is not None:
        return condition_a, condition_b
    conditions = experiment_design.conditions
    if len(conditions) != 2:
        raise ValueError(
            "biological result reporting requires exactly two conditions or an explicit contrast"
        )
    return conditions[0], conditions[1]


def _select_significant_entity_ids(
    report: DifferentialAbundanceReport,
    *,
    policy: BiologicalResultSelectionPolicy,
) -> tuple[str, ...]:
    return tuple(
        entry.entity_id
        for entry in report.entries
        if entry.adjusted_p_value is not None
        and entry.adjusted_p_value <= policy.max_adjusted_p_value
        and abs(entry.log2_fold_change) >= policy.min_absolute_log2_fold_change
    )


def _select_heatmap_entity_ids(
    report: DifferentialAbundanceReport,
    *,
    policy: BiologicalResultSelectionPolicy,
) -> tuple[str, ...]:
    significant_entity_ids = _select_significant_entity_ids(report, policy=policy)
    if significant_entity_ids:
        return significant_entity_ids
    ranked_entries = sorted(
        report.entries,
        key=lambda entry: (
            -(abs(entry.log2_fold_change)),
            entry.adjusted_p_value if entry.adjusted_p_value is not None else 1.0,
            entry.entity_id,
        ),
    )
    return tuple(
        entry.entity_id for entry in ranked_entries[: policy.heatmap_max_entity_count]
    )
