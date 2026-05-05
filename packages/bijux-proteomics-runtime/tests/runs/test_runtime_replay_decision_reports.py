from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.runs import (
    RuntimeArtifactRetentionClass,
    build_run_context_contract,
    create_run_context,
)
from bijux_proteomics_runtime.runs.ledger import ArtifactLedgerEntry
from bijux_proteomics_runtime.runs.ledger import RuntimeArtifactLedger
from bijux_proteomics_runtime.runs.ledger import refresh_runtime_artifact_ledger
from bijux_proteomics_runtime.runs.replay import build_replay_contract
from bijux_proteomics_runtime.runs.replay_decisions import (
    RuntimeReplayDecisionReport,
    build_runtime_replay_decision_report,
    build_workspace_replay_decision_report,
    load_runtime_replay_decision_report,
    write_runtime_replay_decision_report,
)
from bijux_proteomics_runtime.runs.reruns import build_partial_rerun_plan
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace, write_json_atomic


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


def test_runtime_replay_decision_report_explains_exact_reuse(
    tmp_path: Path,
) -> None:
    previous_context, previous_contract = _contract(tmp_path, run_id="replay-report-1")
    _same_context, current_contract = _contract(tmp_path, run_id="replay-report-1")
    plan = build_partial_rerun_plan(
        previous_run_context=previous_context,
        previous_replay_contract=previous_contract,
        current_replay_contract=current_contract,
        artifact_ledger=_ledger(
            "replay-report-1",
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

    report = build_runtime_replay_decision_report(plan)

    assert report.replay_safe is True
    assert report.findings == ()
    assert report.rerun_node_ids == ()
    assert report.reuse_node_ids == (
        "dataset_input",
        "planning",
        "execution",
        "review",
        "handoff",
    )


def test_runtime_replay_decision_report_marks_boundary_and_reruns(
    tmp_path: Path,
) -> None:
    previous_context, previous_contract = _contract(tmp_path, run_id="replay-report-2")
    _changed_context, current_contract = _contract(
        tmp_path,
        run_id="replay-report-2",
        provider_name="local_esmfold",
    )
    plan = build_partial_rerun_plan(
        previous_run_context=previous_context,
        previous_replay_contract=previous_contract,
        current_replay_contract=current_contract,
        artifact_ledger=_ledger(
            "replay-report-2",
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

    report = build_runtime_replay_decision_report(plan)

    assert report.replay_safe is False
    assert report.earliest_invalidation_boundary == "execution"
    assert [finding.reason_code for finding in report.findings] == [
        "parameters_changed",
        "tools_changed",
    ]
    assert report.reuse_node_ids == ("dataset_input", "planning")
    assert report.rerun_node_ids == ("execution", "review", "handoff")


def test_runtime_workspace_replay_decision_report_persists_as_artifact(
    tmp_path: Path,
) -> None:
    previous_context, previous_contract = _contract(
        tmp_path,
        run_id="replay-report-3",
        import_only=True,
    )
    workspace = RunWorkspace.for_run(tmp_path, "replay-report-3")
    write_json_atomic(workspace.run_context_path, previous_context.to_dict())
    write_json_atomic(workspace.replay_contract_path, previous_contract.to_dict())
    write_json_atomic(
        workspace.artifact_ledger_path,
        _ledger(
            "replay-report-3",
            "runtime-import-trace",
            "runtime-status",
            "runtime-import-run-bundle",
            "runtime-replay-contract",
            "runtime-integrity-report",
        ).to_dict(),
    )

    report = build_workspace_replay_decision_report(workspace, previous_contract)
    write_runtime_replay_decision_report(workspace, report)
    ledger = refresh_runtime_artifact_ledger(
        workspace,
        run_id="replay-report-3",
        artifact_policy=previous_context.artifact_policy,
        producer="test",
    )
    reloaded = load_runtime_replay_decision_report(workspace)

    assert isinstance(reloaded, RuntimeReplayDecisionReport)
    assert reloaded.import_only is True
    assert any(
        entry.artifact_kind == "runtime-replay-decision-report"
        for entry in ledger.entries
    )
