# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime-owned replay boundary and partial rerun planning."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.runtime.context import RunContextContract
from bijux_proteomics_runtime.runtime.control.ledger import RuntimeArtifactLedger
from bijux_proteomics_runtime.runtime.control.replay import (
    ReplayContract,
    ReplayEligibility,
    evaluate_replay_eligibility,
)
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace


class RuntimeDependencyNode(JsonModel):
    """One runtime-owned dependency node for replay and partial reruns."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    depends_on: tuple[str, ...] = Field(default_factory=tuple)
    produced_artifact_kinds: tuple[str, ...] = Field(default_factory=tuple)


class PartialRerunStep(JsonModel):
    """One reuse or rerun decision for a dependency node."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    produced_artifact_kinds: tuple[str, ...] = Field(default_factory=tuple)


class PartialRerunPlan(JsonModel):
    """Replay boundary plan grounded in dependency graph and artifact lineage."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    source_lineage_run_id: str = Field(..., min_length=1)
    import_only: bool
    replay_eligibility: ReplayEligibility
    dependency_graph: tuple[RuntimeDependencyNode, ...] = Field(default_factory=tuple)
    reuse_steps: tuple[PartialRerunStep, ...] = Field(default_factory=tuple)
    rerun_steps: tuple[PartialRerunStep, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


def build_runtime_dependency_graph(
    *,
    import_only: bool,
) -> tuple[RuntimeDependencyNode, ...]:
    """Return the runtime dependency graph for standard and import-only flows."""
    if import_only:
        return (
            RuntimeDependencyNode(
                node_id="imported_evidence",
                description="capture third-party evidence and provenance into runtime-owned import artifacts",
                produced_artifact_kinds=("runtime-import-trace",),
            ),
            RuntimeDependencyNode(
                node_id="review",
                description="publish review-facing status and import bundle outputs",
                depends_on=("imported_evidence",),
                produced_artifact_kinds=(
                    "runtime-status",
                    "runtime-import-run-bundle",
                    "runtime-replay-contract",
                ),
            ),
            RuntimeDependencyNode(
                node_id="handoff",
                description="publish downstream reviewable path and integrity outputs",
                depends_on=("review",),
                produced_artifact_kinds=("runtime-integrity-report",),
            ),
        )
    return (
        RuntimeDependencyNode(
            node_id="dataset_input",
            description="capture sequence input and run context for canonical execution",
            produced_artifact_kinds=("runtime-run-context",),
        ),
        RuntimeDependencyNode(
            node_id="planning",
            description="persist plan and replay boundary inputs before execution",
            depends_on=("dataset_input",),
            produced_artifact_kinds=("runtime-plan", "runtime-replay-contract"),
        ),
        RuntimeDependencyNode(
            node_id="execution",
            description="run canonical execution and persist status plus report outputs",
            depends_on=("planning",),
            produced_artifact_kinds=(
                "runtime-status",
                "runtime-report",
                "runtime-local-run-bundle",
            ),
        ),
        RuntimeDependencyNode(
            node_id="review",
            description="publish review-facing integrity evidence for completed execution",
            depends_on=("execution",),
            produced_artifact_kinds=("runtime-integrity-report",),
        ),
        RuntimeDependencyNode(
            node_id="handoff",
            description="publish reviewable downstream handoff path for consumers",
            depends_on=("review",),
            produced_artifact_kinds=("runtime-artifact-item",),
        ),
    )


def build_partial_rerun_plan(
    *,
    previous_run_context: RunContextContract,
    previous_replay_contract: ReplayContract,
    current_replay_contract: ReplayContract,
    artifact_ledger: RuntimeArtifactLedger,
) -> PartialRerunPlan:
    """Build a partial rerun plan from replay contracts and retained artifacts."""
    replay_eligibility = evaluate_replay_eligibility(
        previous_replay_contract,
        current_replay_contract,
    )
    graph = build_runtime_dependency_graph(
        import_only=previous_run_context.workflow.import_only
    )
    boundary_node = _boundary_node_for_reasons(
        replay_eligibility.invalidation_reasons,
        import_only=previous_run_context.workflow.import_only,
    )
    available_artifact_kinds = {
        entry.artifact_kind for entry in artifact_ledger.entries
    }
    reuse_steps: list[PartialRerunStep] = []
    rerun_steps: list[PartialRerunStep] = []
    boundary_reached = False
    for node in graph:
        if node.node_id == boundary_node:
            boundary_reached = True
        can_reuse = replay_eligibility.eligible or (
            not boundary_reached
            and set(node.produced_artifact_kinds).issubset(available_artifact_kinds)
        )
        if can_reuse:
            reuse_steps.append(
                PartialRerunStep(
                    node_id=node.node_id,
                    action="reuse",
                    reason=(
                        "replay fingerprints still match exactly"
                        if replay_eligibility.eligible
                        else "dependency node precedes the invalidation boundary and required artifacts still exist"
                    ),
                    produced_artifact_kinds=node.produced_artifact_kinds,
                )
            )
            continue
        rerun_steps.append(
            PartialRerunStep(
                node_id=node.node_id,
                action="rerun",
                reason=(
                    "dependency node sits on or after the invalidation boundary"
                    if boundary_reached
                    else "required artifacts are missing from runtime lineage"
                ),
                produced_artifact_kinds=node.produced_artifact_kinds,
            )
        )
    return PartialRerunPlan(
        run_id=current_replay_contract.run_id,
        source_lineage_run_id=previous_run_context.run_id,
        import_only=previous_run_context.workflow.import_only,
        replay_eligibility=replay_eligibility,
        dependency_graph=graph,
        reuse_steps=tuple(reuse_steps),
        rerun_steps=tuple(rerun_steps),
        notes=_plan_notes(replay_eligibility, boundary_node),
    )


def build_runtime_partial_rerun_plan(
    workspace: RunWorkspace,
    current_replay_contract: ReplayContract,
) -> PartialRerunPlan:
    """Load one persisted run and build a runtime-owned partial rerun plan."""
    previous_run_context = RunContextContract.load_json(workspace.run_context_path)
    previous_replay_contract = ReplayContract.load_json(workspace.replay_contract_path)
    artifact_ledger = RuntimeArtifactLedger.load_json(workspace.artifact_ledger_path)
    return build_partial_rerun_plan(
        previous_run_context=previous_run_context,
        previous_replay_contract=previous_replay_contract,
        current_replay_contract=current_replay_contract,
        artifact_ledger=artifact_ledger,
    )


def _boundary_node_for_reasons(
    invalidation_reasons: tuple[str, ...],
    *,
    import_only: bool,
) -> str:
    if not invalidation_reasons:
        return "handoff"
    if "input_changed" in invalidation_reasons:
        return "imported_evidence" if import_only else "dataset_input"
    if {
        "parameters_changed",
        "tools_changed",
        "code_expectations_changed",
    } & set(invalidation_reasons):
        return "review" if import_only else "execution"
    return "handoff" if not import_only else "handoff"


def _plan_notes(
    replay_eligibility: ReplayEligibility,
    boundary_node: str,
) -> tuple[str, ...]:
    if replay_eligibility.eligible:
        return (
            "runtime rerun is safe because replay fingerprints still match exactly",
        )
    return (
        "runtime rerun is not fully replay-safe because one or more dependency fingerprints changed",
        f"earliest invalidation boundary: {boundary_node}",
    )


__all__ = [
    "PartialRerunPlan",
    "PartialRerunStep",
    "RuntimeDependencyNode",
    "build_partial_rerun_plan",
    "build_runtime_dependency_graph",
    "build_runtime_partial_rerun_plan",
]
