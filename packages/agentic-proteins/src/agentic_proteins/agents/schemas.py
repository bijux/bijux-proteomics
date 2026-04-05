# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Agent-related schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from agentic_proteins.agents.planning.schemas import PlanDecision
from agentic_proteins.core.decisions import Decision, DecisionExplanation
from agentic_proteins.core.observations import (
    EvaluationInput,
    Observation,
    ReplanningTrigger,
)
from agentic_proteins.domain.candidates.schema import Candidate
from agentic_proteins.domain.metrics.quality import (
    MetricValue,
    QCStatus,
    ToolReliability,
)
from agentic_proteins.memory.schemas import MemoryScope


class AgentMetadata(BaseModel):
    """AgentMetadata."""

    model_config = ConfigDict(extra="forbid")

    agent_name: str = Field(..., min_length=1, description="Agent identifier.")
    version: str = Field(..., min_length=1, description="Agent schema version.")
    capabilities: list[str] = Field(
        default_factory=list, description="Declared capabilities."
    )
    allowed_tools: list[str] = Field(
        default_factory=list, description="Declared tool allowlist."
    )
    cost_budget: float = Field(1.0, gt=0.0, description="Cost budget.")
    latency_budget_ms: int = Field(1, gt=0, description="Latency budget in ms.")
    read_scopes: list[MemoryScope] = Field(
        default_factory=list,
        description="Readable memory scopes.",
    )
    write_scopes: list[MemoryScope] = Field(
        default_factory=list,
        description="Writable memory scopes.",
    )


class OutputReference(BaseModel):
    """OutputReference."""

    model_config = ConfigDict(extra="forbid")

    agent_name: str = Field(..., min_length=1, description="Source agent name.")
    output_id: str = Field(
        ..., min_length=1, description="Identifier for the output payload."
    )
    schema_version: str = Field(..., min_length=1, description="Output schema version.")


class RequestParameter(BaseModel):
    """RequestParameter."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Parameter identifier.")
    value: str = Field(..., min_length=1, description="Parameter value.")


class StructureConstraint(BaseModel):
    """StructureConstraint."""

    model_config = ConfigDict(extra="forbid")

    constraint_type: str = Field(
        ..., min_length=1, description="Constraint identifier."
    )
    value: str = Field(..., min_length=1, description="Constraint value.")


class OrchestrationStep(BaseModel):
    """OrchestrationStep."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1, description="Step identifier.")
    decision_agent: str = Field(
        ..., min_length=1, description="Agent associated with the decision."
    )
    action_code: str = Field(
        ..., min_length=1, description="Machine-actionable orchestration code."
    )


class PlannerAgentInput(BaseModel):
    """PlannerAgentInput."""

    model_config = ConfigDict(extra="forbid")

    goal: str = Field("", description="High-level objective for planning.")
    constraints: list[str] = Field(
        default_factory=list, description="Planning constraints."
    )


class PlannerAgentOutput(PlanDecision):
    """Planner output schema alias."""


class SequenceAnalysisAgentInput(BaseModel):
    """SequenceAnalysisAgentInput."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1, description="Protein sequence input.")
    sequence_id: str = Field(..., min_length=1, description="Sequence identifier.")
    requested_checks: list[str] = Field(
        default_factory=list,
        description="Named checks like validation or motif detection.",
    )


class SequenceAnalysisAgentOutput(BaseModel):
    """SequenceAnalysisAgentOutput."""

    model_config = ConfigDict(extra="forbid")

    validated: bool = Field(False, description="Whether sequence passes validation.")
    detected_motifs: list[str] = Field(
        default_factory=list,
        description="Detected motif identifiers.",
    )
    issues: list[str] = Field(
        default_factory=list, description="Structured issue codes."
    )
    metrics: list[MetricValue] = Field(
        default_factory=list,
        description="Structured metrics from sequence analysis.",
    )


class InputValidationAgentInput(BaseModel):
    """InputValidationAgentInput."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1, description="Protein sequence input.")
    sequence_id: str = Field(..., min_length=1, description="Sequence identifier.")


class InputValidationAgentOutput(BaseModel):
    """InputValidationAgentOutput."""

    model_config = ConfigDict(extra="forbid")

    valid: bool = Field(False, description="Whether the input is valid.")
    warnings: list[str] = Field(default_factory=list, description="Warning codes.")
    errors: list[str] = Field(default_factory=list, description="Error codes.")


class StructureAgentInput(BaseModel):
    """StructureAgentInput."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1, description="Protein sequence input.")
    model_preferences: list[str] = Field(
        default_factory=list,
        description="Preferred model identifiers.",
    )
    constraints: list[StructureConstraint] = Field(
        default_factory=list,
        description="Structured constraints.",
    )


class StructureAgentOutput(BaseModel):
    """StructureAgentOutput."""

    model_config = ConfigDict(extra="forbid")

    selected_model: str = Field(
        ..., min_length=1, description="Chosen provider identifier."
    )
    request_parameters: list[RequestParameter] = Field(
        default_factory=list,
        description="Structured request parameters for a provider.",
    )
    rationale_codes: list[str] = Field(
        default_factory=list,
        description="Structured reasons for model selection.",
    )


class QualityControlAgentInput(BaseModel):
    """QualityControlAgentInput."""

    model_config = ConfigDict(extra="forbid")
    evaluation: EvaluationInput = Field(..., description="Evaluation input bundle.")
    candidate: Candidate = Field(..., description="Candidate under evaluation.")


class QualityControlAgentOutput(BaseModel):
    """QualityControlAgentOutput."""

    model_config = ConfigDict(extra="forbid")
    status: QCStatus = Field(QCStatus.ACCEPTABLE, description="QC status.")
    confidence_deltas: list[MetricValue] = Field(
        default_factory=list,
        description="Confidence deltas.",
    )
    constraint_violations: list[str] = Field(
        default_factory=list,
        description="Constraint violations.",
    )


class CriticAgentInput(BaseModel):
    """CriticAgentInput."""

    model_config = ConfigDict(extra="forbid")

    critic_name: str = Field(..., min_length=1, description="Name of the critic agent.")
    target_agent_name: str = Field(
        ..., min_length=1, description="Name of the agent being reviewed."
    )
    target_output: OutputReference = Field(
        ..., description="Reference to another agent output."
    )
    prior_decisions: list[Decision] = Field(
        default_factory=list,
        description="Decisions from other agents only.",
    )
    qc_output: QualityControlAgentOutput = Field(
        default_factory=QualityControlAgentOutput,
        description="Quality control findings.",
    )
    observations: list[Observation] = Field(
        default_factory=list,
        description="Relevant observations.",
    )
    tool_reliability: ToolReliability | None = Field(
        default=None,
        description="Tool reliability summary.",
    )


class CriticAgentOutput(BaseModel):
    """CriticAgentOutput."""

    model_config = ConfigDict(extra="forbid")
    blocking: bool = Field(False, description="Whether to block continuation.")
    inconsistencies: list[str] = Field(
        default_factory=list,
        description="Inconsistency codes.",
    )
    notes: list[str] = Field(default_factory=list, description="Advisory notes.")
    explanation: DecisionExplanation = Field(
        default_factory=DecisionExplanation,
        description="Decision explanation.",
    )


class FailureAnalysisAgentInput(BaseModel):
    """FailureAnalysisAgentInput."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(..., min_length=1, description="Tool name.")
    status: str = Field(..., min_length=1, description="Tool status.")
    error_type: str = Field(..., min_length=1, description="Error type code.")
    error_message: str = Field(..., min_length=1, description="Error message code.")


class FailureAnalysisAgentOutput(BaseModel):
    """FailureAnalysisAgentOutput."""

    model_config = ConfigDict(extra="forbid")

    failure_type: str = Field(..., min_length=1, description="Failure classification.")
    metadata: list[str] = Field(default_factory=list, description="Metadata codes.")
    replan_recommended: bool = Field(False, description="Whether to replan.")


class CoordinatorAgentInput(BaseModel):
    """CoordinatorAgentInput."""

    model_config = ConfigDict(extra="forbid")

    decisions: list[Decision] = Field(
        default_factory=list,
        description="Decisions from other agents only.",
    )
    observations: list[Observation] = Field(
        default_factory=list,
        description="Observations from execution.",
    )
    qc_output: QualityControlAgentOutput = Field(
        default_factory=QualityControlAgentOutput,
        description="Quality control findings.",
    )
    critic_output: CriticAgentOutput = Field(
        default_factory=CriticAgentOutput,
        description="Critic findings.",
    )
    replanning_trigger: ReplanningTrigger | None = Field(
        default=None,
        description="Optional replanning trigger.",
    )
    loop_limits: LoopLimits = Field(
        default_factory=lambda: LoopLimits(),
        description="Loop limits.",
    )
    loop_state: LoopState = Field(
        default_factory=lambda: LoopState(),
        description="Loop state.",
    )


class CoordinatorDecisionType(Enum):
    """CoordinatorDecisionType."""

    CONTINUE = "ContinueExecution"
    REPLAN = "RequestReplan"
    TERMINATE = "TerminateRun"


class CoordinatorAgentOutput(BaseModel):
    """CoordinatorAgentOutput."""

    model_config = ConfigDict(extra="forbid")

    decision: CoordinatorDecisionType = Field(
        CoordinatorDecisionType.CONTINUE,
        description="Coordinator decision.",
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Decision reason codes.",
    )
    replanning_trigger: ReplanningTrigger | None = Field(
        default=None,
        description="Replanning trigger if applicable.",
    )
    stop_reason: str = Field(..., min_length=1, description="Why the loop stopped.")
    thresholds_hit: list[str] = Field(
        default_factory=list, description="Thresholds that triggered stop."
    )
    confidence_plateau: bool = Field(False, description="Whether confidence plateaued.")
    explanation: DecisionExplanation = Field(
        default_factory=DecisionExplanation,
        description="Decision explanation.",
    )


class ReportingAgentInput(BaseModel):
    """ReportingAgentInput."""

    model_config = ConfigDict(extra="forbid")

    tool_outputs: list[RequestParameter] = Field(
        default_factory=list,
        description="Tool outputs used for reporting.",
    )
    qc_status: QCStatus = Field(
        QCStatus.ACCEPTABLE, description="Quality control status."
    )
    decision: str = Field(..., min_length=1, description="Coordinator decision.")


class ReportingAgentOutput(BaseModel):
    """ReportingAgentOutput."""

    model_config = ConfigDict(extra="forbid")

    summary: dict = Field(default_factory=dict, description="Summary report payload.")
    confidence_statement: str = Field(
        "", description="Structured confidence statement."
    )
    artifact_refs: list[str] = Field(
        default_factory=list, description="Artifact references."
    )


from agentic_proteins.core.execution import LoopLimits, LoopState  # noqa: E402
