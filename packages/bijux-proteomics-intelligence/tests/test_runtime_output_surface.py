from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.runs import (
    build_run_context_contract,
    create_run_context,
)
from bijux_proteomics_runtime.runs.replay import (
    build_local_run_bundle,
    build_replay_contract,
)
from bijux_proteomics_runtime.runs.replay import load_local_run_bundle
from bijux_proteomics_runtime.runs.ledger import (
    refresh_runtime_artifact_ledger,
)
from bijux_proteomics_runtime.runs.replay import write_local_run_bundle
from bijux_proteomics_runtime.runs.replay import write_replay_contract
from bijux_proteomics_runtime.runtime.workspace import write_json_atomic


def test_intelligence_can_read_runtime_local_run_bundle_via_public_runtime_surface(
    tmp_path: Path,
) -> None:
    context, _ = create_run_context(tmp_path, run_id="intelligence-runtime-1")
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
        candidate_id="intelligence-runtime-1-c0",
    )
    write_json_atomic(
        context.workspace.run_summary_path,
        {"run_id": context.run_id, "outcome": "accepted"},
    )
    replay_contract = build_replay_contract(
        run_context,
        app_version="1.2.3",
        git_commit="abc123",
        tool_versions={"heuristic_proxy": "0.1"},
    )
    write_replay_contract(context.workspace, replay_contract)
    ledger = refresh_runtime_artifact_ledger(
        context.workspace,
        run_id=context.run_id,
        artifact_policy=context.artifact_policy,
        producer="test",
    )
    write_local_run_bundle(
        context.workspace,
        build_local_run_bundle(
            run_context=run_context,
            replay_contract=replay_contract,
            artifact_ledger=ledger,
            run_summary={"run_id": context.run_id, "outcome": "accepted"},
        ),
    )
    ledger = refresh_runtime_artifact_ledger(
        context.workspace,
        run_id=context.run_id,
        artifact_policy=context.artifact_policy,
        producer="test",
    )

    bundle = load_local_run_bundle(context.workspace)

    assert bundle.run_context.workflow.workflow_family == "structure_prediction"
    assert bundle.run_summary["outcome"] == "accepted"
