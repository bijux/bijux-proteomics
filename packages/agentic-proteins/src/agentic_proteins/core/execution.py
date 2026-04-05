# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Core execution graph schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from agentic_proteins.core.tooling import ToolInvocationSpec
from agentic_proteins.state.schemas import StateSnapshot


class RetryPolicy(BaseModel):
    """RetryPolicy."""

    model_config = ConfigDict(extra="forbid")

    max_retries: int = Field(0, ge=0, description="Maximum retry attempts.")
    backoff_ms: int = Field(0, ge=0, description="Backoff duration in ms.")
    retry_on: list[str] = Field(
        default_factory=list, description="Error codes to retry."
    )


class ExecutionTask(BaseModel):
    """ExecutionTask."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., min_length=1, description="Execution task identifier.")
    tool_invocation: ToolInvocationSpec = Field(
        ..., description="Tool invocation spec."
    )
    input_state_id: str = Field(
        ..., min_length=1, description="Input state identifier."
    )
    expected_output_schema: str = Field(
        ..., min_length=1, description="Expected output schema id."
    )
    retry_policy: RetryPolicy = Field(
        default_factory=RetryPolicy,
        description="Retry policy.",
    )
    timeout_ms: int = Field(0, ge=0, description="Timeout in ms.")


class ExecutionGraph(BaseModel):
    """ExecutionGraph."""

    model_config = ConfigDict(extra="forbid")

    tasks: dict[str, ExecutionTask] = Field(
        default_factory=dict, description="Task map."
    )
    dependencies: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Task dependency map.",
    )
    entry_tasks: list[str] = Field(default_factory=list, description="Entry task ids.")
    exit_conditions: list[str] = Field(
        default_factory=list, description="Exit conditions."
    )


class LoopLimits(BaseModel):
    """LoopLimits."""

    model_config = ConfigDict(extra="forbid")

    max_replans: int = Field(0, ge=0, description="Max replans per run.")
    max_executions_per_plan: int = Field(
        0, ge=0, description="Max executions per plan."
    )
    max_uncertainty: float = Field(
        0.0, ge=0.0, description="Max uncertainty tolerance."
    )


class LoopState(BaseModel):
    """LoopState."""

    model_config = ConfigDict(extra="forbid")

    replans: int = Field(0, ge=0, description="Replans so far.")
    executions: int = Field(0, ge=0, description="Executions for current plan.")
    uncertainty: float = Field(0.0, ge=0.0, description="Current uncertainty level.")
    iteration_index: int = Field(0, ge=0, description="Iteration index.")
    stopping_criteria: list[str] = Field(
        default_factory=list, description="Stopping criteria met."
    )
    improvement_delta: float = Field(
        0.0, description="Improvement delta since prior iteration."
    )


class ResourceLimits(BaseModel):
    """ResourceLimits."""

    model_config = ConfigDict(extra="forbid")

    max_concurrent_tasks: int = Field(1, ge=1, description="Concurrency limit.")
    max_task_runtime_ms: int = Field(0, ge=0, description="Max per-task runtime.")
    max_total_cost: float = Field(0.0, ge=0.0, description="Max total cost.")
    cpu_seconds: float = Field(0.0, ge=0.0, description="CPU seconds budget.")
    gpu_seconds: float = Field(0.0, ge=0.0, description="GPU seconds budget.")


class ExecutionContext(BaseModel):
    """ExecutionContext."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    execution_id: str = Field(..., min_length=1, description="Execution identifier.")
    plan_fingerprint: str = Field(..., min_length=1, description="Plan fingerprint.")
    initial_state: StateSnapshot = Field(..., description="Initial state snapshot.")
    memory_snapshot: list[str] = Field(
        default_factory=list,
        description="Memory snapshot record ids.",
    )
    resource_limits: ResourceLimits = Field(
        default_factory=ResourceLimits,
        description="Execution resource limits.",
    )
