# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Success criteria for protein programs."""

from __future__ import annotations

from enum import StrEnum

from bijux_proteomics_foundation import EvidenceId
from pydantic import BaseModel, ConfigDict, Field


class MeasurementDirection(StrEnum):
    """Target direction for a success criterion."""

    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"
    BOUND = "bound"
    GREATER_THAN = "maximize"
    LESS_THAN = "minimize"


class MetricFamily(StrEnum):
    """Typed families for measurable program criteria."""

    ACTIVITY = "activity"
    AFFINITY = "affinity"
    STABILITY = "stability"
    SELECTIVITY = "selectivity"
    EXPRESSION = "expression"
    SOLUBILITY = "solubility"
    AGGREGATION = "aggregation"
    CELLULAR_ACTIVITY = "cellular_activity"
    PHENOTYPE_RESCUE = "phenotype_rescue"
    SAFETY = "safety"
    DEVELOPABILITY = "developability"


class SuccessCriterion(BaseModel):
    """Condition required for a program to advance."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: EvidenceId = Field(..., description="Stable criterion identifier.")
    metric: str = Field(..., min_length=1, description="Metric to evaluate.")
    metric_family: MetricFamily = Field(
        default=MetricFamily.ACTIVITY,
        description="Typed metric family for this criterion.",
    )
    direction: MeasurementDirection = Field(..., description="Optimization direction.")
    threshold: float = Field(..., description="Threshold for the metric.")
    upper_threshold: float | None = Field(
        default=None,
        description="Upper bound used when direction is bound.",
    )
    unit: str | None = Field(default=None, description="Optional measurement unit.")


def criterion_passes(
    criterion: SuccessCriterion,
    *,
    observed_value: float,
) -> bool:
    """Return whether an observed value satisfies a success criterion."""
    if criterion.direction is MeasurementDirection.MAXIMIZE:
        return observed_value >= criterion.threshold
    if criterion.direction is MeasurementDirection.MINIMIZE:
        return observed_value <= criterion.threshold
    if criterion.upper_threshold is None:
        raise ValueError("bound criteria require upper_threshold")
    lower = min(criterion.threshold, criterion.upper_threshold)
    upper = max(criterion.threshold, criterion.upper_threshold)
    return lower <= observed_value <= upper


def build_assay_grounded_criteria(
    *,
    target_id: str,
) -> list[SuccessCriterion]:
    """Build assay-grounded criteria that map to common proteomics endpoints."""
    return [
        SuccessCriterion(
            criterion_id=f"{target_id}-affinity",
            metric="binding_kd",
            metric_family=MetricFamily.AFFINITY,
            direction=MeasurementDirection.MINIMIZE,
            threshold=1e-6,
            unit="M",
        ),
        SuccessCriterion(
            criterion_id=f"{target_id}-stability",
            metric="delta_tm",
            metric_family=MetricFamily.STABILITY,
            direction=MeasurementDirection.MAXIMIZE,
            threshold=2.0,
            unit="C",
        ),
        SuccessCriterion(
            criterion_id=f"{target_id}-expression",
            metric="yield_mg_per_l",
            metric_family=MetricFamily.EXPRESSION,
            direction=MeasurementDirection.MAXIMIZE,
            threshold=5.0,
            unit="mg/L",
        ),
        SuccessCriterion(
            criterion_id=f"{target_id}-solubility",
            metric="solubility_fraction",
            metric_family=MetricFamily.SOLUBILITY,
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.8,
        ),
        SuccessCriterion(
            criterion_id=f"{target_id}-aggregation",
            metric="aggregation_index",
            metric_family=MetricFamily.AGGREGATION,
            direction=MeasurementDirection.MINIMIZE,
            threshold=0.2,
        ),
        SuccessCriterion(
            criterion_id=f"{target_id}-cellular",
            metric="cellular_activity",
            metric_family=MetricFamily.CELLULAR_ACTIVITY,
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.6,
        ),
    ]
