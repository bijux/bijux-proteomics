from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_runtime.runs import RunConfig, RunManager
from bijux_proteomics_runtime.runs.checkpoints import (
    ResumeCheckpoint,
    load_resume_checkpoint,
)
from bijux_proteomics_runtime.runs.integrity import verify_runtime_artifact_integrity
from bijux_proteomics_runtime.runs.replay import load_local_run_bundle


def test_runtime_partial_human_review_writes_resume_checkpoint(
    tmp_path: Path,
) -> None:
    manager = RunManager(
        tmp_path,
        RunConfig(require_human_decision=True),
    )
    result = manager.run("MPEPTIDE", run_id="runtime-checkpoint-1")

    from bijux_proteomics_runtime.support.workspace import RunWorkspace

    workspace = RunWorkspace.for_run(tmp_path, "runtime-checkpoint-1")
    checkpoint = load_resume_checkpoint(workspace)

    assert result["status"] == "partial"
    assert isinstance(checkpoint, ResumeCheckpoint)
    assert checkpoint.resume_command == "resume"


def test_runtime_integrity_report_detects_corrupted_local_bundle(
    tmp_path: Path,
) -> None:
    manager = RunManager(tmp_path)
    manager.run("MPEPTIDE", run_id="runtime-integrity-1")

    from bijux_proteomics_runtime.support.workspace import RunWorkspace

    workspace = RunWorkspace.for_run(tmp_path, "runtime-integrity-1")
    workspace.local_run_bundle_path.write_text('{"corrupted": true}', encoding="utf-8")

    report = verify_runtime_artifact_integrity(
        workspace,
        run_id="runtime-integrity-1",
        max_artifact_bytes=1_000_000,
    )

    assert report.verified is False
    assert any(issue.issue_code == "artifact_corrupted" for issue in report.issues)
    with pytest.raises(ValueError, match="artifact_corrupted"):
        load_local_run_bundle(workspace)


def test_runtime_import_guard_rejects_oversized_external_artifact(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "external" / "huge-import.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("x" * 128, encoding="utf-8")
    manager = RunManager(
        tmp_path,
        RunConfig(max_bundle_artifact_bytes=32),
    )

    result = manager.import_result(
        sequence="MPEPTIDE",
        source_path=source_path,
        imported_payload={"payload": "x" * 16},
        engine_name="diann",
        engine_version="1.8.2",
        run_id="runtime-import-guard-1",
    )

    assert result["status"] == "failure"
    assert result["failure_type"] == "invalid_output"
