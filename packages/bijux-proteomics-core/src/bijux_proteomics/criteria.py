# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Success criteria for protein programs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from bijux_proteomics_foundation import EvidenceId


class MeasurementDirection(StrEnum):
    """Target direction for a success criterion."""

    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"
    BOUND = "bound"


class MetricFamily(StrEnum):
    """Typed families for measurable program criteria."""

    ACTIVITY = "activity"
    AFFINITY = "affinity"
    STABILITY = "stability"
    SELECTIVITY = "selectivity"
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
