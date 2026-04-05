# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Quality and metric schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MetricValue(BaseModel):
    """MetricValue."""

    model_config = ConfigDict(extra="forbid")

    metric_name: str = Field(..., min_length=1, description="Metric identifier.")
    value: float = Field(0.0, description="Metric value.")
    unit: str = Field(..., min_length=1, description="Unit identifier.")


class ConfidenceVector(BaseModel):
    """ConfidenceVector."""

    model_config = ConfigDict(extra="forbid")

    structural: float = Field(0.0, ge=0.0, le=1.0, description="Structural confidence.")
    functional: float = Field(0.0, ge=0.0, le=1.0, description="Functional confidence.")
    computational: float = Field(
        0.0, ge=0.0, le=1.0, description="Computational confidence."
    )
    empirical: float = Field(0.0, ge=0.0, le=1.0, description="Empirical confidence.")


class ToolReliability(BaseModel):
    """ToolReliability."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(..., min_length=1, description="Tool name.")
    success_rate: float = Field(0.0, ge=0.0, le=1.0, description="Success rate.")
    latency_p50_ms: float = Field(0.0, ge=0.0, description="Median latency (ms).")
    latency_p95_ms: float = Field(
        0.0, ge=0.0, description="95th percentile latency (ms)."
    )
    latency_variance: float = Field(0.0, ge=0.0, description="Latency variance.")
    sample_count: int = Field(0, ge=0, description="Number of samples.")


class QCStatus(str, Enum):
    """QCStatus."""

    ACCEPTABLE = "acceptable"
    NEEDS_HUMAN = "needs_human"
    REJECT = "reject"
    SKIPPED = "skipped"
