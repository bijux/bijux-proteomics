# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Decision schema models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from agentic_proteins.core.tooling import ToolInvocationSpec


class DecisionExplanation(BaseModel):
    """DecisionExplanation."""

    model_config = ConfigDict(extra="forbid")

    input_refs: list[str] = Field(
        default_factory=list, description="Inputs used for the decision."
    )
    rules_triggered: list[str] = Field(
        default_factory=list, description="Rules triggered."
    )
    confidence_impact: list[str] = Field(
        default_factory=list, description="Confidence impacts."
    )


class Decision(BaseModel):
    """Decision."""

    model_config = ConfigDict(extra="forbid")

    agent_name: str = Field(
        ..., min_length=1, description="Name of the agent producing the decision."
    )
    rationale: str = Field(
        ..., min_length=1, description="Justification for the decision."
    )
    requested_tools: list[ToolInvocationSpec] = Field(
        default_factory=list,
        description="Tool invocation specs for follow-up steps.",
    )
    next_tasks: list[str] = Field(
        default_factory=list,
        description="Structured next tasks (no free-form text).",
    )
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1.",
    )
    input_refs: list[str] = Field(
        default_factory=list,
        description="Input references used for the decision.",
    )
    memory_refs: list[str] = Field(
        default_factory=list,
        description="Memory record references linked to the decision.",
    )
    rules_triggered: list[str] = Field(
        default_factory=list,
        description="Rules triggered during decision making.",
    )
    confidence_impact: list[str] = Field(
        default_factory=list,
        description="How the decision impacted confidence.",
    )
