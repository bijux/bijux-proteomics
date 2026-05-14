from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_proteomics_runtime.providers.environment import (
    SlurmJobScriptInput,
    SlurmLifecycleState,
    export_slurm_job_script,
    run_container_smoke_execution,
    run_mocked_slurm_lifecycle,
)
from bijux_proteomics_runtime.runs.integrity import load_artifact_integrity_report
from bijux_proteomics_runtime.runs.launch_bundles import (
    load_container_run_bundle,
    load_scheduler_job_bundle,
)
from bijux_proteomics_runtime.runs.ledger import load_artifact_ledger
from bijux_proteomics_runtime.runs.manager import RunManager
from bijux_proteomics_runtime.runs.run_config import RunConfig
from bijux_proteomics_runtime.support.workspace import RunWorkspace

from ..support.fixture_data import load_fixture


def _fake_run_flow_from_fixture(
    fixture: dict[str, object],
) -> Callable[[Any, Any, Any], dict[str, object]]:
    result_payload = dict(cast(dict[str, object], fixture["fake_run_flow_result"]))

    def _fake_run_flow(candidate, context, tool):  # type: ignore[no-untyped-def]
        result = dict(result_payload)
        result["candidate_id"] = candidate.candidate_id
        result["candidate"] = candidate.model_dump()
        return result

    return _fake_run_flow


def test_runtime_container_path_publishes_launch_bundle_and_smoke_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = load_fixture("execution", "container_review_path.json")
    monkeypatch.setattr(
        "bijux_proteomics_runtime.runs.manager.run_flow",
        _fake_run_flow_from_fixture(fixture),
    )

    manager = RunManager(tmp_path, RunConfig.model_validate(fixture["config"]))
    result = manager.run(str(fixture["sequence"]), run_id=str(fixture["run_id"]))
    workspace = RunWorkspace.for_run(tmp_path, str(fixture["run_id"]))
    bundle = load_container_run_bundle(workspace)
    ledger = load_artifact_ledger(workspace, str(fixture["run_id"]))
    integrity = load_artifact_integrity_report(workspace)
    smoke = run_container_smoke_execution(
        image_tag=bundle.image_reference,
        command=tuple(str(token) for token in fixture["smoke_command"]),
        expected_artifact_paths=tuple(
            str(path) for path in fixture["expected_smoke_artifacts"]
        ),
    )

    assert result["status"] == "success"
    assert bundle.image_digest == fixture["config"]["container_image_digest"]
    assert (
        bundle.environment_capture.execution_mode == fixture["config"]["execution_mode"]
    )
    assert bundle.environment_capture.enabled_predictors == tuple(
        fixture["expected_enabled_predictors"]
    )
    assert smoke.passed is True
    assert set(fixture["expected_artifact_kinds"]).issubset(
        {entry.artifact_kind for entry in ledger.entries}
    )
    assert integrity.verified is True


def test_runtime_scheduler_path_publishes_launch_bundle_and_lifecycle_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = load_fixture("execution", "scheduler_review_path.json")
    monkeypatch.setattr(
        "bijux_proteomics_runtime.runs.manager.run_flow",
        _fake_run_flow_from_fixture(fixture),
    )

    manager = RunManager(tmp_path, RunConfig.model_validate(fixture["config"]))
    result = manager.run(str(fixture["sequence"]), run_id=str(fixture["run_id"]))
    workspace = RunWorkspace.for_run(tmp_path, str(fixture["run_id"]))
    bundle = load_scheduler_job_bundle(workspace)
    ledger = load_artifact_ledger(workspace, str(fixture["run_id"]))
    integrity = load_artifact_integrity_report(workspace)
    script = export_slurm_job_script(
        SlurmJobScriptInput.model_validate(fixture["slurm_script"])
    )
    lifecycle = run_mocked_slurm_lifecycle(
        job_id=bundle.launch_metadata.submission_id,
        outcome=SlurmLifecycleState.SUCCEEDED,
        collected_logs=tuple(str(path) for path in fixture["collected_logs"]),
    )

    assert result["status"] == "success"
    assert (
        bundle.launch_metadata.scheduler_system == fixture["config"]["scheduler_system"]
    )
    assert bundle.launch_metadata.queue_name == fixture["config"]["scheduler_queue"]
    assert bundle.replay_boundary.requires_human_resume is True
    assert "#SBATCH --job-name=bijux-runtime-review" in script.script_text
    assert "artifacts/runtime-scheduler-review-1" in script.script_text
    assert lifecycle.final_state is SlurmLifecycleState.SUCCEEDED
    assert lifecycle.collected_logs == tuple(sorted(fixture["collected_logs"]))
    assert set(fixture["expected_artifact_kinds"]).issubset(
        {entry.artifact_kind for entry in ledger.entries}
    )
    assert integrity.verified is True
