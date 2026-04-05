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


class SuccessCriterion(BaseModel):
    """Condition required for a program to advance."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: EvidenceId = Field(..., description="Stable criterion identifier.")
    metric: str = Field(..., min_length=1, description="Metric to evaluate.")
    direction: MeasurementDirection = Field(..., description="Optimization direction.")
    threshold: float = Field(..., description="Threshold for the metric.")
    unit: str | None = Field(default=None, description="Optional measurement unit.")
