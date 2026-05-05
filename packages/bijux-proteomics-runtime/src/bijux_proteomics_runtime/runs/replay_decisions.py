# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Operator-facing replay decision reports for runtime reruns."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.runs.reruns import (
    PartialRerunPlan,
    build_runtime_partial_rerun_plan,
)
from bijux_proteomics_runtime.runs.replay import ReplayContract
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace, write_json_atomic


class ReplayDecisionFinding(JsonModel):
    """One precise operator-facing explanation for replay invalidation."""

    model_config = ConfigDict(extra="forbid")

    reason_code: str = Field(..., min_length=1)
    boundary_node: str = Field(..., min_length=1)
    effect: str = Field(..., min_length=1)
    operator_guidance: str = Field(..., min_length=1)


class RuntimeReplayDecisionReport(JsonModel):
    """Stable report that explains runtime replay and partial rerun decisions."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    source_lineage_run_id: str = Field(..., min_length=1)
    import_only: bool
    replay_safe: bool
    earliest_invalidation_boundary: str = Field(..., min_length=1)
    findings: tuple[ReplayDecisionFinding, ...] = Field(default_factory=tuple)
    reuse_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    rerun_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    operator_summary: str = Field(..., min_length=1)
    notes: tuple[str, ...] = Field(default_factory=tuple)


def build_runtime_replay_decision_report(
    plan: PartialRerunPlan,
) -> RuntimeReplayDecisionReport:
    """Explain one replay decision in stable operator-facing terms."""
    boundary_node = (
        plan.rerun_steps[0].node_id if plan.rerun_steps else "handoff"
    )
    findings = tuple(
        ReplayDecisionFinding(
            reason_code=reason_code,
            boundary_node=_boundary_node_for_reason(
                reason_code,
                import_only=plan.import_only,
            ),
            effect=_effect_for_reason(reason_code, import_only=plan.import_only),
            operator_guidance=_guidance_for_reason(
                reason_code,
                import_only=plan.import_only,
            ),
        )
        for reason_code in plan.replay_eligibility.invalidation_reasons
    )
    reuse_node_ids = tuple(step.node_id for step in plan.reuse_steps)
    rerun_node_ids = tuple(step.node_id for step in plan.rerun_steps)
    return RuntimeReplayDecisionReport(
        run_id=plan.run_id,
        source_lineage_run_id=plan.source_lineage_run_id,
        import_only=plan.import_only,
        replay_safe=plan.replay_eligibility.eligible,
        earliest_invalidation_boundary=boundary_node,
        findings=findings,
        reuse_node_ids=reuse_node_ids,
        rerun_node_ids=rerun_node_ids,
        operator_summary=_operator_summary(
            plan=plan,
            reuse_node_ids=reuse_node_ids,
            rerun_node_ids=rerun_node_ids,
            boundary_node=boundary_node,
        ),
        notes=plan.notes,
    )


def build_workspace_replay_decision_report(
    workspace: RunWorkspace,
    current_replay_contract: ReplayContract,
) -> RuntimeReplayDecisionReport:
    """Load persisted rerun inputs and explain the replay decision."""
    plan = build_runtime_partial_rerun_plan(workspace, current_replay_contract)
    return build_runtime_replay_decision_report(plan)


def write_runtime_replay_decision_report(
    workspace: RunWorkspace,
    report: RuntimeReplayDecisionReport,
) -> None:
    """Persist one replay decision report."""
    write_json_atomic(workspace.replay_decision_report_path, report.to_dict())


def load_runtime_replay_decision_report(
    workspace: RunWorkspace,
) -> RuntimeReplayDecisionReport:
    """Load one persisted replay decision report."""
    return RuntimeReplayDecisionReport.load_json(workspace.replay_decision_report_path)


def _boundary_node_for_reason(reason_code: str, *, import_only: bool) -> str:
    if reason_code == "input_changed":
        return "imported_evidence" if import_only else "dataset_input"
    if reason_code in {
        "parameters_changed",
        "tools_changed",
        "code_expectations_changed",
    }:
        return "review" if import_only else "execution"
    return "handoff"


def _effect_for_reason(reason_code: str, *, import_only: bool) -> str:
    if reason_code == "input_changed":
        return (
            "import provenance and every downstream review output must be rebuilt"
            if import_only
            else "input capture and every downstream execution output must be rebuilt"
        )
    if reason_code == "parameters_changed":
        return "parameter drift invalidates replay at the execution boundary"
    if reason_code == "tools_changed":
        return "tool drift invalidates replay at the execution boundary"
    if reason_code == "code_expectations_changed":
        return "runtime code expectations changed and block exact replay reuse"
    if reason_code == "artifact_policy_changed":
        return "artifact retention policy changed and requires fresh review outputs"
    return "runtime replay safety requires explicit operator review"


def _guidance_for_reason(reason_code: str, *, import_only: bool) -> str:
    if reason_code == "input_changed":
        return (
            "capture the new external evidence and regenerate review outputs"
            if import_only
            else "rebuild the run from input capture forward"
        )
    if reason_code in {"parameters_changed", "tools_changed"}:
        return "reuse only nodes before the execution boundary and rerun execution onward"
    if reason_code == "code_expectations_changed":
        return "rerun the execution path under the current runtime build"
    if reason_code == "artifact_policy_changed":
        return "refresh reviewable artifacts under the current retention policy"
    return "inspect the replay contract difference before reusing artifacts"


def _operator_summary(
    *,
    plan: PartialRerunPlan,
    reuse_node_ids: tuple[str, ...],
    rerun_node_ids: tuple[str, ...],
    boundary_node: str,
) -> str:
    if plan.replay_eligibility.eligible:
        return (
            "replay is safe because dependency fingerprints still match; "
            f"runtime can reuse {len(reuse_node_ids)} dependency nodes without rerunning execution"
        )
    return (
        f"replay is not safe because {', '.join(plan.replay_eligibility.invalidation_reasons)} "
        f"cross the {boundary_node} boundary; runtime will reuse {len(reuse_node_ids)} nodes "
        f"and rerun {len(rerun_node_ids)} nodes"
    )


__all__ = [
    "ReplayDecisionFinding",
    "RuntimeReplayDecisionReport",
    "build_runtime_replay_decision_report",
    "build_workspace_replay_decision_report",
    "load_runtime_replay_decision_report",
    "write_runtime_replay_decision_report",
]
