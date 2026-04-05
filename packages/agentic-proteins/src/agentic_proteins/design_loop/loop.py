# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Iterative design loop for candidate refinement."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

from agentic_proteins.agents.schemas import CoordinatorDecisionType
from agentic_proteins.core.execution import LoopState
from agentic_proteins.design_loop.convergence import is_convergence_failure
from agentic_proteins.design_loop.stagnation import update_stagnation_count
from agentic_proteins.domain.candidates.schema import Candidate
from agentic_proteins.domain.metrics.quality import QCStatus


class PipelineResultProtocol(Protocol):
    """PipelineResultProtocol."""

    candidate: Candidate
    tool_status: str
    qc_status: QCStatus
    timings: dict[str, float]
    tool_result: object | None
    coordinator_decision: CoordinatorDecisionType
    failure_type: str


class PipelineRunner(Protocol):
    """PipelineRunner."""

    def run_iteration(
        self, candidate: Candidate, loop_state: LoopState
    ) -> PipelineResultProtocol:
        """Run one loop iteration for a candidate."""
        ...


class LoopAction(str, Enum):
    """LoopAction."""

    CONTINUE = "continue"
    MUTATE = "mutate"
    STOP = "stop"


@dataclass
class LoopDecision:
    """LoopDecision."""

    action: LoopAction
    reason: str


class LoggerProtocol(Protocol):
    """LoggerProtocol."""

    def log(self, **_kwargs: Any) -> None:  # noqa: ANN401
        """log."""
        ...


class TelemetryProtocol(Protocol):
    """TelemetryProtocol."""

    cost: dict[str, float]


class AnalysisProtocol(Protocol):
    """AnalysisProtocol."""

    def record_candidate_event(
        self, candidate_id: str, event: str, payload: dict[str, Any]
    ) -> None:
        """Record a candidate lifecycle event."""
        ...

    def record_tool_result(
        self, tool_name: str, status: str, duration_ms: float
    ) -> None:
        """Record tool execution outcome and latency."""
        ...

    def record_iteration_delta(
        self, iteration_index: int, improvement_delta: float, score: float | None
    ) -> None:
        """Record iteration improvement delta."""
        ...

    def write(self, path: Path) -> None:
        """Persist analysis summary to disk."""
        ...


@dataclass(frozen=True)
class LoopContext:
    """LoopContext."""

    config: dict[str, Any]
    telemetry: TelemetryProtocol
    logger: LoggerProtocol
    analysis_path: Path


class LoopRunner:
    """LoopRunner."""

    def __init__(
        self,
        loop_context: LoopContext,
        pipeline: PipelineRunner,
        analysis: AnalysisProtocol,
    ) -> None:
        """__init__."""
        self._context = loop_context
        self._pipeline = pipeline
        self._analysis = analysis
        self._logger = loop_context.logger

    def run(self, candidate: Candidate) -> PipelineResultProtocol:
        """run."""
        max_iterations = int(self._context.config.get("loop_max_iterations", 1))
        stagnation_window = int(self._context.config.get("loop_stagnation_window", 2))
        improvement_threshold = float(
            self._context.config.get("loop_improvement_threshold", 0.5)
        )
        max_cost = float(self._context.config.get("loop_max_cost", 1.0))
        loop_state = LoopState(
            replans=0,
            executions=0,
            uncertainty=0.0,
            iteration_index=0,
            stopping_criteria=[],
            improvement_delta=0.0,
        )
        last_score: float | None = None
        result: PipelineResultProtocol | None = None
        stagnation_count = 0
        self._analysis.record_candidate_event(
            candidate.candidate_id,
            "loop_start",
            {"sequence_length": len(candidate.sequence)},
        )

        for idx in range(max_iterations):
            loop_state.iteration_index = idx
            result = self._pipeline.run_iteration(candidate, loop_state)
            candidate = result.candidate
            loop_state.executions += 1

            self._analysis.record_candidate_event(
                candidate.candidate_id,
                "iteration_complete",
                {
                    "iteration_index": idx,
                    "tool_status": result.tool_status,
                    "qc_status": result.qc_status,
                },
            )
            if result.timings.get("tool_invocation_ms") is not None:
                self._analysis.record_tool_result(
                    getattr(result.tool_result, "tool_name", "unknown"),
                    result.tool_status,
                    result.timings.get("tool_invocation_ms", 0.0),
                )

            score = candidate.metrics.get("mean_plddt")
            if score is not None and last_score is not None:
                loop_state.improvement_delta = float(score) - float(last_score)
            else:
                loop_state.improvement_delta = 0.0
            if score is not None:
                last_score = float(score)
            self._analysis.record_iteration_delta(
                idx, loop_state.improvement_delta, score
            )
            stagnation_count = update_stagnation_count(
                stagnation_count, loop_state.improvement_delta, improvement_threshold
            )

            stopping = []
            if result.tool_status != "success":
                stopping.append("tool_failure")
            if result.qc_status is QCStatus.REJECT:
                stopping.append("qc_reject")
            if self._context.telemetry.cost.get("tool_units", 0.0) > max_cost:
                stopping.append("max_cost")
            if stagnation_count >= stagnation_window:
                stopping.append("stagnation")
            if idx >= max_iterations - 1:
                stopping.append("max_iterations")
            loop_state.stopping_criteria = stopping

            decision = self._decide_next(result, stopping)
            self._log_loop_iteration(
                candidate.candidate_id,
                idx,
                decision.action,
                decision.reason,
                loop_state.improvement_delta,
                stopping,
            )

            if decision.action is LoopAction.MUTATE:
                loop_state.replans += 1
                candidate.flags.append("mutate_requested")
                continue
            if decision.action is LoopAction.STOP:
                if is_convergence_failure(stopping):
                    result.failure_type = "convergence_failure"
                break

        self._analysis.record_candidate_event(candidate.candidate_id, "loop_end", {})
        self._analysis.write(self._context.analysis_path)
        return result  # type: ignore[return-value]

    @staticmethod
    def _decide_next(
        result: PipelineResultProtocol, stopping: list[str]
    ) -> LoopDecision:
        """_decide_next."""
        if stopping:
            return LoopDecision(LoopAction.STOP, ",".join(stopping))
        if result.coordinator_decision is CoordinatorDecisionType.REPLAN:
            return LoopDecision(LoopAction.MUTATE, "coordinator_replan")
        if result.coordinator_decision is CoordinatorDecisionType.TERMINATE:
            return LoopDecision(LoopAction.STOP, "coordinator_terminate")
        return LoopDecision(LoopAction.CONTINUE, "coordinator_continue")

    def _log_loop_iteration(
        self,
        candidate_id: str,
        iteration_index: int,
        decision: LoopAction,
        reason: str,
        improvement_delta: float,
        stopping_criteria: list[str],
    ) -> None:
        """_log_loop_iteration."""
        self._logger.log(
            component="iteration",
            event="loop_iteration",
            status=decision.value,
            duration_ms=0.0,
            candidate_id=candidate_id,
            iteration_index=iteration_index,
            improvement_delta=round(improvement_delta, 3),
            stopping_criteria=stopping_criteria,
            reason=reason,
            timestamp=datetime.now(UTC).isoformat(),
        )
