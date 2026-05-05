from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.runtime.context import (
    build_run_context_contract,
    create_run_context,
)
from bijux_proteomics_runtime.runtime.control import (
    apply_runtime_cleanup_plan,
    build_replay_contract,
    build_runtime_cleanup_plan,
    build_runtime_failure_recovery_audit,
    refresh_runtime_artifact_ledger,
    verify_runtime_artifact_integrity,
)
from bijux_proteomics_runtime.runtime.workspace import write_json_atomic


def _seed_runtime_outputs(
    tmp_path: Path,
    *,
    run_id: str,
    failure: str | None = None,
) -> object:
    context, _ = create_run_context(tmp_path, run_id=run_id)
    run_context = build_run_context_contract(
        run_id=context.run_id,
        started_at=context.start_time.isoformat(),
        base_dir=tmp_path,
        config=context.config,
        provider_name="heuristic_proxy",
        artifact_policy=context.artifact_policy,
        sequence="MPEPTIDE",
        command="run",
        workflow_family="sequence_to_digest",
        candidate_id=f"{run_id}-c0",
    )
    replay_contract = build_replay_contract(
        run_context,
        app_version="1.2.3",
        git_commit="abc123",
        tool_versions={"heuristic_proxy": "0.1"},
    )
    write_json_atomic(context.workspace.run_context_path, run_context.to_dict())
    write_json_atomic(context.workspace.replay_contract_path, replay_contract.to_dict())
    write_json_atomic(context.workspace.report_path, {"status": "ok", "steps": ["digest"]})
    write_json_atomic(
        context.workspace.run_summary_path,
        {
            "run_id": context.run_id,
            "candidate_id": f"{run_id}-c0",
            "command": "run",
            "execution_status": "errored" if failure else "completed",
            "workflow_state": "done",
            "outcome": "inconclusive" if failure else "accepted",
            "provider": "heuristic_proxy",
            "tool_status": "failed" if failure else "success",
            "qc_status": "acceptable",
            "artifacts_dir": str(context.workspace.run_dir),
            "warnings": [],
            "failure": failure,
            "version": {
                "app": "0+local",
                "git_commit": "unknown",
                "tool_versions": {"heuristic_proxy": "0.1"},
            },
        },
    )
    refresh_runtime_artifact_ledger(
        context.workspace,
        run_id=context.run_id,
        artifact_policy=context.artifact_policy,
        producer="test",
    )
    verify_runtime_artifact_integrity(
        context.workspace,
        run_id=context.run_id,
        max_artifact_bytes=1_000_000,
    )
    return context


def test_runtime_cleanup_preserves_review_and_replay_outputs(tmp_path: Path) -> None:
    context = _seed_runtime_outputs(tmp_path, run_id="cleanup-1")

    plan = build_runtime_cleanup_plan(context.workspace, run_id=context.run_id)
    apply_runtime_cleanup_plan(plan)

    removable_kinds = {artifact.artifact_kind for artifact in plan.removable_artifacts}
    preserved_kinds = {artifact.artifact_kind for artifact in plan.preserved_artifacts}

    assert "runtime-state" in removable_kinds
    assert "runtime-status" in preserved_kinds
    assert "runtime-replay-contract" in preserved_kinds
    assert not context.workspace.state_path.exists()
    assert context.workspace.run_summary_path.exists()
    assert context.workspace.replay_contract_path.exists()


def test_runtime_failure_recovery_keeps_previous_good_artifacts_after_partial_failure(
    tmp_path: Path,
) -> None:
    context = _seed_runtime_outputs(
        tmp_path,
        run_id="recovery-1",
        failure="tool_timeout",
    )

    audit = build_runtime_failure_recovery_audit(
        context.workspace,
        run_id=context.run_id,
    )

    assert audit.partial_failure is True
    preserved_kinds = {artifact.artifact_kind for artifact in audit.preserved_artifacts}
    assert "runtime-report" in preserved_kinds
    assert "runtime-replay-contract" in preserved_kinds
