# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Evaluation runner and scorecard aggregation."""

from __future__ import annotations

from datetime import datetime
import json

from agentic_proteins.agents.execution.coordinator import CoordinatorAgent
from agentic_proteins.agents.planning.compiler import compile_plan_to_execution
from agentic_proteins.agents.planning.planner import PlannerAgent
from agentic_proteins.agents.schemas import (
    CoordinatorAgentInput,
    CriticAgentInput,
    OutputReference,
    PlannerAgentInput,
    QualityControlAgentInput,
)
from agentic_proteins.agents.verification.critic import CriticAgent
from agentic_proteins.agents.verification.quality_control import QualityControlAgent
from agentic_proteins.core.decisions import Decision
from agentic_proteins.core.execution import (
    ExecutionContext,
    LoopLimits,
    LoopState,
    ResourceLimits,
)
from agentic_proteins.core.hashing import sha256_hex
from agentic_proteins.core.observations import EvaluationInput, PlanMetadata
from agentic_proteins.domain.candidates.schema import Candidate
from agentic_proteins.execution.compiler.boundary import ExecutionBoundary
from agentic_proteins.execution.evaluation.schemas import (
    AgentScorecard,
    EvaluationCase,
    EvaluationReport,
    EvaluationResult,
    ObservedProperty,
)
from agentic_proteins.execution.runtime.executor import (
    LocalExecutor,
    materialize_observation,
)
from agentic_proteins.registry.agents import AgentRegistry
from agentic_proteins.state.schemas import StateSnapshot
from agentic_proteins.tools.heuristic import HeuristicStructureTool
from agentic_proteins.tools.schemas import InvocationInput, ToolInvocationSpec


class HeuristicBoundary(ExecutionBoundary):
    """HeuristicBoundary."""

    def __init__(self) -> None:
        """__init__."""
        self._tool = HeuristicStructureTool()

    def execute(self, invocation: ToolInvocationSpec):
        """execute."""
        return self._tool.run(invocation.invocation_id, invocation.inputs)


class EvaluationRunner:
    """EvaluationRunner."""

    def __init__(self, boundary: ExecutionBoundary) -> None:
        """__init__."""
        self._executor = LocalExecutor(boundary)

    def run(self, cases: list[EvaluationCase]) -> EvaluationReport:
        """run."""
        results: list[EvaluationResult] = []
        scorecard_inputs: dict[str, list[dict]] = {}

        for case in cases:
            if not AgentRegistry.list():
                raise ValueError("AgentRegistry must be populated before evaluation.")

            planner = PlannerAgent()
            plan_decision = planner.decide(PlannerAgentInput(goal=case.description))
            plan = plan_decision.plan

            task_id = plan.entry_tasks[0]
            inputs = [InvocationInput(name="sequence", value=case.inputs.sequence)]
            if "force_failure" in case.inputs.config_refs:
                inputs.append(InvocationInput(name="mode", value="fail"))
            invocation = ToolInvocationSpec(
                invocation_id=f"{case.case_id}-invocation",
                tool_name=HeuristicStructureTool.name,
                tool_version=HeuristicStructureTool.version,
                inputs=inputs,
                expected_outputs=[],
                constraints=[],
                origin_task_id=task_id,
            )
            decision = Decision(
                agent_name="structure",
                rationale="evaluate_case",
                requested_tools=[invocation],
                next_tasks=["execute"],
                confidence=0.5,
                input_refs=[f"sequence:{case.case_id}"],
                memory_refs=["memory:evaluation"],
                rules_triggered=["evaluation_case"],
                confidence_impact=["baseline_assumed"],
            )
            graph = compile_plan_to_execution(plan, [decision])
            execution_task = graph.tasks[task_id]
            initial_state = StateSnapshot(
                state_id=f"state-{case.case_id}",
                parent_state_id=None,
                plan_fingerprint=plan.fingerprint(),
                timestamp=datetime(2025, 1, 1, 0, 0, 0),
                agent_decisions=[],
                artifacts=[],
                metrics=[],
                confidence_summary=[],
            )
            context = ExecutionContext(
                execution_id=f"exec-{case.case_id}",
                plan_fingerprint=plan.fingerprint(),
                initial_state=initial_state,
                memory_snapshot=[],
                resource_limits=ResourceLimits(),
            )

            result = self._executor.run(execution_task, context)
            observation = materialize_observation(result, execution_task)
            metrics = _metrics_from_outputs(result.outputs)

            evaluation_input = EvaluationInput(
                observations=[observation],
                prior_state=initial_state,
                plan_metadata=PlanMetadata(
                    plan_fingerprint=plan.fingerprint(),
                    plan_id=case.case_id,
                ),
                constraints=[],
            )
            qc = QualityControlAgent()
            candidate = Candidate(
                candidate_id=case.case_id,
                sequence=case.inputs.sequence,
                metrics=metrics,
                provenance={"evaluation_case": case.case_id},
            )
            qc_output = qc.decide(
                QualityControlAgentInput(
                    evaluation=evaluation_input, candidate=candidate
                )
            )
            critic = CriticAgent()
            critic_output = critic.decide(
                CriticAgentInput(
                    critic_name="critic",
                    target_agent_name="quality_control",
                    target_output=OutputReference(
                        agent_name="quality_control",
                        output_id=f"{case.case_id}-qc",
                        schema_version="1.0",
                    ),
                    prior_decisions=[],
                    qc_output=qc_output,
                    observations=[observation],
                )
            )
            coordinator = CoordinatorAgent()
            coordinator_output = coordinator.decide(
                CoordinatorAgentInput(
                    decisions=[],
                    observations=[observation],
                    qc_output=qc_output,
                    critic_output=critic_output,
                    replanning_trigger=None,
                    loop_limits=LoopLimits(
                        max_replans=1, max_executions_per_plan=1, max_uncertainty=1.0
                    ),
                    loop_state=LoopState(replans=0, executions=1, uncertainty=0.0),
                )
            )

            observed_properties = [
                ObservedProperty(name=m.name, value=m.value, unit=m.unit)
                for m in observation.metrics
            ]
            observed_properties.append(
                ObservedProperty(
                    name="status_success",
                    value=1.0 if result.status == "success" else 0.0,
                    unit="bool",
                )
            )
            violations: list[str] = []
            if result.status != "success":
                violations.append("tool_failure")
            observed_map = {p.name: p for p in observed_properties}
            for expected in case.expected_properties:
                observed = observed_map.get(expected.name)
                if observed is None:
                    violations.append(f"missing_property:{expected.name}")
                    continue
                min_allowed = expected.min_value - case.tolerance
                max_allowed = expected.max_value + case.tolerance
                if not (min_allowed <= observed.value <= max_allowed):
                    violations.append(f"out_of_bounds:{expected.name}")
            pass_fail = not violations
            confidence = (
                1.0
                if not case.expected_properties
                else max(
                    0.0,
                    1.0 - (len(violations) / len(case.expected_properties)),
                )
            )
            fingerprint_payload = json.dumps(
                {
                    "case_id": case.case_id,
                    "plan_fingerprint": plan.fingerprint(),
                    "tool_result_fingerprint": result.fingerprint(
                        tool_version=invocation.tool_version,
                        inputs=invocation.inputs,
                    ),
                    "decision": coordinator_output.decision.value,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            run_fingerprint = sha256_hex(fingerprint_payload)

            results.append(
                EvaluationResult(
                    case_id=case.case_id,
                    observed_properties=observed_properties,
                    pass_fail=pass_fail,
                    violations=violations,
                    confidence=confidence,
                    run_fingerprint=run_fingerprint,
                )
            )

            scorecard_inputs.setdefault("quality_control", []).append(
                {
                    "failure": qc_output.status in {"reject", "needs_human"},
                    "uncertainty": sum(
                        abs(m.value) for m in qc_output.confidence_deltas
                    ),
                }
            )
            scorecard_inputs.setdefault("critic", []).append(
                {
                    "failure": critic_output.blocking,
                    "uncertainty": 1.0 if critic_output.blocking else 0.0,
                }
            )
            scorecard_inputs.setdefault("coordinator", []).append(
                {
                    "failure": coordinator_output.decision.value != "ContinueExecution",
                    "uncertainty": 0.0,
                }
            )
            scorecard_inputs.setdefault("planner", []).append(
                {"failure": False, "uncertainty": 0.0}
            )

        scorecards = _aggregate_scorecards(scorecard_inputs)
        return EvaluationReport(results=results, scorecards=scorecards)


def _aggregate_scorecards(per_agent: dict[str, list[dict]]) -> list[AgentScorecard]:
    """_aggregate_scorecards."""
    scorecards: list[AgentScorecard] = []
    for agent_name, items in sorted(per_agent.items()):
        cases = len(items)
        failure_count = sum(1 for item in items if item["failure"])
        uncertainty_total = sum(float(item["uncertainty"]) for item in items)
        try:
            agent_cls = AgentRegistry.get(agent_name)
            cost_total = agent_cls.cost_budget * cases
            latency_total = agent_cls.latency_budget_ms * cases
        except KeyError:
            cost_total = 0.0
            latency_total = 0
        scorecards.append(
            AgentScorecard(
                agent_name=agent_name,
                cases=cases,
                failure_rate=(failure_count / cases) if cases else 0.0,
                uncertainty_contribution=(uncertainty_total / cases) if cases else 0.0,
                cost_total=cost_total,
                latency_total_ms=latency_total,
            )
        )
    return scorecards


def _metrics_from_outputs(outputs: list[InvocationInput]) -> dict[str, float]:
    """_metrics_from_outputs."""
    metrics: dict[str, float] = {}
    for item in outputs:
        try:
            metrics[item.name] = float(item.value)
        except (TypeError, ValueError):
            continue
    return metrics


def evaluate_execution(
    cases: list[EvaluationCase],
    boundary: ExecutionBoundary | None = None,
) -> EvaluationReport:
    """evaluate_execution."""
    runner = EvaluationRunner(boundary or HeuristicBoundary())
    return runner.run(cases)
