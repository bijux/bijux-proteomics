# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics_runtime.runs import (
    RuntimeArtifactRetentionClass,
    RunConfig,
    build_run_context_contract,
    create_run_context,
)
from bijux_proteomics_runtime.runs.ledger import ArtifactLedgerEntry
from bijux_proteomics_runtime.runs.ledger import RuntimeArtifactLedger
from bijux_proteomics_runtime.runs.replay import build_replay_contract
from bijux_proteomics_runtime.runtime.workspace import write_json_atomic


def build_medium_startup_config() -> RunConfig:
    return RunConfig.model_validate(
        {
            "predictors_enabled": ["local_esmfold"],
            "resource_limits": {"cpu_seconds": 240.0, "gpu_seconds": 180.0},
            "retry_policy": {"max_retries": 2},
            "logging_enabled": True,
            "strict_mode": True,
            "loop_max_iterations": 3,
            "loop_stagnation_window": 3,
            "loop_improvement_threshold": 0.2,
            "loop_max_cost": 12.0,
            "tool_versions": {
                "local_esmfold": "2.0",
                "diann": "1.9.2",
                "spectronaut": "19.0",
            },
            "execution_mode": "gpu",
            "launch_surface": "container",
            "container_image": "ghcr.io/bijux/proteomics-runtime:bench",
            "container_image_digest": "sha256:" + "1" * 64,
            "max_bundle_artifact_bytes": 2_000_000,
        }
    )


def seed_medium_artifact_runs(base_dir: Path, *, run_count: int = 18) -> None:
    for index in range(run_count):
        context, _ = create_run_context(
            base_dir,
            build_medium_startup_config(),
            run_id=f"artifact-benchmark-{index}",
        )
        write_json_atomic(
            context.workspace.run_context_path,
            {
                "run_id": context.run_id,
                "started_at": context.start_time.isoformat(),
                "provider_name": "local_esmfold",
                "config_fingerprint": f"cfg-{index}",
                "dataset": {
                    "dataset_id": f"dataset-{index}",
                    "dataset_kind": "imported_evidence",
                    "dataset_fingerprint": f"fp-{index}",
                    "source_path": f"/bench/import-{index}.json",
                },
                "workflow": {
                    "workflow_id": f"wf-{index}",
                    "command": "import",
                    "workflow_family": "external_import",
                    "import_only": True,
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
                "command": "import",
                "execution_status": "completed",
                "workflow_state": "done",
                "outcome": "accepted",
                "provider": "local_esmfold",
                "tool_status": "success",
                "qc_status": "acceptable",
                "artifacts_dir": str(context.workspace.run_dir),
                "warnings": [],
                "failure": None,
                "version": {
                    "app": "0+local",
                    "git_commit": "unknown",
                    "tool_versions": {"local_esmfold": "2.0"},
                },
            },
        )
        for artifact_index in range(12):
            payload = {
                "artifact_id": f"{context.run_id}-artifact-{artifact_index}",
                "peptides": [
                    {
                        "sequence": f"PEPTIDE{artifact_index:02d}",
                        "charge": charge,
                        "score": round(0.81 + artifact_index * 0.003 + charge * 0.01, 4),
                    }
                    for charge in range(2, 5)
                ],
                "channels": [f"TMT-{channel:02d}" for channel in range(1, 11)],
            }
            write_json_atomic(
                context.workspace.artifact_items_dir
                / f"artifact_{artifact_index:02d}.json",
                payload,
            )


def build_medium_rerun_fixture(tmp_path: Path):
    config = build_medium_startup_config()
    previous_context, _ = create_run_context(
        tmp_path,
        config,
        run_id="replay-benchmark-medium-1",
    )
    run_context = build_run_context_contract(
        run_id=previous_context.run_id,
        started_at=previous_context.start_time.isoformat(),
        base_dir=tmp_path,
        config=previous_context.config,
        provider_name="local_esmfold",
        artifact_policy=previous_context.artifact_policy,
        sequence="MPEPTIDE" * 10,
        command="run",
        workflow_family="sequence_to_digest",
        candidate_id="replay-benchmark-medium-1-c0",
    )
    expected = build_replay_contract(
        run_context,
        app_version="1.2.3",
        git_commit="abc123",
        tool_versions={"local_esmfold": "2.0", "diann": "1.9.2"},
    )
    current = build_replay_contract(
        run_context.model_copy(
            update={"provider_name": "heuristic_proxy"},
        ),
        app_version="1.2.4",
        git_commit="abc123",
        tool_versions={"heuristic_proxy": "v1", "diann": "1.9.2"},
    )
    artifact_kinds = (
        "runtime-run-context",
        "runtime-plan",
        "runtime-replay-contract",
        "runtime-status",
        "runtime-report",
        "runtime-local-run-bundle",
        "runtime-integrity-report",
        "runtime-artifact-item",
        "runtime-analysis",
        "runtime-telemetry",
        "runtime-output",
        "runtime-failure-report",
    )
    ledger = RuntimeArtifactLedger(
        run_id=run_context.run_id,
        entries=tuple(
            ArtifactLedgerEntry(
                artifact_role=f"role-{index}",
                artifact_kind=artifact_kind,
                path=f"/tmp/{artifact_kind}-{index}.json",
                producer="benchmark",
                retention_class=RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
                content_sha256=f"{index:064x}"[-64:],
                size_bytes=8_192 + index * 256,
            )
            for index, artifact_kind in enumerate(artifact_kinds * 4)
        ),
    )
    return run_context, expected, current, ledger


def medium_import_payload() -> dict[str, object]:
    return {
        "experiment": "medium-import-benchmark",
        "peptides": [
            {
                "sequence": f"PEPTIDE{index:03d}",
                "charge": (index % 3) + 2,
                "proteins": [f"P{index:05d}", f"Q{index:05d}"],
                "intensities": [round(10_000 + index * 17 + offset * 3.5, 4) for offset in range(10)],
            }
            for index in range(180)
        ],
        "metadata": {
            "engine": "spectronaut",
            "version": "19.0",
            "channels": [f"TMT-{channel:02d}" for channel in range(1, 11)],
        },
    }


def write_medium_import_source(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(medium_import_payload(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
