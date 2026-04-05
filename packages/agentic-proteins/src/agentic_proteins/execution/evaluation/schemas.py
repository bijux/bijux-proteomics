# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Evaluation schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EvaluationInputs(BaseModel):
    """EvaluationInputs."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1, description="Sequence input.")
    config_refs: list[str] = Field(
        default_factory=list,
        description="Configuration reference identifiers.",
    )


class ExpectedProperty(BaseModel):
    """ExpectedProperty."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Property identifier.")
    min_value: float = Field(0.0, description="Minimum acceptable value.")
    max_value: float = Field(0.0, description="Maximum acceptable value.")
    unit: str = Field(..., min_length=1, description="Property unit.")


class ObservedProperty(BaseModel):
    """ObservedProperty."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Property identifier.")
    value: float = Field(0.0, description="Observed value.")
    unit: str = Field(..., min_length=1, description="Property unit.")


class EvaluationCase(BaseModel):
    """EvaluationCase."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1, description="Evaluation case identifier.")
    description: str = Field("", description="Case description.")
    inputs: EvaluationInputs = Field(..., description="Case inputs.")
    expected_properties: list[ExpectedProperty] = Field(
        default_factory=list,
        description="Expected property assertions.",
    )
    tolerance: float = Field(0.0, ge=0.0, description="Tolerance for comparisons.")
    tags: list[str] = Field(default_factory=list, description="Case tags.")


class EvaluationResult(BaseModel):
    """EvaluationResult."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1, description="Evaluation case identifier.")
    observed_properties: list[ObservedProperty] = Field(
        default_factory=list,
        description="Observed properties.",
    )
    pass_fail: bool = Field(False, description="Whether the case passed.")
    violations: list[str] = Field(default_factory=list, description="Violation codes.")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Result confidence.")
    run_fingerprint: str = Field(
        ..., min_length=1, description="Deterministic run fingerprint."
    )


class AgentScorecard(BaseModel):
    """AgentScorecard."""

    model_config = ConfigDict(extra="forbid")

    agent_name: str = Field(..., min_length=1, description="Agent name.")
    cases: int = Field(0, ge=0, description="Cases evaluated.")
    failure_rate: float = Field(0.0, ge=0.0, le=1.0, description="Failure rate.")
    uncertainty_contribution: float = Field(
        0.0,
        ge=0.0,
        description="Uncertainty contribution.",
    )
    cost_total: float = Field(0.0, ge=0.0, description="Total estimated cost.")
    latency_total_ms: int = Field(0, ge=0, description="Total estimated latency in ms.")


class EvaluationReport(BaseModel):
    """EvaluationReport."""

    model_config = ConfigDict(extra="forbid")

    results: list[EvaluationResult] = Field(
        default_factory=list,
        description="Evaluation results.",
    )
    scorecards: list[AgentScorecard] = Field(
        default_factory=list,
        description="Agent scorecards.",
    )
