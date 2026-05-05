from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics_runtime.runtime.control import (
    RuntimeReviewableOutputPath,
    build_runtime_smoke_workflows,
    run_reviewable_import_path,
    run_reviewable_sequence_path,
)
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace


def _fake_success(candidate, context, tool):  # type: ignore[no-untyped-def]
    return {
        "candidate_id": candidate.candidate_id,
        "candidate": candidate.model_dump(),
        "plan_fingerprint": "plan-1",
        "tool_status": "success",
        "report": {"status": "ok"},
        "qc_status": "acceptable",
        "coordinator_decision": "TerminateRun",
        "failure_type": "none",
        "lifecycle_state": "done",
    }


def test_runtime_smoke_workflows_cover_review_and_handoff_paths() -> None:
    workflows = {
        workflow.workflow_key: workflow for workflow in build_runtime_smoke_workflows()
    }

    assert tuple(workflows) == (
        "sequence_to_digest",
        "dda_import",
        "dia_import",
        "quant",
        "ptm",
        "review",
        "lab_handoff",
    )
    assert workflows["sequence_to_digest"].steps[0].operation_name == (
        "run_reviewable_sequence_path"
    )
    assert workflows["dda_import"].steps[0].import_only is True
    assert workflows["lab_handoff"].steps[0].handoff_surface == (
        "lab_operational_follow_up"
    )


def test_runtime_useful_run_path_persists_reviewable_manifest(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_runtime.runs.manager.run_flow",
        _fake_success,
    )

    manifest = run_reviewable_sequence_path(tmp_path, sequence="MPEPTIDE")
    workspace = RunWorkspace.for_run(tmp_path, manifest.run_id)
    persisted = RuntimeReviewableOutputPath.load_json(
        workspace.artifact_items_dir / "reviewable_run_path.json"
    )

    assert manifest.command == "run"
    assert manifest.import_only is False
    assert Path(manifest.summary_path).exists()
    assert Path(manifest.replay_contract_path).exists()
    assert Path(manifest.integrity_report_path).exists()
    assert persisted.downstream_surface == "intelligence_review"


def test_runtime_useful_import_path_persists_reviewable_manifest(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "external" / "dia-result.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        json.dumps({"peptides": ["PEPTIDE"], "engine_score": 0.97}),
        encoding="utf-8",
    )

    manifest = run_reviewable_import_path(
        tmp_path,
        sequence="MPEPTIDE",
        source_path=source_path,
        engine_name="spectronaut",
        engine_version="19.0",
    )
    workspace = RunWorkspace.for_run(tmp_path, manifest.run_id)
    persisted = RuntimeReviewableOutputPath.load_json(
        workspace.artifact_items_dir / "reviewable_import_path.json"
    )

    assert manifest.command == "import"
    assert manifest.import_only is True
    assert manifest.import_trace_path is not None
    assert Path(manifest.import_trace_path).exists()
    assert Path(manifest.integrity_report_path).exists()
    assert persisted.artifact_kinds[:2] == (
        "runtime-status",
        "runtime-import-trace",
    )
