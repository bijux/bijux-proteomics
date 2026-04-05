# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime

from agentic_proteins.agents.execution.coordinator import CoordinatorAgent
from agentic_proteins.agents.verification.critic import CriticAgent
from agentic_proteins.agents.analysis.failure_analysis import FailureAnalysisAgent
from agentic_proteins.agents.verification.input_validation import InputValidationAgent
from agentic_proteins.agents.planning.planner import PlannerAgent
from agentic_proteins.agents.verification.quality_control import QualityControlAgent
from agentic_proteins.agents.reporting.reporting import ReportingAgent
from agentic_proteins.agents.planning.compiler import compile_plan_to_execution
from agentic_proteins.execution.compiler.boundary import ExecutionBoundary
from agentic_proteins.execution.runtime.executor import LocalExecutor
from agentic_proteins.execution.runtime.executor import materialize_observation
from agentic_proteins.registry.agents import AgentRegistry
from agentic_proteins.registry.tools import ToolRegistry
from agentic_proteins.agents.schemas import (
    CoordinatorAgentInput,
    CriticAgentInput,
    PlannerAgentInput,
    QualityControlAgentInput,
    QualityControlAgentOutput,
    OutputReference,
)
from agentic_proteins.core.decisions import Decision
from agentic_proteins.core.execution import ExecutionContext, LoopLimits, LoopState, ResourceLimits
from agentic_proteins.core.observations import EvaluationInput, PlanMetadata
from agentic_proteins.state.schemas import StateSnapshot
from agentic_proteins.domain.candidates.schema import Candidate
from agentic_proteins.tools.schemas import (
    InvocationInput,
    OutputExpectation,
    SchemaDefinition,
    ToolContract,
    ToolDeterminism,
    ToolInvocationSpec,
    ToolResult,
)
from agentic_proteins.tools.heuristic import HeuristicStructureTool


class DummyBoundary(ExecutionBoundary):
    def execute(self, invocation: ToolInvocationSpec) -> ToolResult:
        tool = HeuristicStructureTool()
        return tool.run(invocation.invocation_id, invocation.inputs)


def register_agents() -> None:
    AgentRegistry._registry.clear()
    AgentRegistry._locked = False
    AgentRegistry.register(InputValidationAgent)
    AgentRegistry.register(PlannerAgent)
    AgentRegistry.register(QualityControlAgent)
    AgentRegistry.register(CriticAgent)
    AgentRegistry.register(FailureAnalysisAgent)
    AgentRegistry.register(ReportingAgent)
    AgentRegistry.register(CoordinatorAgent)
    AgentRegistry.lock()


def register_tools() -> None:
    ToolRegistry._registry.clear()
    ToolRegistry._locked = False
    ToolRegistry.register(
        ToolContract(
            tool_name=HeuristicStructureTool.name,
            version=HeuristicStructureTool.version,
            input_schema=SchemaDefinition(schema_name="dummy_input", json_schema="{}"),
            output_schema=SchemaDefinition(schema_name="dummy_output", json_schema="{}"),
            failure_modes=[],
            cost_estimate=1.0,
            latency_estimate_ms=1,
            determinism=ToolDeterminism.DETERMINISTIC,
        )
    )
    ToolRegistry.lock()


def test_agentic_loop_e2e() -> None:
    register_agents()
    register_tools()

    planner = PlannerAgent()
    plan_decision = planner.decide(PlannerAgentInput(goal="plan"))
    plan = plan_decision.plan

    task_id = plan.entry_tasks[0]
    invocation = ToolInvocationSpec(
        invocation_id="invocation-1",
        tool_name=HeuristicStructureTool.name,
        tool_version="v1",
        inputs=[InvocationInput(name="sequence", value="ACDE")],
        expected_outputs=[OutputExpectation(name="sequence_length", schema_version="v1")],
        constraints=[],
        origin_task_id=task_id,
    )
    decision = Decision(
        agent_name="structure",
        rationale="invoke_dummy_tool",
        requested_tools=[invocation],
        next_tasks=["execute_dummy"],
        confidence=0.5,
        input_refs=["sequence:ACDE"],
        memory_refs=["memory:session"],
        rules_triggered=["test_invocation"],
        confidence_impact=["baseline_assumed"],
    )

    graph = compile_plan_to_execution(plan, [decision])
    execution_task = graph.tasks[task_id]

    initial_state = StateSnapshot(
        state_id="state-0",
        parent_state_id=None,
        plan_fingerprint=plan.fingerprint(),
        timestamp=datetime.now(UTC),
        agent_decisions=[],
        artifacts=[],
        metrics=[],
        confidence_summary=[],
    )
    context = ExecutionContext(
        execution_id="exec-1",
        plan_fingerprint=plan.fingerprint(),
        initial_state=initial_state,
        memory_snapshot=[],
        resource_limits=ResourceLimits(),
    )

    executor = LocalExecutor(DummyBoundary())
    result = executor.run(execution_task, context)
    observation = materialize_observation(result, execution_task)

    evaluation = EvaluationInput(
        observations=[observation],
        prior_state=initial_state,
        plan_metadata=PlanMetadata(plan_fingerprint=plan.fingerprint(), plan_id="plan-1"),
        constraints=[],
    )

    qc = QualityControlAgent()
    candidate = Candidate(
        candidate_id="cand-1",
        sequence="ACDE",
        metrics={"mean_plddt": 80.0, "helix_pct": 40.0, "sheet_pct": 30.0},
    )
    qc_output = qc.decide(
        QualityControlAgentInput(evaluation=evaluation, candidate=candidate)
    )
    critic = CriticAgent()
    critic_output = critic.decide(
        CriticAgentInput(
            critic_name="critic",
            target_agent_name="quality_control",
            target_output=OutputReference(agent_name="qc", output_id="qc-1", schema_version="1.0"),
            prior_decisions=[],
            qc_output=qc_output,
            observations=[observation],
        )
    )

    coordinator = CoordinatorAgent()
    final_decision = coordinator.decide(
        CoordinatorAgentInput(
            decisions=[],
            observations=[observation],
            qc_output=qc_output,
            critic_output=critic_output,
            replanning_trigger=None,
            loop_limits=LoopLimits(max_replans=1, max_executions_per_plan=1, max_uncertainty=1.0),
            loop_state=LoopState(replans=0, executions=1, uncertainty=0.0),
        )
    )

    assert final_decision.decision.value == "ContinueExecution"
