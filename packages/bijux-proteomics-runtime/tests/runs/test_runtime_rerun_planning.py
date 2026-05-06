from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.runs import (
    RuntimeArtifactRetentionClass,
    build_run_context_contract,
    create_run_context,
)
from bijux_proteomics_runtime.runs.ledger import ArtifactLedgerEntry
from bijux_proteomics_runtime.runs.ledger import RuntimeArtifactLedger
from bijux_proteomics_runtime.runs.replay import build_replay_contract
from bijux_proteomics_runtime.runs.reruns import PartialRerunPlan
from bijux_proteomics_runtime.runs.reruns import build_partial_rerun_plan
from bijux_proteomics_runtime.runs.reruns import build_runtime_partial_rerun_plan
from bijux_proteomics_runtime.support.workspace import write_json_atomic


def _contract(
    tmp_path: Path,
    *,
    run_id: str,
    provider_name: str = "heuristic_proxy",
    sequence: str = "MPEPTIDE",
    import_only: bool = False,
) -> tuple[object, object]:
    context, _ = create_run_context(tmp_path, run_id=run_id)
    run_context = build_run_context_contract(
        run_id=context.run_id,
        started_at=context.start_time.isoformat(),
        base_dir=tmp_path,
        config=context.config,
        provider_name=provider_name,
        artifact_policy=context.artifact_policy,
        sequence=sequence,
        command="import" if import_only else "run",
        workflow_family="external_import" if import_only else "sequence_to_digest",
        candidate_id=f"{run_id}-c0",
        import_only=import_only,
    )
    replay_contract = build_replay_contract(
        run_context,
        app_version="1.2.3",
        git_commit="abc123",
        tool_versions={provider_name: "0.1"},
    )
    return run_context, replay_contract


def _ledger(run_id: str, *artifact_kinds: str) -> RuntimeArtifactLedger:
    return RuntimeArtifactLedger(
        run_id=run_id,
        entries=tuple(
            ArtifactLedgerEntry(
                artifact_role=f"role-{index}",
                artifact_kind=artifact_kind,
                path=f"/tmp/{run_id}/{artifact_kind}.json",
                producer="test",
                retention_class=RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
                content_sha256="0" * 64,
                size_bytes=16,
            )
            for index, artifact_kind in enumerate(artifact_kinds)
        ),
    )


def test_runtime_replay_requires_exact_fingerprint_match_for_safe_reruns(
    tmp_path: Path,
) -> None:
    previous_context, previous_contract = _contract(tmp_path, run_id="rerun-safe-1")
    _same_context, changed_contract = _contract(
        tmp_path,
        run_id="rerun-safe-1",
        provider_name="local_esmfold",
    )

    plan = build_partial_rerun_plan(
        previous_run_context=previous_context,
        previous_replay_contract=previous_contract,
        current_replay_contract=changed_contract,
        artifact_ledger=_ledger(
            "rerun-safe-1",
            "runtime-run-context",
            "runtime-plan",
            "runtime-replay-contract",
            "runtime-status",
            "runtime-report",
            "runtime-local-run-bundle",
            "runtime-integrity-report",
            "runtime-artifact-item",
        ),
    )

    assert plan.replay_eligibility.eligible is False
    assert "tools_changed" in plan.replay_eligibility.invalidation_reasons
    assert plan.rerun_steps[0].node_id == "execution"


def test_runtime_partial_rerun_reuses_pre_execution_nodes_when_tools_change(
    tmp_path: Path,
) -> None:
    previous_context, previous_contract = _contract(tmp_path, run_id="rerun-plan-1")
    _changed_context, changed_contract = _contract(
        tmp_path,
        run_id="rerun-plan-1",
        provider_name="local_esmfold",
    )

    plan = build_partial_rerun_plan(
        previous_run_context=previous_context,
        previous_replay_contract=previous_contract,
        current_replay_contract=changed_contract,
        artifact_ledger=_ledger(
            "rerun-plan-1",
            "runtime-run-context",
            "runtime-plan",
            "runtime-replay-contract",
            "runtime-status",
            "runtime-report",
            "runtime-local-run-bundle",
            "runtime-integrity-report",
            "runtime-artifact-item",
        ),
    )

    assert [step.node_id for step in plan.reuse_steps] == ["dataset_input", "planning"]
    assert [step.node_id for step in plan.rerun_steps] == [
        "execution",
        "review",
        "handoff",
    ]


def test_runtime_partial_rerun_requires_full_rerun_when_input_changes(
    tmp_path: Path,
) -> None:
    previous_context, previous_contract = _contract(tmp_path, run_id="rerun-plan-2")
    _changed_context, changed_contract = _contract(
        tmp_path,
        run_id="rerun-plan-2",
        sequence="MOTHERPEPTIDE",
    )

    plan = build_partial_rerun_plan(
        previous_run_context=previous_context,
        previous_replay_contract=previous_contract,
        current_replay_contract=changed_contract,
        artifact_ledger=_ledger(
            "rerun-plan-2",
            "runtime-run-context",
            "runtime-plan",
            "runtime-replay-contract",
            "runtime-status",
        ),
    )

    assert plan.reuse_steps == ()
    assert plan.rerun_steps[0].node_id == "dataset_input"
    assert plan.rerun_steps[-1].node_id == "handoff"


def test_runtime_workspace_rerun_plan_loads_import_lineage_graph(
    tmp_path: Path,
) -> None:
    previous_context, previous_contract = _contract(
        tmp_path,
        run_id="rerun-import-1",
        import_only=True,
    )
    workspace = (create_run_context(tmp_path, run_id="rerun-import-1"))[0].workspace
    write_json_atomic(workspace.run_context_path, previous_context.to_dict())
    write_json_atomic(workspace.replay_contract_path, previous_contract.to_dict())
    write_json_atomic(
        workspace.artifact_ledger_path,
        _ledger(
            "rerun-import-1",
            "runtime-import-trace",
            "runtime-status",
            "runtime-import-run-bundle",
            "runtime-replay-contract",
            "runtime-integrity-report",
        ).to_dict(),
    )

    plan = build_runtime_partial_rerun_plan(workspace, previous_contract)

    assert isinstance(plan, PartialRerunPlan)
    assert plan.import_only is True
    assert [node.node_id for node in plan.dependency_graph] == [
        "imported_evidence",
        "review",
        "handoff",
    ]
