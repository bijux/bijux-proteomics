from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.runs import (
    RunConfig,
    RunContextContract,
    RuntimeArtifactRetentionClass,
    RuntimeDatasetKind,
    build_run_context_contract,
    create_run_context,
)


def test_runtime_context_contract_captures_dataset_workflow_environment_and_policy(
    tmp_path: Path,
) -> None:
    context, warnings = create_run_context(
        tmp_path,
        RunConfig(predictors_enabled=["heuristic_proxy"]),
        run_id="run-context-1",
    )

    contract = build_run_context_contract(
        run_id=context.run_id,
        started_at=context.start_time.isoformat(),
        base_dir=tmp_path,
        config=context.config,
        provider_name="heuristic_proxy",
        artifact_policy=context.artifact_policy,
        sequence="ACDEFGHIKLMNPQRSTVWY",
        command="run",
        workflow_family="structure_prediction",
        candidate_id="run-context-1-c0",
    )

    assert warnings
    assert isinstance(contract, RunContextContract)
    assert contract.dataset.dataset_kind is RuntimeDatasetKind.INLINE_SEQUENCE
    assert contract.workflow.command == "run"
    assert contract.workflow.workflow_family == "structure_prediction"
    assert contract.provider_name == "heuristic_proxy"
    assert contract.environment.working_directory == str(tmp_path.resolve())
    assert (
        contract.artifact_policy.retention_by_role["runtime-report"]
        is RuntimeArtifactRetentionClass.REVIEW_REQUIRED
    )


def test_runtime_workspace_exposes_integrity_artifact_paths(tmp_path: Path) -> None:
    context, _ = create_run_context(tmp_path, run_id="run-context-paths")
    workspace = context.workspace

    assert workspace.run_context_path.name == "run_context.json"
    assert workspace.artifact_ledger_path.name == "artifact_ledger.json"
    assert workspace.replay_contract_path.name == "replay_contract.json"
    assert workspace.local_run_bundle_path.name == "local_run_bundle.json"
    assert workspace.preflight_report_path.name == "preflight_report.json"
    assert workspace.failure_report_path.name == "failure_report.json"
