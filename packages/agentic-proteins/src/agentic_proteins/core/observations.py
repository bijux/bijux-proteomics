# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Observation and evaluation schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from agentic_proteins.state.schemas import StateSnapshot


class ObservationSource(Enum):
    """ObservationSource."""

    TOOL = "tool"
    EXECUTOR = "executor"


class ObservationMetric(BaseModel):
    """ObservationMetric."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Metric identifier.")
    value: float = Field(0.0, description="Metric value.")
    unit: str = Field(..., min_length=1, description="Metric unit.")


class Observation(BaseModel):
    """Observation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: str = Field(
        ..., min_length=1, description="Observation identifier."
    )
    source: ObservationSource = Field(..., description="Observation source.")
    related_task_id: str = Field(
        ..., min_length=1, description="Related execution task id."
    )
    tool_result_fingerprint: str = Field(
        ..., min_length=1, description="Tool result fingerprint."
    )
    metrics: list[ObservationMetric] = Field(
        default_factory=list, description="Observed metrics."
    )
    confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Observation confidence."
    )
    timestamp: datetime = Field(..., description="Observation timestamp.")


class PlanMetadata(BaseModel):
    """PlanMetadata."""

    model_config = ConfigDict(extra="forbid")

    plan_fingerprint: str = Field(..., min_length=1, description="Plan fingerprint.")
    plan_id: str = Field(..., min_length=1, description="Plan identifier.")


class EvaluationInput(BaseModel):
    """EvaluationInput."""

    model_config = ConfigDict(extra="forbid")

    observations: list[Observation] = Field(
        default_factory=list,
        description="Relevant observations.",
    )
    prior_state: StateSnapshot = Field(
        default_factory=lambda: StateSnapshot(
            state_id="state-0",
            parent_state_id=None,
            plan_fingerprint="unknown",
            timestamp=datetime.now(UTC),
            agent_decisions=[],
            artifacts=[],
            metrics=[],
            confidence_summary=[],
        ),
        description="Prior state snapshot.",
    )
    plan_metadata: PlanMetadata = Field(..., description="Plan metadata.")
    constraints: list[str] = Field(
        default_factory=list, description="Constraint codes."
    )


class ReplanningTriggerType(Enum):
    """ReplanningTriggerType."""

    FAILURE = "failure"
    UNCERTAINTY = "uncertainty"
    IMPROVEMENT = "improvement"


class ReplanningTrigger(BaseModel):
    """ReplanningTrigger."""

    model_config = ConfigDict(extra="forbid")

    trigger_type: ReplanningTriggerType = Field(..., description="Trigger type.")
    source_agent: str = Field(..., min_length=1, description="Triggering agent name.")
    severity: int = Field(0, ge=0, description="Severity level.")
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Supporting evidence ids.",
    )
