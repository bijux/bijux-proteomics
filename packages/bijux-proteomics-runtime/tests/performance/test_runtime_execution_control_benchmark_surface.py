# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.api.catalog import build_artifact_lookup_response
from bijux_proteomics_runtime.runtime.context import (
    RuntimeArtifactRetentionClass,
    build_run_context_contract,
    create_run_context,
)
from bijux_proteomics_runtime.runtime.control import (
    ArtifactLedgerEntry,
    RuntimeArtifactLedger,
    build_partial_rerun_plan,
    build_replay_contract,
    run_reviewable_sequence_path,
)
from bijux_proteomics_runtime.runtime.workspace import write_json_atomic


def _fake_success(candidate, context, tool):  # type: ignore[no-untyped-def]
    return {
        "candidate_id": candidate.candidate_id,
        "candidate": candidate.model_dump(),
        "plan_fingerprint": "plan-benchmark",
        "tool_status": "success",
        "report": {
            "status": "ok",
            "observations": [
                {"step": index, "score": round(0.8 + (index % 7) * 0.01, 4)}
                for index in range(96)
            ],
        },
        "qc_status": "acceptable",
        "coordinator_decision": "TerminateRun",
        "failure_type": "none",
        "lifecycle_state": "done",
    }


def _seed_artifact_runs(base_dir: Path, *, run_count: int = 8) -> None:
    for index in range(run_count):
        context, _ = create_run_context(base_dir, run_id=f"artifact-benchmark-{index}")
        write_json_atomic(
            context.workspace.run_context_path,
            {
                "run_id": context.run_id,
                "started_at": context.start_time.isoformat(),
                "provider_name": "heuristic_proxy",
                "config_fingerprint": f"cfg-{index}",
                "dataset": {
                    "dataset_id": f"dataset-{index}",
                    "dataset_kind": "inline_sequence",
                    "dataset_fingerprint": f"fp-{index}",
                    "source_path": None,
                },
                "workflow": {
                    "workflow_id": f"wf-{index}",
                    "command": "run",
                    "workflow_family": "sequence_to_digest",
                    "import_only": False,
                },
                "environment": {
                    "environment_id": f"env-{index}",
                    "host_name": "benchmark-host",
                    "platform": "darwin",
                    "python_version": "3.11.9",
                    "working_directory": str(base_dir),
                },
                "artifact_policy": {
                    "artifacts_root": str(base_dir / "artifacts"),
                    "hash_policy_id": "bijux-stable-sha256-v1",
                    "inline_limit_bytes": 256000,
                    "retention_by_role": {},
                },
                "lineage": {"parent_run_id": None, "resume_depth": 0},
            },
        )
        write_json_atomic(
            context.workspace.run_summary_path,
            {
                "run_id": context.run_id,
                "candidate_id": f"{context.run_id}-c0",
                "command": "run",
                "execution_status": "completed",
                "workflow_state": "done",
                "outcome": "accepted",
                "provider": "heuristic_proxy",
                "tool_status": "success",
                "qc_status": "acceptable",
                "artifacts_dir": str(context.workspace.run_dir),
                "warnings": [],
                "failure": None,
                "version": {
                    "app": "0+local",
                    "git_commit": "unknown",
                    "tool_versions": {"heuristic_proxy": "0.1"},
                },
            },
        )


def _rerun_plan_fixture(tmp_path: Path):
    previous_context, _ = create_run_context(tmp_path, run_id="replay-benchmark-1")
    run_context = build_run_context_contract(
        run_id=previous_context.run_id,
        started_at=previous_context.start_time.isoformat(),
        base_dir=tmp_path,
        config=previous_context.config,
        provider_name="heuristic_proxy",
        artifact_policy=previous_context.artifact_policy,
        sequence="MPEPTIDE",
        command="run",
        workflow_family="sequence_to_digest",
        candidate_id="replay-benchmark-1-c0",
    )
    expected = build_replay_contract(
        run_context,
        app_version="1.2.3",
        git_commit="abc123",
        tool_versions={"heuristic_proxy": "0.1"},
    )
    current = build_replay_contract(
        run_context,
        app_version="1.2.4",
        git_commit="abc123",
        tool_versions={"heuristic_proxy": "0.2"},
    )
    ledger = RuntimeArtifactLedger(
        run_id=run_context.run_id,
        entries=tuple(
            ArtifactLedgerEntry(
                artifact_role=f"role-{index}",
                artifact_kind=artifact_kind,
                path=f"/tmp/{artifact_kind}.json",
                producer="benchmark",
                retention_class=RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
                content_sha256="0" * 64,
                size_bytes=16,
            )
            for index, artifact_kind in enumerate(
                (
                    "runtime-run-context",
                    "runtime-plan",
                    "runtime-replay-contract",
                    "runtime-status",
                    "runtime-report",
                    "runtime-local-run-bundle",
                    "runtime-integrity-report",
                    "runtime-artifact-item",
                )
            )
        ),
    )
    return run_context, expected, current, ledger


def test_runtime_startup_benchmark_creates_context_layout(
    benchmark, tmp_path: Path
) -> None:
    startup_root = tmp_path / "startup"
    startup_root.mkdir(parents=True, exist_ok=True)

    context, warnings = benchmark(lambda: create_run_context(startup_root))

    assert context.workspace.run_dir.exists()
    assert isinstance(warnings, list)


def test_runtime_artifact_listing_benchmark_scales_across_seeded_runs(
    benchmark,
    tmp_path: Path,
) -> None:
    _seed_artifact_runs(tmp_path)

    response = benchmark(
        lambda: build_artifact_lookup_response(
            tmp_path,
            page_size=50,
            max_query_cost=500,
        )
    )

    assert response.page.returned_count >= 8


def test_runtime_replay_planning_benchmark_measures_invalidation_cost(
    benchmark,
    tmp_path: Path,
) -> None:
    run_context, expected, current, ledger = _rerun_plan_fixture(tmp_path)

    plan = benchmark(
        lambda: build_partial_rerun_plan(
            previous_run_context=run_context,
            previous_replay_contract=expected,
            current_replay_contract=current,
            artifact_ledger=ledger,
        )
    )

    assert plan.replay_eligibility.eligible is False


def test_runtime_medium_execution_benchmark_publishes_reviewable_path(
    benchmark,
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_runtime.runtime.control.execution.run_flow",
        _fake_success,
    )

    manifest = benchmark.pedantic(
        lambda: run_reviewable_sequence_path(tmp_path, sequence="MPEPTIDE"),
        rounds=3,
        iterations=1,
    )

    assert Path(manifest.summary_path).exists()
    assert manifest.command == "run"
