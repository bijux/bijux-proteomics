# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Runtime execution control and loop orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import importlib.metadata
import json
from pathlib import Path
from time import perf_counter
from typing import Any, cast

from bijux_proteomics_intelligence.candidates import (
    CandidateStore,
    update_candidate_from_result,
)
from bijux_proteomics_intelligence.candidates.quality import QCStatus
from bijux_proteomics_intelligence.candidates.schema import Candidate
from bijux_proteomics_intelligence.learning.refinement.runner import (
    LoopContext,
    LoopRunner,
)
from bijux_proteomics_runtime.execution.agents.analysis.failure_analysis import (
    FailureAnalysisAgent,
)
from bijux_proteomics_runtime.execution.agents.catalog import AgentCatalog
from bijux_proteomics_runtime.execution.agents.coordination.coordinator import (
    CoordinatorAgent,
)
from bijux_proteomics_runtime.execution.agents.planning.compiler import (
    compile_plan_to_execution,
)
from bijux_proteomics_runtime.execution.agents.planning.generation import generate_plan
from bijux_proteomics_runtime.execution.agents.planning.planner import PlannerAgent
from bijux_proteomics_runtime.execution.agents.planning.validation import (
    PlanningValidator,
)
from bijux_proteomics_runtime.execution.agents.reporting.reporting import ReportingAgent
from bijux_proteomics_runtime.execution.agents.schemas import (
    CoordinatorAgentInput,
    CoordinatorDecisionType,
    CriticAgentInput,
    OutputReference,
    QualityControlAgentInput,
    ReportingAgentInput,
    RequestParameter,
)
from bijux_proteomics_runtime.execution.agents.verification.critic import CriticAgent
from bijux_proteomics_runtime.execution.agents.verification.input_validation import (
    InputValidationAgent,
)
from bijux_proteomics_runtime.execution.agents.verification.quality_control import (
    QualityControlAgent,
)
from bijux_proteomics_runtime.execution.compiler.boundary import ToolBoundary
from bijux_proteomics_runtime.execution.engine.executor import (
    LocalExecutor,
    materialize_observation,
)
from bijux_proteomics_runtime.execution.tools.base import Tool
from bijux_proteomics_runtime.execution.tools.heuristic import (
    HeuristicStructureTool,
)
from bijux_proteomics_runtime.execution.validation import validate_outputs
from bijux_proteomics_runtime.providers.capabilities import (
    validate_runtime_capabilities,
)
from bijux_proteomics_runtime.runs.analysis import RunAnalysis
from bijux_proteomics_runtime.runs.artifacts import (
    TelemetryHooks,
    map_failure_type,
    require_human_decision,
    validate_human_decision,
    write_artifact,
    write_failure_artifacts,
)
from bijux_proteomics_runtime.runs.checkpoints import (
    build_resume_checkpoint,
    write_resume_checkpoint,
)
from bijux_proteomics_runtime.runs.context import RunContext, create_run_context
from bijux_proteomics_runtime.runs.contracts import (
    RunContextContract,
    RuntimeDatasetKind,
    build_run_context_contract,
)
from bijux_proteomics_runtime.runs.execution_decisions import (
    build_runtime_degraded_execution_report,
    build_runtime_refusal_decision_report,
    write_runtime_execution_decision_report,
)
from bijux_proteomics_runtime.runs.failure_reports import (
    RuntimeFailureCategory,
    build_runtime_failure_report,
    write_runtime_failure_report,
)
from bijux_proteomics_runtime.runs.import_lineage import (
    build_import_run_bundle,
    build_import_trace,
    write_import_documents,
    write_import_run_bundle,
    write_import_trace,
)
from bijux_proteomics_runtime.runs.integrity import (
    guard_path_size,
    guard_payload_size,
    verify_runtime_artifact_integrity,
)
from bijux_proteomics_runtime.runs.launch_bundles import (
    build_container_run_bundle,
    build_scheduler_job_bundle,
    write_container_run_bundle,
    write_scheduler_job_bundle,
)
from bijux_proteomics_runtime.runs.ledger import (
    load_artifact_ledger,
    refresh_runtime_artifact_ledger,
)
from bijux_proteomics_runtime.runs.lifecycle import RunLifecycleState
from bijux_proteomics_runtime.runs.output import (
    ErrorDetail,
    RunOutput,
    RunStatus,
    VersionInfo,
)
from bijux_proteomics_runtime.runs.preflight import (
    RuntimePreflightReport,
    build_runtime_preflight_report,
    write_runtime_preflight_report,
)
from bijux_proteomics_runtime.runs.replay import (
    build_local_run_bundle,
    build_replay_contract,
    write_local_run_bundle,
    write_replay_contract,
)
from bijux_proteomics_runtime.runs.request import RunRequest
from bijux_proteomics_runtime.runs.run_config import RunConfig
from bijux_proteomics_runtime.runs.state_machine import RunStateMachine
from bijux_proteomics_runtime.runs.tool_reliability import (
    ToolReliabilityTracker,
)
from bijux_proteomics_runtime.state.schemas import StateSnapshot
from bijux_proteomics_runtime.support.primitives.decisions import Decision
from bijux_proteomics_runtime.support.primitives.execution import (
    ExecutionContext,
    LoopLimits,
    LoopState,
    ResourceLimits,
)
from bijux_proteomics_runtime.support.primitives.failures import (
    FailureType,
    suggest_next_action,
)
from bijux_proteomics_runtime.support.primitives.observations import (
    EvaluationInput,
    PlanMetadata,
)
from bijux_proteomics_runtime.support.primitives.status import (
    ExecutionStatus,
    Outcome,
    ToolStatus,
    WorkflowState,
)
from bijux_proteomics_runtime.support.primitives.tooling import (
    InvocationInput,
    ToolError,
    ToolInvocationSpec,
    ToolResult,
)
from bijux_proteomics_runtime.support.workspace import (
    write_json_atomic,
    write_text_atomic,
)

__all__ = [
    "PipelineArtifacts",
    "PipelineExecutor",
    "PipelineResult",
    "RunManager",
    "RuntimeStateMachine",
    "_build_run_summary",
    "_ensure_telemetry_costs",
    "_select_structure_tool",
    "_version_info",
    "run_flow",
]


@dataclass
class PipelineArtifacts:
    """PipelineArtifacts."""

    plan: Any
    decision: Decision
    graph: Any
    execution_task: Any
    context: ExecutionContext
    plan_duration_ms: float


@dataclass
class PipelineResult:
    """PipelineResult."""

    candidate: Candidate
    plan_fingerprint: str
    tool_status: str
    report: dict[str, Any]
    qc_status: QCStatus
    coordinator_decision: CoordinatorDecisionType
    failure_type: str
    observation: object | None
    decision: Decision | None
    qc_output: object | None
    critic_output: object | None
    coordinator_output: object | None
    tool_result: ToolResult | None
    timings: dict[str, float]


class PipelineExecutor:
    """PipelineExecutor."""

    def __init__(
        self,
        run_context: RunContext,
        tool: Tool,
        validator: PlanningValidator,
    ) -> None:
        """__init__."""
        self._run_context = run_context
        self._tool = tool
        self._validator = validator
        self._boundary = ToolBoundary({(tool.name, tool.version): tool})
        self._executor = LocalExecutor(self._boundary)
        self._reliability = ToolReliabilityTracker(tool_name=tool.name)
        self._telemetry = TelemetryHooks(run_context)

    def run_iteration(
        self, candidate: Candidate, loop_state: LoopState
    ) -> PipelineResult:
        """run_iteration."""
        run_logger = self._run_context.logger.scope("run")
        agent_logger = self._run_context.logger.scope("agent")
        tool_logger = self._run_context.logger.scope("tool")
        flow_start = perf_counter()
        tool_versions = self._run_context.config.get("tool_versions") or {}
        if self._tool.name not in tool_versions:
            tool_versions[self._tool.name] = self._tool.version
            self._run_context.config["tool_versions"] = tool_versions

        run_logger.log(component=None, event="start", status="ok", duration_ms=0.0)
        self._run_context.telemetry.record_event("run_start")

        validation_errors = self._validator.validate_candidate(candidate)
        if validation_errors:
            agent_logger.log(
                component="input_validation",
                event="validate",
                status="failed",
                duration_ms=0.0,
                errors=validation_errors,
            )
            self._run_context.telemetry.increment("validation_failures", 1.0)
            write_failure_artifacts(
                self._run_context,
                FailureType.INPUT_INVALID,
                {"errors": validation_errors},
            )
            self._run_context.telemetry.observe("run_total_ms", 0.0)
            self._run_context.telemetry.add_cost("tool_units", 0.0)
            self._run_context.telemetry.add_cost("cpu_seconds", 0.0)
            self._run_context.telemetry.add_cost("gpu_seconds", 0.0)
            self._run_context.telemetry.flush()
            return PipelineResult(
                candidate=candidate,
                plan_fingerprint="unknown",
                tool_status="failure",
                report={},
                qc_status=QCStatus.REJECT,
                coordinator_decision=CoordinatorDecisionType.TERMINATE,
                failure_type=FailureType.INPUT_INVALID.value,
                observation=None,
                decision=None,
                qc_output=None,
                critic_output=None,
                coordinator_output=None,
                tool_result=None,
                timings={},
            )

        tool_errors = self._validator.validate_tool_enabled(
            self._tool.name, self._run_context.config
        )
        if tool_errors:
            write_failure_artifacts(
                self._run_context,
                FailureType.TOOL_CRASH,
                {"errors": sorted(tool_errors)},
            )
            self._run_context.telemetry.observe("run_total_ms", 0.0)
            self._run_context.telemetry.add_cost("tool_units", 0.0)
            self._run_context.telemetry.add_cost("cpu_seconds", 0.0)
            self._run_context.telemetry.add_cost("gpu_seconds", 0.0)
            self._run_context.telemetry.flush()
            return PipelineResult(
                candidate=candidate,
                plan_fingerprint="",
                tool_status="failure",
                report={},
                qc_status=QCStatus.REJECT,
                coordinator_decision=CoordinatorDecisionType.TERMINATE,
                failure_type=FailureType.TOOL_CRASH.value,
                observation=None,
                decision=None,
                qc_output=None,
                critic_output=None,
                coordinator_output=None,
                tool_result=None,
                timings={},
            )

        compat_errors = self._validator.validate_tool_compatibility(
            self._tool.name, self._run_context.config
        )
        if compat_errors:
            write_failure_artifacts(
                self._run_context,
                FailureType.TOOL_CRASH,
                {"errors": sorted(compat_errors)},
            )
            self._run_context.telemetry.observe("run_total_ms", 0.0)
            self._run_context.telemetry.add_cost("tool_units", 0.0)
            self._run_context.telemetry.add_cost("cpu_seconds", 0.0)
            self._run_context.telemetry.add_cost("gpu_seconds", 0.0)
            self._run_context.telemetry.flush()
            return PipelineResult(
                candidate=candidate,
                plan_fingerprint="",
                tool_status="failure",
                report={},
                qc_status=QCStatus.REJECT,
                coordinator_decision=CoordinatorDecisionType.TERMINATE,
                failure_type=FailureType.TOOL_CRASH.value,
                observation=None,
                decision=None,
                qc_output=None,
                critic_output=None,
                coordinator_output=None,
                tool_result=None,
                timings={},
            )

        planning_start = perf_counter()
        planner = PlannerAgent()
        plan_output = generate_plan(cast(Any, planner), "predict_structure")
        plan = plan_output.plan
        plan_duration_ms = (perf_counter() - planning_start) * 1000.0
        write_json_atomic(
            self._run_context.workspace.plan_path, plan.model_dump(mode="json")
        )
        self._telemetry.record_snapshot(
            "planner", loop_state.iteration_index, plan.model_dump()
        )

        origin_task_id = "unknown"
        if plan.tasks:
            origin_task_id = next(iter(plan.tasks))
        invocation = ToolInvocationSpec(
            invocation_id=f"{self._run_context.run_id}:{self._tool.name}:0",
            tool_name=self._tool.name,
            tool_version=self._tool.version,
            inputs=[InvocationInput(name="sequence", value=candidate.sequence)],
            expected_outputs=[],
            constraints=[],
            origin_task_id=origin_task_id,
        )
        planning_decision = Decision(
            agent_name="planner",
            rationale="default_invocation",
            requested_tools=[invocation],
            next_tasks=[],
            confidence=0.1,
            input_refs=["sequence"],
            memory_refs=["memory:session"],
            rules_triggered=["default_plan"],
            confidence_impact=["baseline_low_confidence"],
        )

        try:
            compiled = compile_plan_to_execution(plan, [planning_decision])
        except Exception as exc:  # noqa: BLE001
            write_failure_artifacts(
                self._run_context,
                FailureType.INVALID_PLAN,
                {"errors": [str(exc)]},
            )
            return PipelineResult(
                candidate=candidate,
                plan_fingerprint="",
                tool_status="failure",
                report={},
                qc_status=QCStatus.REJECT,
                coordinator_decision=CoordinatorDecisionType.TERMINATE,
                failure_type=FailureType.INVALID_PLAN.value,
                observation=None,
                decision=None,
                qc_output=None,
                critic_output=None,
                coordinator_output=None,
                tool_result=None,
                timings={"planning_ms": plan_duration_ms},
            )
        plan_fingerprint = plan.fingerprint()
        initial_state = StateSnapshot.model_validate(
            json.loads(self._run_context.workspace.state_path.read_text())
        )
        exec_ctx = ExecutionContext(
            execution_id=f"{self._run_context.run_id}:execution:0",
            plan_fingerprint=plan_fingerprint,
            initial_state=initial_state,
            memory_snapshot=[],
            resource_limits=ResourceLimits(
                cpu_seconds=float(
                    self._run_context.config["resource_limits"]["cpu_seconds"]
                ),
                gpu_seconds=float(
                    self._run_context.config["resource_limits"]["gpu_seconds"]
                ),
                max_total_cost=float(
                    self._run_context.config.get("loop_max_cost", 0.0)
                ),
            ),
        )
        task = next(
            (
                item
                for item in compiled.tasks.values()
                if item.tool_invocation.tool_name == self._tool.name
            ),
            None,
        )
        if task is None:
            write_failure_artifacts(
                self._run_context,
                FailureType.INVALID_PLAN,
                {"errors": [f"missing_task_for_tool:{self._tool.name}"]},
            )
            return PipelineResult(
                candidate=candidate,
                plan_fingerprint="",
                tool_status="failure",
                report={},
                qc_status=QCStatus.REJECT,
                coordinator_decision=CoordinatorDecisionType.TERMINATE,
                failure_type=FailureType.INVALID_PLAN.value,
                observation=None,
                decision=None,
                qc_output=None,
                critic_output=None,
                coordinator_output=None,
                tool_result=None,
                timings={"planning_ms": plan_duration_ms},
            )

        tool_logger.log(
            component=self._tool.name,
            event="invoke",
            status="start",
            duration_ms=0.0,
        )
        tool_start = perf_counter()
        result = self._executor.run(task, exec_ctx)
        tool_latency = (perf_counter() - tool_start) * 1000.0
        tool_logger.log(
            component=self._tool.name,
            event="invoke",
            status=result.status,
            duration_ms=tool_latency,
        )
        self._run_context.telemetry.observe("tool_latency_ms", tool_latency)
        self._run_context.telemetry.add_cost("tool_units", 1.0)
        self._reliability.record(result.status, tool_latency)
        tool_status = result.status

        failure_type = map_failure_type(result.status, result.error)
        if tool_status == "success" and not validate_outputs(result.outputs):
            tool_status = "failure"
            failure_type = FailureType.INVALID_OUTPUT.value
            result = result.model_copy(
                update={
                    "status": "failure",
                    "error": ToolError(
                        error_type="invalid_output", message="invalid_output"
                    ),
                }
            )
        if tool_status != "success" and not failure_type:
            failure_type = FailureType.TOOL_FAILURE.value
        if failure_type:
            write_failure_artifacts(
                self._run_context,
                FailureType(failure_type),
                {"error": result.error.model_dump() if result.error else {}},
            )
        if tool_status == "success":
            outputs_map = {item.name: item.value for item in result.outputs}
            pdb_text = outputs_map.get("pdb_text")
            if pdb_text:
                write_text_atomic(
                    self._run_context.workspace.run_dir / "predicted.pdb", pdb_text
                )

        observation = None
        if tool_status == "success":
            observation = materialize_observation(result, task)

        updated_candidate = update_candidate_from_result(
            candidate,
            self._tool.name,
            self._tool.version,
            cast(Any, result),
            plan_fingerprint,
            loop_state.iteration_index,
        )

        evaluation_input = EvaluationInput(
            observations=[observation] if observation else [],
            prior_state=initial_state,
            plan_metadata=PlanMetadata(
                plan_fingerprint=plan_fingerprint, plan_id=origin_task_id
            ),
            constraints=[],
        )
        qc_agent = QualityControlAgent()
        qc_input = QualityControlAgentInput(
            evaluation=evaluation_input,
            candidate=updated_candidate,
        )
        qc_output = qc_agent.decide(qc_input)
        qc_status = qc_output.status

        critic_agent = CriticAgent()
        critic_input = CriticAgentInput(
            critic_name=CriticAgent.name,
            target_agent_name=QualityControlAgent.name,
            target_output=OutputReference(
                agent_name=QualityControlAgent.name,
                output_id="qc:0",
                schema_version="1.0",
            ),
            prior_decisions=[planning_decision],
            qc_output=qc_output,
            observations=[observation] if observation else [],
            tool_reliability=self._reliability.summary(),
        )
        critic_output = critic_agent.decide(critic_input)

        coordinator = CoordinatorAgent()
        coordinator_input = CoordinatorAgentInput(
            decisions=[planning_decision],
            observations=[observation] if observation else [],
            qc_output=qc_output,
            critic_output=critic_output,
            replanning_trigger=None,
            loop_limits=LoopLimits(
                max_replans=0,
                max_executions_per_plan=int(
                    self._run_context.config.get("loop_max_iterations", 1)
                ),
                max_uncertainty=0.0,
            ),
            loop_state=loop_state,
        )
        coordinator_output = coordinator.decide(coordinator_input)

        reporting = ReportingAgent()
        report_input = ReportingAgentInput(
            qc_status=qc_status,
            decision=coordinator_output.decision.value,
            tool_outputs=[
                RequestParameter(name=item.name, value=str(item.value))
                for item in result.outputs
            ],
        )
        report = reporting.decide(report_input)
        write_json_atomic(
            self._run_context.workspace.report_path, report.model_dump(mode="json")
        )

        decision = Decision(
            agent_name="coordinator",
            rationale=coordinator_output.stop_reason,
            confidence=0.5,
            input_refs=[
                "tool_result",
                "qc_output",
            ],
            memory_refs=[],
            rules_triggered=coordinator_output.reason_codes,
            requested_tools=[],
            confidence_impact=coordinator_output.explanation.confidence_impact,
            next_tasks=coordinator_output.thresholds_hit,
        )
        execution_plan = compiled
        write_json_atomic(
            self._run_context.workspace.execution_path,
            execution_plan.model_dump(mode="json"),
        )

        decision_artifact = write_artifact(
            self._run_context.workspace,
            "decision",
            decision.model_dump(mode="json"),
            description="coordinator_decision",
            tags=["decision"],
        )
        tool_artifact = write_artifact(
            self._run_context.workspace,
            "tool_result",
            result.model_dump(mode="json"),
            description=self._tool.name,
            tags=["tool_output"],
        )
        report_artifact = write_artifact(
            self._run_context.workspace,
            "report",
            report.model_dump(mode="json"),
            description="run_report",
            tags=["report"],
        )

        state_snapshot = StateSnapshot(
            state_id=f"state-{loop_state.iteration_index}",
            parent_state_id=None,
            plan_fingerprint=plan_fingerprint,
            timestamp=datetime.now(UTC),
            agent_decisions=[],
            artifacts=[decision_artifact, tool_artifact, report_artifact],
            metrics=[],
            confidence_summary=[],
        )
        write_json_atomic(
            self._run_context.workspace.state_path,
            state_snapshot.model_dump(mode="json"),
        )
        self._telemetry.record_execution_snapshot(
            loop_state.iteration_index,
            state_snapshot.model_dump(mode="json"),
            decisions=[decision_artifact.model_dump(mode="json")],
            tool_outputs=[tool_artifact.model_dump(mode="json")],
        )
        self._telemetry.record_snapshot(
            "execution", loop_state.iteration_index, state_snapshot.model_dump()
        )
        timings = {
            "planning_ms": plan_duration_ms,
            "tool_ms": tool_latency,
            "total_ms": (perf_counter() - flow_start) * 1000.0,
        }
        write_json_atomic(self._run_context.workspace.timings_path, timings)

        return PipelineResult(
            candidate=updated_candidate,
            plan_fingerprint=plan_fingerprint,
            tool_status=tool_status,
            report=report.summary,
            qc_status=qc_status,
            coordinator_decision=coordinator_output.decision,
            failure_type=failure_type,
            observation=observation,
            decision=decision,
            qc_output=qc_output,
            critic_output=critic_output,
            coordinator_output=coordinator_output,
            tool_result=result,
            timings=timings,
        )


def register_runtime_agents() -> None:
    """register_runtime_agents."""
    if AgentCatalog.list():
        return
    AgentCatalog.clear()
    AgentCatalog.register(PlannerAgent)
    AgentCatalog.register(InputValidationAgent)
    AgentCatalog.register(QualityControlAgent)
    AgentCatalog.register(CriticAgent)
    AgentCatalog.register(FailureAnalysisAgent)
    AgentCatalog.register(ReportingAgent)
    AgentCatalog.register(CoordinatorAgent)
    AgentCatalog.lock()


class RuntimeStateMachine:
    """RuntimeStateMachine."""

    def __init__(self, run_context: RunContext, tool: Tool | None = None) -> None:
        """__init__."""
        self._run_context = run_context
        self._tool = tool or HeuristicStructureTool()
        register_runtime_agents()
        self._validator = PlanningValidator()
        self._executor = PipelineExecutor(run_context, self._tool, self._validator)
        self._analysis = RunAnalysis()
        self._loop_context = LoopContext(
            config=run_context.config,
            telemetry=run_context.telemetry,
            logger=cast(Any, run_context.logger.scope("loop")),
            analysis_path=run_context.workspace.analysis_path,
        )
        self._loop_runner = LoopRunner(
            self._loop_context, cast(Any, self._executor), self._analysis
        )
        self._state_machine = RunStateMachine()

    def run(self, candidate: Candidate) -> dict[str, Any]:
        """run."""
        self._state_machine.transition("execute")
        result = self._loop_runner.run(candidate)
        self._state_machine.transition("evaluate")
        return self._finalize(cast(PipelineResult, result))

    def _finalize(self, result: PipelineResult) -> dict[str, Any]:
        """_finalize."""
        require_human = bool(self._run_context.config.get("require_human_decision"))
        if require_human:
            selection = require_human_decision(
                [result.candidate], self._run_context.workspace, top_n=1
            )
            lifecycle_state = RunLifecycleState.HUMAN_REVIEW.value
            frozen_ids = selection.frozen_ids
        else:
            selection = None
            lifecycle_state = RunLifecycleState.CANDIDATE_READY.value
            frozen_ids = []
        write_json_atomic(
            self._run_context.workspace.lifecycle_path,
            {"state": lifecycle_state, "frozen": frozen_ids},
        )
        if result.failure_type == FailureType.CONVERGENCE_FAILURE.value:
            write_failure_artifacts(
                self._run_context,
                FailureType.CONVERGENCE_FAILURE,
                {"errors": ["loop_convergence_failure"]},
            )
        if (
            require_human
            and selection
            and selection.human_required
            and not result.failure_type
        ):
            decision_report = validate_human_decision(
                self._run_context.workspace.human_decision_path
            )
            if not decision_report.passed:
                result = PipelineResult(
                    candidate=result.candidate,
                    plan_fingerprint=result.plan_fingerprint,
                    tool_status=result.tool_status,
                    report=result.report,
                    qc_status=result.qc_status,
                    coordinator_decision=result.coordinator_decision,
                    failure_type=FailureType.NONE.value,
                    observation=result.observation,
                    decision=result.decision,
                    qc_output=result.qc_output,
                    critic_output=result.critic_output,
                    coordinator_output=result.coordinator_output,
                    tool_result=result.tool_result,
                    timings=result.timings,
                )
        write_json_atomic(
            self._run_context.workspace.config_path, self._run_context.config
        )
        return {
            "candidate_id": result.candidate.candidate_id,
            "candidate": result.candidate.model_dump(),
            "plan_fingerprint": result.plan_fingerprint,
            "tool_status": result.tool_status,
            "report": result.report,
            "qc_status": result.qc_status.value,
            "coordinator_decision": result.coordinator_decision.value,
            "failure_type": result.failure_type,
            "lifecycle_state": lifecycle_state,
        }


class RunManager:
    """RunManager."""

    def __init__(self, base_dir: Path, config: RunConfig | None = None) -> None:
        """__init__."""
        self._base_dir = base_dir
        self._config = config or RunConfig()

    def run(
        self, sequence: str, tool: Tool | None = None, run_id: str | None = None
    ) -> dict[str, Any]:
        """run."""
        try:
            RunRequest.model_validate({"sequence": sequence})
        except Exception as exc:  # noqa: BLE001
            context, warnings = create_run_context(
                self._base_dir, self._config, run_id=run_id
            )
            selected_tool = tool or _select_structure_tool(context.config)
            return self._fail_fast(
                context, [str(exc)], FailureType.INPUT_INVALID.value, selected_tool
            )
        context, warnings = create_run_context(
            self._base_dir, self._config, run_id=run_id
        )
        return self._run_with_context(sequence, context, warnings, tool)

    def run_candidate(
        self,
        candidate: Candidate,
        tool: Tool | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """run_candidate."""
        context, warnings = create_run_context(
            self._base_dir, self._config, run_id=run_id
        )
        selected_tool = tool or _select_structure_tool(context.config)
        start = perf_counter()
        run_logger = context.logger.scope("run")
        run_logger.log(component=None, event="start", status="ok", duration_ms=0.0)
        context.telemetry.record_event("run_start")
        try:
            result = self._run_with_candidate(
                candidate,
                context,
                warnings,
                selected_tool,
                explicit_tool=tool is not None,
                command="resume",
            )
            failure_type = result.get("failure_type") or FailureType.NONE.value
            status = "failure" if failure_type != FailureType.NONE.value else "success"
            if result.get("tool_status") == "dry_run":
                status = "partial"
            if result.get("lifecycle_state") == RunLifecycleState.HUMAN_REVIEW.value:
                status = "partial"
        except KeyboardInterrupt:
            status = "failure"
            failure_type = FailureType.UNKNOWN.value
            result = self._fail_fast(
                context, ["cancelled"], failure_type, selected_tool
            )
        except Exception as exc:  # noqa: BLE001
            status = "failure"
            failure_type = FailureType.UNKNOWN.value
            result = self._fail_fast(context, [str(exc)], failure_type, selected_tool)
        return self._finalize_execution(
            context,
            warnings,
            selected_tool,
            result,
            status,
            failure_type,
            command="resume",
            start=start,
            run_logger=run_logger,
        )

    def import_result(
        self,
        *,
        sequence: str,
        source_path: Path,
        imported_payload: dict[str, Any],
        engine_name: str,
        engine_version: str,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """Import external-engine outputs without pretending runtime produced them."""
        start = perf_counter()
        try:
            RunRequest.model_validate({"sequence": sequence})
        except Exception as exc:  # noqa: BLE001
            context, _warnings = create_run_context(
                self._base_dir, self._config, run_id=run_id
            )
            return self._fail_fast(
                context,
                [str(exc)],
                FailureType.INPUT_INVALID.value,
                None,
            )
        context, warnings = create_run_context(
            self._base_dir, self._config, run_id=run_id
        )
        context.telemetry.record_event("run_start")
        run_context_contract = build_run_context_contract(
            run_id=context.run_id,
            started_at=context.start_time.isoformat(),
            base_dir=self._base_dir,
            config=context.config,
            provider_name=engine_name,
            artifact_policy=context.artifact_policy,
            sequence=sequence,
            command="import",
            workflow_family="external_import",
            candidate_id=f"{context.run_id}-c0",
            dataset_kind=RuntimeDatasetKind.IMPORTED_EVIDENCE,
            source_path=source_path,
            import_only=True,
        )
        write_json_atomic(
            context.workspace.run_context_path, run_context_contract.to_dict()
        )
        preflight_report = build_runtime_preflight_report(
            context.workspace,
            run_id=context.run_id,
            provider_name=engine_name,
            source_path=source_path,
            required_tool_versions=context.config.get("tool_versions"),
            available_tool_versions={engine_name: engine_version},
        )
        write_runtime_preflight_report(context.workspace, preflight_report)
        if not preflight_report.passed:
            preflight_messages = [
                detail_code
                for check in preflight_report.checks
                for detail_code in check.detail_codes
            ] or [check.message for check in preflight_report.checks]
            return self._fail_fast(
                context,
                preflight_messages,
                FailureType.INVALID_OUTPUT.value,
                None,
            )
        max_bundle_artifact_bytes = int(
            context.config.get("max_bundle_artifact_bytes") or 1_000_000
        )
        source_guard = guard_path_size(
            source_path, max_size_bytes=max_bundle_artifact_bytes
        )
        if not source_guard.allowed:
            return self._fail_fast(
                context,
                [f"source_artifact_too_large:{source_guard.actual_size_bytes}"],
                FailureType.INVALID_OUTPUT.value,
                None,
            )
        payload_guard = guard_payload_size(
            imported_payload,
            artifact_label="imported_payload",
            max_size_bytes=max_bundle_artifact_bytes,
        )
        if not payload_guard.allowed:
            return self._fail_fast(
                context,
                [f"import_payload_too_large:{payload_guard.actual_size_bytes}"],
                FailureType.INVALID_OUTPUT.value,
                None,
            )
        imported_path, evidence_bundle_path, review_packet_path = (
            write_import_documents(
                context.workspace,
                engine_name=engine_name,
                engine_version=engine_version,
                source_path=source_path,
                imported_payload=imported_payload,
            )
        )
        version_info = _version_info(None)
        version_info.tool_versions = {engine_name: engine_version}
        summary = _build_run_summary(
            context,
            command="import",
            candidate_id=f"{context.run_id}-c0",
            status="success",
            failure_type=FailureType.NONE.value,
            lifecycle_state=RunLifecycleState.ARCHIVED.value,
            tool_status="imported",
            qc_status=QCStatus.ACCEPTABLE.value,
            warnings=warnings,
            version_info=version_info,
            provider_name=engine_name,
        )
        write_json_atomic(context.workspace.run_summary_path, summary)
        output = RunOutput(
            run_id=context.run_id,
            candidate_id=f"{context.run_id}-c0",
            lifecycle_state=RunLifecycleState.ARCHIVED.value,
            status=RunStatus.SUCCESS,
            failure_type=FailureType.NONE.value,
            plan_fingerprint="import-only",
            tool_status="imported",
            report={
                "engine_name": engine_name,
                "engine_version": engine_version,
                "source_path": str(source_path),
            },
            qc_status=QCStatus.ACCEPTABLE,
            coordinator_decision=CoordinatorDecisionType.TERMINATE,
            errors=[],
            warnings=sorted(warnings),
            version_info=version_info,
        )
        write_json_atomic(
            context.workspace.run_output_path, output.model_dump(mode="json")
        )
        replay_contract = build_replay_contract(
            run_context_contract,
            app_version=version_info.app_version,
            git_commit=version_info.git_commit,
            tool_versions=version_info.tool_versions,
        )
        write_replay_contract(context.workspace, replay_contract)
        refresh_runtime_artifact_ledger(
            context.workspace,
            run_id=context.run_id,
            artifact_policy=context.artifact_policy,
            producer="bijux_proteomics_runtime.runs.manager",
        )
        import_trace = build_import_trace(
            workspace=context.workspace,
            run_id=context.run_id,
            engine_name=engine_name,
            engine_version=engine_version,
            source_path=source_path,
            imported_artifact_path=imported_path,
            derived_paths=(
                evidence_bundle_path,
                review_packet_path,
                context.workspace.run_summary_path,
                context.workspace.run_context_path,
                context.workspace.replay_contract_path,
            ),
        )
        write_import_trace(context.workspace, import_trace)
        refresh_runtime_artifact_ledger(
            context.workspace,
            run_id=context.run_id,
            artifact_policy=context.artifact_policy,
            producer="bijux_proteomics_runtime.runs.manager",
        )
        import_run_bundle = build_import_run_bundle(
            run_context=run_context_contract,
            replay_contract=replay_contract,
            import_trace=import_trace,
            artifact_ledger=load_artifact_ledger(context.workspace, context.run_id),
            run_summary=summary,
        )
        write_import_run_bundle(context.workspace, import_run_bundle)
        refresh_runtime_artifact_ledger(
            context.workspace,
            run_id=context.run_id,
            artifact_policy=context.artifact_policy,
            producer="bijux_proteomics_runtime.runs.manager",
        )
        verify_runtime_artifact_integrity(
            context.workspace,
            run_id=context.run_id,
            max_artifact_bytes=max_bundle_artifact_bytes,
        )
        context.telemetry.observe("run_total_ms", (perf_counter() - start) * 1000.0)
        _ensure_telemetry_costs(context)
        context.telemetry.flush()
        refresh_runtime_artifact_ledger(
            context.workspace,
            run_id=context.run_id,
            artifact_policy=context.artifact_policy,
            producer="bijux_proteomics_runtime.runs.manager",
        )
        return output.model_dump(mode="json")

    def _run_with_context(
        self,
        sequence: str,
        context: RunContext,
        warnings: list[str],
        tool: Tool | None,
    ) -> dict[str, Any]:
        """_run_with_context."""
        start = perf_counter()
        run_logger = context.logger.scope("run")
        run_logger.log(component=None, event="start", status="ok", duration_ms=0.0)
        context.telemetry.record_event("run_start")
        selected_tool = tool or _select_structure_tool(context.config)

        try:
            candidate = Candidate(
                candidate_id=f"{context.run_id}-c0",
                sequence=sequence,
                provenance={"run_id": context.run_id},
            )
            result = self._run_with_candidate(
                candidate,
                context,
                warnings,
                selected_tool,
                explicit_tool=tool is not None,
                command="run",
            )
            failure_type = result.get("failure_type") or FailureType.NONE.value
            status = "failure" if failure_type != FailureType.NONE.value else "success"
            if result.get("tool_status") == "dry_run":
                status = "partial"
            if result.get("lifecycle_state") == RunLifecycleState.HUMAN_REVIEW.value:
                status = "partial"
        except KeyboardInterrupt:
            status = "failure"
            failure_type = FailureType.UNKNOWN.value
            result = self._fail_fast(
                context, ["cancelled"], failure_type, selected_tool
            )
        except Exception as exc:  # noqa: BLE001
            status = "failure"
            failure_type = FailureType.UNKNOWN.value
            result = self._fail_fast(context, [str(exc)], failure_type, selected_tool)
        return self._finalize_execution(
            context,
            warnings,
            selected_tool,
            result,
            status,
            failure_type,
            command="run",
            start=start,
            run_logger=run_logger,
        )

    def _finalize_execution(
        self,
        context: RunContext,
        warnings: list[str],
        selected_tool: Tool,
        result: dict[str, Any],
        status: str,
        failure_type: str,
        command: str,
        start: float | None = None,
        run_logger: Any | None = None,
    ) -> dict[str, Any]:
        """Finalize run output and summary artifacts."""
        version_info = _version_info(selected_tool)
        if status != "failure":
            failure_type = FailureType.NONE.value
        output = RunOutput(
            run_id=context.run_id,
            candidate_id=result.get("candidate_id") or f"{context.run_id}-c0",
            lifecycle_state=result.get("lifecycle_state")
            or RunLifecycleState.PLANNED.value,
            status=RunStatus.PARTIAL
            if status == "partial"
            else RunStatus.SUCCESS
            if status == "success"
            else RunStatus.FAILURE,
            failure_type=failure_type or FailureType.UNKNOWN.value,
            plan_fingerprint=result.get("plan_fingerprint") or "unknown",
            tool_status=result.get("tool_status") or "unknown",
            report=result.get("report", {}),
            qc_status=QCStatus(result.get("qc_status") or QCStatus.REJECT.value),
            coordinator_decision=CoordinatorDecisionType(
                result.get("coordinator_decision")
                or CoordinatorDecisionType.TERMINATE.value
            ),
            errors=(
                [
                    ErrorDetail(
                        error_type=failure_type or FailureType.UNKNOWN.value,
                        message="run_failed",
                    )
                ]
                if status == "failure" and failure_type
                else []
            ),
            warnings=sorted(warnings),
            version_info=version_info,
        )
        summary = _build_run_summary(
            context,
            command=command,
            candidate_id=output.candidate_id,
            status=status,
            failure_type=failure_type,
            lifecycle_state=output.lifecycle_state,
            tool_status=output.tool_status,
            qc_status=output.qc_status.value,
            warnings=warnings,
            version_info=version_info,
            provider_name=selected_tool.name,
        )
        write_json_atomic(context.workspace.run_summary_path, summary)
        if start is not None:
            context.telemetry.observe("run_total_ms", (perf_counter() - start) * 1000.0)
            _ensure_telemetry_costs(context)
            context.telemetry.flush()
        if run_logger is not None:
            run_logger.log(
                component=None, event="complete", status=status, duration_ms=0.0
            )
        write_json_atomic(
            context.workspace.run_output_path, output.model_dump(mode="json")
        )
        if summary["tool_status"] == ToolStatus.DEGRADED.value:
            write_runtime_execution_decision_report(
                context.workspace,
                build_runtime_degraded_execution_report(summary),
            )
        run_context_contract = RunContextContract.load_json(
            context.workspace.run_context_path
        )
        replay_contract = build_replay_contract(
            run_context_contract,
            app_version=version_info.app_version,
            git_commit=version_info.git_commit,
            tool_versions=version_info.tool_versions,
        )
        write_replay_contract(context.workspace, replay_contract)
        refresh_runtime_artifact_ledger(
            context.workspace,
            run_id=context.run_id,
            artifact_policy=context.artifact_policy,
            producer="bijux_proteomics_runtime.runs.manager",
        )
        local_run_bundle = build_local_run_bundle(
            run_context=run_context_contract,
            replay_contract=replay_contract,
            artifact_ledger=load_artifact_ledger(context.workspace, context.run_id),
            run_summary=summary,
        )
        write_local_run_bundle(context.workspace, local_run_bundle)
        launch_surface = str(context.config.get("launch_surface") or "local")
        if launch_surface == "container":
            write_container_run_bundle(
                context.workspace,
                build_container_run_bundle(
                    workspace=context.workspace,
                    run_context=run_context_contract,
                    replay_contract=replay_contract,
                    config=context.config,
                ),
            )
        elif launch_surface == "scheduler":
            write_scheduler_job_bundle(
                context.workspace,
                build_scheduler_job_bundle(
                    run_context=run_context_contract,
                    replay_contract=replay_contract,
                    config=context.config,
                ),
            )
        checkpoint = build_resume_checkpoint(
            run_context=run_context_contract,
            status=status,
            lifecycle_state=output.lifecycle_state,
            command=command,
        )
        if checkpoint is not None:
            write_resume_checkpoint(context.workspace, checkpoint)
        refresh_runtime_artifact_ledger(
            context.workspace,
            run_id=context.run_id,
            artifact_policy=context.artifact_policy,
            producer="bijux_proteomics_runtime.runs.manager",
        )
        verify_runtime_artifact_integrity(
            context.workspace,
            run_id=context.run_id,
            max_artifact_bytes=int(
                context.config.get("max_bundle_artifact_bytes") or 1_000_000
            ),
        )
        refresh_runtime_artifact_ledger(
            context.workspace,
            run_id=context.run_id,
            artifact_policy=context.artifact_policy,
            producer="bijux_proteomics_runtime.runs.manager",
        )
        return output.model_dump(mode="json")

    def _run_with_candidate(
        self,
        candidate: Candidate,
        context: RunContext,
        warnings: list[str],
        tool: Tool | None,
        explicit_tool: bool = False,
        command: str = "run",
    ) -> dict[str, Any]:
        """_run_with_candidate."""
        if warnings:
            run_logger = context.logger.scope("run")
            run_logger.log(
                component=None,
                event="defaults_applied",
                status="warn",
                duration_ms=0.0,
                warnings=sorted(warnings),
            )
            if context.config.get("strict_mode"):
                return self._fail_fast(
                    context, warnings, FailureType.UNKNOWN.value, tool
                )
        if context.config.get("strict_mode"):
            enabled = context.config.get("predictors_enabled", [])
            if len(enabled) > 1:
                return self._fail_fast(
                    context,
                    ["multiple_predictors_in_strict_mode"],
                    FailureType.UNKNOWN.value,
                    tool,
                )
        selected_tool = tool or _select_structure_tool(context.config)
        parent_run_id = None
        if candidate.provenance.get("run_id") not in {None, context.run_id}:
            parent_run_id = str(candidate.provenance["run_id"])
        run_context_contract = build_run_context_contract(
            run_id=context.run_id,
            started_at=context.start_time.isoformat(),
            base_dir=self._base_dir,
            config=context.config,
            provider_name=selected_tool.name,
            artifact_policy=context.artifact_policy,
            sequence=candidate.sequence,
            command=command,
            workflow_family="structure_prediction",
            candidate_id=candidate.candidate_id,
            dataset_kind=(
                RuntimeDatasetKind.CANDIDATE_STORE
                if parent_run_id is not None
                else RuntimeDatasetKind.INLINE_SEQUENCE
            ),
            parent_run_id=parent_run_id,
            resume_depth=0 if parent_run_id is None else 1,
        )
        write_json_atomic(
            context.workspace.run_context_path,
            run_context_contract.to_dict(),
        )
        preflight_report = build_runtime_preflight_report(
            context.workspace,
            run_id=context.run_id,
            provider_name=selected_tool.name,
            required_tool_versions=context.config.get("tool_versions"),
            available_tool_versions={selected_tool.name: selected_tool.version},
        )
        write_runtime_preflight_report(context.workspace, preflight_report)
        if not preflight_report.passed:
            preflight_messages = [
                detail_code
                for check in preflight_report.checks
                for detail_code in check.detail_codes
            ] or [check.message for check in preflight_report.checks]
            return self._fail_fast(
                context,
                preflight_messages,
                FailureType.CAPABILITY_MISSING.value,
                selected_tool,
            )
        capability_errors, capability_warnings = validate_runtime_capabilities(
            context.config, allow_unknown=explicit_tool
        )
        if capability_errors:
            return self._fail_fast(
                context,
                capability_errors,
                FailureType.CAPABILITY_MISSING.value,
                tool,
            )
        if capability_warnings:
            warnings.extend(capability_warnings)
            context.logger.scope("capabilities").log(
                component="capabilities",
                event="execution_mode_warning",
                status="warn",
                duration_ms=0.0,
                warnings=capability_warnings,
            )
        result = run_flow(candidate, context, selected_tool)
        if result.get("candidate"):
            store = CandidateStore(context.workspace.candidate_store_dir)
            stored = Candidate.model_validate(result["candidate"])
            store.update_candidate(stored)
        return result

    def _fail_fast(
        self,
        context: RunContext,
        warnings: list[str],
        failure_type: str,
        tool: Tool | None = None,
    ) -> dict[str, Any]:
        """_fail_fast."""
        context.telemetry.record_event("run_start")
        context.telemetry.observe("run_total_ms", 0.0)
        context.telemetry.add_cost("tool_units", 0.0)
        context.telemetry.add_cost("cpu_seconds", 0.0)
        context.telemetry.add_cost("gpu_seconds", 0.0)
        error_report = {
            "failure_type": failure_type,
            "message": ";".join(warnings),
        }
        try:
            error_report["next_action"] = suggest_next_action(FailureType(failure_type))
        except Exception:
            error_report["next_action"] = suggest_next_action(FailureType.UNKNOWN)
        write_json_atomic(context.workspace.error_path, error_report)
        failure_report = build_runtime_failure_report(
            run_id=context.run_id,
            failure_type=failure_type,
            message=error_report["message"],
            detail_codes=tuple(sorted(warnings)),
        )
        write_runtime_failure_report(
            context.workspace,
            failure_report,
        )
        preflight_report = _load_preflight_report_if_available(context.workspace)
        if preflight_report is not None or failure_report.failure_category in {
            RuntimeFailureCategory.CONTAINER,
            RuntimeFailureCategory.IMPORT,
            RuntimeFailureCategory.SCHEDULER,
            RuntimeFailureCategory.VALIDATION,
            RuntimeFailureCategory.WORKSPACE,
        }:
            write_runtime_execution_decision_report(
                context.workspace,
                build_runtime_refusal_decision_report(
                    provider_name=tool.name if tool else "unknown",
                    preflight_report=preflight_report,
                    failure_report=failure_report,
                ),
            )
        version_info = _version_info(tool)
        output = RunOutput(
            run_id=context.run_id,
            candidate_id=f"{context.run_id}-c0",
            lifecycle_state=RunLifecycleState.PLANNED.value,
            status=RunStatus.FAILURE,
            failure_type=failure_type or FailureType.UNKNOWN.value,
            plan_fingerprint="unknown",
            tool_status="failure",
            report={},
            qc_status=QCStatus.REJECT,
            coordinator_decision=CoordinatorDecisionType.TERMINATE,
            errors=[
                ErrorDetail(
                    error_type=failure_type or FailureType.UNKNOWN.value,
                    message="run_failed",
                )
            ],
            warnings=sorted(warnings),
            version_info=version_info,
        )
        summary = _build_run_summary(
            context,
            command="run",
            candidate_id=output.candidate_id,
            status="failure",
            failure_type=failure_type,
            lifecycle_state=RunLifecycleState.PLANNED.value,
            tool_status="failed",
            qc_status=QCStatus.REJECT.value,
            warnings=warnings,
            version_info=version_info,
            provider_name=tool.name if tool else "unknown",
        )
        write_json_atomic(context.workspace.run_summary_path, summary)
        write_json_atomic(
            context.workspace.run_output_path, output.model_dump(mode="json")
        )
        refresh_runtime_artifact_ledger(
            context.workspace,
            run_id=context.run_id,
            artifact_policy=context.artifact_policy,
            producer="bijux_proteomics_runtime.runs.manager",
        )
        return output.model_dump(mode="json")


def _build_run_summary(
    context: RunContext,
    command: str,
    candidate_id: str,
    status: str,
    failure_type: str,
    lifecycle_state: str,
    tool_status: str,
    qc_status: str,
    warnings: list[str],
    version_info: VersionInfo,
    provider_name: str,
) -> dict[str, Any]:
    """Build the stable run summary contract."""
    execution_status = (
        ExecutionStatus.ERRORED.value
        if status == "failure"
        else ExecutionStatus.COMPLETED.value
    )
    if lifecycle_state == RunLifecycleState.HUMAN_REVIEW.value:
        workflow_state = WorkflowState.AWAITING_HUMAN_REVIEW.value
    elif status == "partial":
        workflow_state = WorkflowState.PAUSED.value
    elif status == "success":
        workflow_state = WorkflowState.DONE.value
    else:
        workflow_state = WorkflowState.DONE.value

    if workflow_state == WorkflowState.AWAITING_HUMAN_REVIEW.value:
        outcome = Outcome.NEEDS_REVIEW.value
    elif status == "success":
        outcome = (
            Outcome.ACCEPTED.value
            if qc_status == QCStatus.ACCEPTABLE.value
            else Outcome.REJECTED.value
        )
    elif status == "partial":
        outcome = Outcome.INCONCLUSIVE.value
    else:
        outcome = Outcome.INCONCLUSIVE.value

    normalized_tool_status = tool_status.lower()
    if normalized_tool_status in {"dry_run", "skipped"}:
        tool_state = ToolStatus.SKIPPED.value
    elif normalized_tool_status in {"failure", "failed", "error"}:
        tool_state = ToolStatus.FAILED.value
    else:
        tool_state = ToolStatus.SUCCESS.value
    if any(warn.startswith(("cpu_fallback:", "cpu_mode:")) for warn in warnings):
        tool_state = ToolStatus.DEGRADED.value

    failure_value = None
    if status == "failure" and failure_type and failure_type != FailureType.NONE.value:
        failure_value = failure_type

    return {
        "run_id": context.run_id,
        "candidate_id": candidate_id,
        "command": command,
        "execution_status": execution_status,
        "workflow_state": workflow_state,
        "outcome": outcome,
        "provider": provider_name,
        "tool_status": tool_state,
        "qc_status": qc_status,
        "artifacts_dir": str(context.workspace.run_dir),
        "warnings": sorted(warnings),
        "failure": failure_value,
        "version": {
            "app": version_info.app_version,
            "git_commit": version_info.git_commit,
            "tool_versions": version_info.tool_versions,
        },
    }


def _load_preflight_report_if_available(
    workspace: Any,
) -> RuntimePreflightReport | None:
    if not workspace.preflight_report_path.exists():
        return None
    return RuntimePreflightReport.load_json(workspace.preflight_report_path)


def _version_info(tool: Tool | None) -> VersionInfo:
    """_version_info."""
    tool_versions = {}
    if tool is not None:
        tool_versions[tool.name] = tool.version
    try:
        app_version = importlib.metadata.version("bijux-proteomics-runtime")
    except importlib.metadata.PackageNotFoundError:
        app_version = "unknown"
    return VersionInfo(
        app_version=app_version, git_commit="unknown", tool_versions=tool_versions
    )


def _select_structure_tool(config: dict[str, Any]) -> Tool:
    """Select a structure tool based on enabled providers."""
    enabled = config.get("predictors_enabled", []) or []
    provider_name = enabled[0] if enabled else HeuristicStructureTool.name
    return HeuristicStructureTool(provider_name=provider_name)


def _ensure_telemetry_costs(context: RunContext) -> None:
    """_ensure_telemetry_costs."""
    for name in ("tool_units", "cpu_seconds", "gpu_seconds"):
        if name not in context.telemetry.cost:
            context.telemetry.add_cost(name, 0.0)


def run_flow(
    candidate: Candidate, run_context: RunContext, tool: Tool | None = None
) -> dict[str, Any]:
    """Run the canonical agentic flow end-to-end."""
    machine = RuntimeStateMachine(run_context, tool)
    return machine.run(candidate)
