from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.runs import (
    build_run_context_contract,
    create_run_context,
)
from bijux_proteomics_runtime.runs.ledger import (
    RuntimeArtifactLedger,
    refresh_runtime_artifact_ledger,
)
from bijux_proteomics_runtime.runs.replay import (
    LocalRunBundle,
    build_local_run_bundle,
    build_replay_contract,
    evaluate_replay_eligibility,
    write_local_run_bundle,
)
from bijux_proteomics_runtime.runtime.workspace import write_json_atomic


def _contract(tmp_path: Path, *, run_id: str, provider_name: str = "heuristic_proxy"):
    context, _ = create_run_context(tmp_path, run_id=run_id)
    return build_run_context_contract(
        run_id=context.run_id,
        started_at=context.start_time.isoformat(),
        base_dir=tmp_path,
        config=context.config,
        provider_name=provider_name,
        artifact_policy=context.artifact_policy,
        sequence="ACDEFGHIKLMNPQRSTVWY",
        command="run",
        workflow_family="structure_prediction",
        candidate_id=f"{run_id}-c0",
    )


def test_runtime_replay_contract_marks_matching_fingerprints_eligible(
    tmp_path: Path,
) -> None:
    contract = _contract(tmp_path, run_id="replay-run-1")
    expected = build_replay_contract(
        contract,
        app_version="1.2.3",
        git_commit="abc123",
        tool_versions={"heuristic_proxy": "0.1"},
    )
    current = build_replay_contract(
        contract,
        app_version="1.2.3",
        git_commit="abc123",
        tool_versions={"heuristic_proxy": "0.1"},
    )

    decision = evaluate_replay_eligibility(expected, current)

    assert decision.eligible is True
    assert decision.invalidation_reasons == ()


def test_runtime_replay_contract_reports_precise_invalidation_reasons(
    tmp_path: Path,
) -> None:
    baseline = _contract(tmp_path, run_id="replay-run-2")
    changed = _contract(tmp_path, run_id="replay-run-2", provider_name="local_esmfold")
    expected = build_replay_contract(
        baseline,
        app_version="1.2.3",
        git_commit="abc123",
        tool_versions={"heuristic_proxy": "0.1"},
    )
    current = build_replay_contract(
        changed,
        app_version="1.2.4",
        git_commit="def456",
        tool_versions={"local_esmfold": "2.0"},
    )

    decision = evaluate_replay_eligibility(expected, current)

    assert decision.eligible is False
    assert set(decision.invalidation_reasons) == {
        "parameters_changed",
        "tools_changed",
        "code_expectations_changed",
    }


def test_runtime_local_run_bundle_persists_context_replay_and_ledger(
    tmp_path: Path,
) -> None:
    context, _ = create_run_context(tmp_path, run_id="replay-run-3")
    run_context = build_run_context_contract(
        run_id=context.run_id,
        started_at=context.start_time.isoformat(),
        base_dir=tmp_path,
        config=context.config,
        provider_name="heuristic_proxy",
        artifact_policy=context.artifact_policy,
        sequence="ACDEFGHIKLMNPQRSTVWY",
        command="run",
        workflow_family="structure_prediction",
        candidate_id="replay-run-3-c0",
    )
    write_json_atomic(context.workspace.run_summary_path, {"run_id": context.run_id})
    ledger = refresh_runtime_artifact_ledger(
        context.workspace,
        run_id=context.run_id,
        artifact_policy=context.artifact_policy,
        producer="test",
    )
    replay_contract = build_replay_contract(
        run_context,
        app_version="1.2.3",
        git_commit="abc123",
        tool_versions={"heuristic_proxy": "0.1"},
    )

    bundle = build_local_run_bundle(
        run_context=run_context,
        replay_contract=replay_contract,
        artifact_ledger=ledger,
        run_summary={"run_id": context.run_id},
    )
    write_local_run_bundle(context.workspace, bundle)

    reloaded = LocalRunBundle.load_json(context.workspace.local_run_bundle_path)

    assert isinstance(ledger, RuntimeArtifactLedger)
    assert reloaded.run_context.run_id == context.run_id
    assert reloaded.replay_contract.workflow_id == replay_contract.workflow_id
    assert reloaded.artifact_ledger.entries
