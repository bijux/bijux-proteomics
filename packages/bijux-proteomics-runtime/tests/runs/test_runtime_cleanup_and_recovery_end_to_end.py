from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.runs.checkpoints import write_resume_checkpoint
from bijux_proteomics_runtime.runs.cleanup import (
    apply_runtime_cleanup_plan,
    build_runtime_cleanup_plan,
)
from bijux_proteomics_runtime.runs.context import create_run_context
from bijux_proteomics_runtime.runs.contracts import build_run_context_contract
from bijux_proteomics_runtime.runs.failure_reports import build_runtime_failure_report
from bijux_proteomics_runtime.runs.failure_reports import write_runtime_failure_report
from bijux_proteomics_runtime.runs.integrity import verify_runtime_artifact_integrity
from bijux_proteomics_runtime.runs.ledger import (
    load_artifact_ledger,
    refresh_runtime_artifact_ledger,
)
from bijux_proteomics_runtime.runs.recovery import build_runtime_failure_recovery_audit
from bijux_proteomics_runtime.runs.replay import (
    build_local_run_bundle,
    build_replay_contract,
    load_local_run_bundle,
    write_local_run_bundle,
    write_replay_contract,
)
from bijux_proteomics_runtime.runs.checkpoints import build_resume_checkpoint
from bijux_proteomics_runtime.runtime.workspace import write_json_atomic

from ..support.fixture_data import load_fixture


def _seed_runtime_bundle(
    tmp_path: Path,
    *,
    run_id: str,
    sequence: str,
    provider_name: str,
    failure_type: str | None = None,
    detail_codes: tuple[str, ...] = (),
):
    context, _ = create_run_context(tmp_path, run_id=run_id)
    run_context = build_run_context_contract(
        run_id=context.run_id,
        started_at=context.start_time.isoformat(),
        base_dir=tmp_path,
        config=context.config,
        provider_name=provider_name,
        artifact_policy=context.artifact_policy,
        sequence=sequence,
        command="run",
        workflow_family="structure_prediction",
        candidate_id=f"{run_id}-c0",
    )
    replay_contract = build_replay_contract(
        run_context,
        app_version="1.2.3",
        git_commit="abc123",
        tool_versions={provider_name: "0.1"},
    )
    write_json_atomic(context.workspace.run_context_path, run_context.to_dict())
    write_replay_contract(context.workspace, replay_contract)
    write_json_atomic(context.workspace.report_path, {"status": "ok", "steps": ["run"]})
    write_json_atomic(
        context.workspace.run_summary_path,
        {
            "run_id": context.run_id,
            "candidate_id": f"{run_id}-c0",
            "command": "run",
            "execution_status": "errored" if failure_type else "completed",
            "workflow_state": "done",
            "outcome": "inconclusive" if failure_type else "accepted",
            "provider": provider_name,
            "tool_status": "failed" if failure_type else "success",
            "qc_status": "acceptable",
            "artifacts_dir": str(context.workspace.run_dir),
            "warnings": list(detail_codes),
            "failure": failure_type,
            "version": {
                "app": "0+local",
                "git_commit": "unknown",
                "tool_versions": {provider_name: "0.1"},
            },
        },
    )
    refresh_runtime_artifact_ledger(
        context.workspace,
        run_id=context.run_id,
        artifact_policy=context.artifact_policy,
        producer="test",
    )
    bundle = build_local_run_bundle(
        run_context=run_context,
        replay_contract=replay_contract,
        artifact_ledger=load_artifact_ledger(context.workspace, context.run_id),
        run_summary={"run_id": context.run_id, "outcome": "accepted"},
    )
    write_local_run_bundle(context.workspace, bundle)
    refresh_runtime_artifact_ledger(
        context.workspace,
        run_id=context.run_id,
        artifact_policy=context.artifact_policy,
        producer="test",
    )
    if failure_type is not None:
        write_runtime_failure_report(
            context.workspace,
            build_runtime_failure_report(
                run_id=context.run_id,
                failure_type=failure_type,
                message=";".join(detail_codes) or failure_type,
                detail_codes=detail_codes,
            ),
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


def test_runtime_cleanup_keeps_reusable_bundle_after_failed_run(tmp_path: Path) -> None:
    fixture = load_fixture("execution", "failure_recovery_paths.json")
    case = fixture["cleanup_reuse_case"]
    context = _seed_runtime_bundle(
        tmp_path,
        run_id=str(case["run_id"]),
        sequence=str(case["sequence"]),
        provider_name=str(case["provider_name"]),
        failure_type="tool_timeout",
        detail_codes=("tool_timeout",),
    )

    plan = build_runtime_cleanup_plan(context.workspace, run_id=context.run_id)
    apply_runtime_cleanup_plan(plan)
    bundle = load_local_run_bundle(context.workspace)

    assert bundle.run_context.run_id == context.run_id
    assert context.workspace.run_summary_path.exists()
    assert context.workspace.replay_contract_path.exists()
    assert context.workspace.local_run_bundle_path.exists()


def test_runtime_failure_recovery_cases_produce_operator_actions(
    tmp_path: Path,
) -> None:
    fixture = load_fixture("execution", "failure_recovery_paths.json")

    for case in fixture["recovery_cases"]:
        context = _seed_runtime_bundle(
            tmp_path,
            run_id=str(case["run_id"]),
            sequence="MPEPTIDEKAAALSYIFCLVFADYK",
            provider_name="heuristic_proxy",
            failure_type=str(case["failure_type"]),
            detail_codes=tuple(str(code) for code in case["detail_codes"]),
        )
        if case.get("write_resume_checkpoint"):
            checkpoint = build_resume_checkpoint(
                run_context=load_local_run_bundle(context.workspace).run_context,
                status="partial",
                lifecycle_state="human_review",
                command="resume",
            )
            assert checkpoint is not None
            write_resume_checkpoint(context.workspace, checkpoint)

        audit = build_runtime_failure_recovery_audit(
            context.workspace,
            run_id=context.run_id,
        )

        assert audit.failure_category.value == case["expected_failure_category"]
        assert audit.recovery_action.value == case["expected_recovery_action"]
        assert audit.partial_failure is True
        assert audit.preserved_artifacts
        assert "preserved artifacts remain reusable" in audit.operator_summary
