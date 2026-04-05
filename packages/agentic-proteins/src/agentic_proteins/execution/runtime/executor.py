# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Executor interfaces and local executor."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
import time

from agentic_proteins.core.hashing import sha256_hex
from agentic_proteins.core.observations import (
    Observation,
    ObservationMetric,
    ObservationSource,
)
from agentic_proteins.execution.compiler.boundary import ExecutionBoundary
from agentic_proteins.execution.schemas import (
    ExecutionContext,
    ExecutionTask,
    ExecutionTrace,
)
from agentic_proteins.tools.schemas import ToolError, ToolResult


def build_trace(
    task: ExecutionTask,
    status: str,
    started_at: float,
    finished_at: float,
    observed_cost: float,
) -> ExecutionTrace:
    """build_trace."""
    return ExecutionTrace(
        task_id=task.task_id,
        tool_name=task.tool_invocation.tool_name,
        status=status,
        started_at=datetime.fromtimestamp(started_at).isoformat(),
        finished_at=datetime.fromtimestamp(finished_at).isoformat(),
        observed_cost=observed_cost,
        observed_latency_ms=int((finished_at - started_at) * 1000),
        result=None,
    )


def materialize_observation(result: ToolResult, task: ExecutionTask) -> Observation:
    """materialize_observation."""
    fingerprint = result.fingerprint(
        tool_version=task.tool_invocation.tool_version,
        inputs=task.tool_invocation.inputs,
    )
    observation_id = sha256_hex(
        f"{fingerprint}:{task.task_id}:{task.tool_invocation.tool_name}"
    )
    metrics = [
        ObservationMetric(name=m.name, value=m.value, unit=m.unit)
        for m in result.metrics
    ]
    return Observation(
        observation_id=observation_id,
        source=ObservationSource.TOOL,
        related_task_id=task.task_id,
        tool_result_fingerprint=fingerprint,
        metrics=metrics,
        confidence=0.0,
        timestamp=datetime.now(UTC),
    )


class Executor(ABC):
    """Executor."""

    @abstractmethod
    def run(self, task: ExecutionTask, context: ExecutionContext) -> ToolResult:
        """Run a single execution task."""


class LocalExecutor(Executor):
    """LocalExecutor."""

    def __init__(self, boundary: ExecutionBoundary | None = None) -> None:
        """Create a local executor with an optional boundary."""
        self._boundary = boundary

    def run(self, task: ExecutionTask, context: ExecutionContext) -> ToolResult:
        """Execute a task locally and capture timeout failures."""
        start = time.time()
        timeout_s = task.timeout_ms / 1000.0 if task.timeout_ms else None
        if timeout_s is not None:
            elapsed = time.time() - start
            if elapsed > timeout_s:
                build_trace(task, "failure", start, time.time(), 0.0)
                return ToolResult(
                    invocation_id=task.tool_invocation.invocation_id,
                    tool_name=task.tool_invocation.tool_name,
                    status="failure",
                    outputs=[],
                    metrics=[],
                    error=ToolError(
                        error_type="timeout", message="timeout_before_start"
                    ),
                )
        if self._boundary is None:
            result = ToolResult(
                invocation_id=task.tool_invocation.invocation_id,
                tool_name=task.tool_invocation.tool_name,
                status="failure",
                outputs=[],
                metrics=[],
                error=ToolError(
                    error_type="no_boundary", message="execution_boundary_missing"
                ),
            )
        else:
            result = self._boundary.execute(task.tool_invocation)
        elapsed = time.time() - start
        if timeout_s is not None and elapsed > timeout_s:
            result = ToolResult(
                invocation_id=task.tool_invocation.invocation_id,
                tool_name=task.tool_invocation.tool_name,
                status="failure",
                outputs=[],
                metrics=[],
                error=ToolError(error_type="timeout", message="timeout_exceeded"),
            )
        build_trace(task, result.status, start, time.time(), 0.0)
        return result
