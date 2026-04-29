from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from bijux_proteomics_runtime.api import AppConfig, create_app


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _seed_run(base_dir: Path, run_id: str) -> Path:
    run_dir = base_dir / "artifacts" / run_id
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "run_id": run_id,
        "candidate_id": f"{run_id}-c0",
        "command": "run",
        "execution_status": "completed",
        "workflow_state": "done",
        "outcome": "accepted",
        "provider": "heuristic_proxy",
        "tool_status": "success",
        "qc_status": "acceptable",
        "artifacts_dir": str(run_dir),
        "warnings": [],
        "failure": None,
        "version": {
            "app": "0+local",
            "git_commit": "unknown",
            "tool_versions": {},
        },
    }
    _write_json(run_dir / "run_summary.json", summary)
    _write_json(run_dir / "config.json", {"provider": "heuristic_proxy"})
    _write_json(run_dir / "plan.json", {"steps": ["plan"]})
    _write_json(run_dir / "state.json", {"status": "ready"})
    _write_json(run_dir / "report.json", {"report": "ok"})
    _write_json(run_dir / "telemetry.json", {"events": []})
    _write_json(artifacts_dir / "evidence_bundle.json", {"bundle_id": "bundle-1"})
    _write_json(artifacts_dir / "review_packet.json", {"packet_id": "review-1"})
    return run_dir


def test_runtime_status_contract_reports_evidence_and_review_documents(
    tmp_path: Path,
) -> None:
    run_id = "run-status-1"
    _seed_run(tmp_path, run_id)
    client = TestClient(create_app(AppConfig(base_dir=tmp_path, docs_enabled=False)))

    response = client.get(f"/api/v1/runs/{run_id}/status", params={"include_documents": "true"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["summary"]["run_id"] == run_id
    assert payload["data"]["evidence_bundle"]["availability"] == "available"
    assert payload["data"]["evidence_bundle"]["content"]["bundle_id"] == "bundle-1"
    assert payload["data"]["review_packet"]["availability"] == "available"


def test_runtime_artifact_contract_lists_top_level_and_document_artifacts(
    tmp_path: Path,
) -> None:
    run_id = "run-artifacts-1"
    _seed_run(tmp_path, run_id)
    client = TestClient(create_app(AppConfig(base_dir=tmp_path, docs_enabled=False)))

    response = client.get(f"/api/v1/runs/{run_id}/artifacts")

    assert response.status_code == 200
    payload = response.json()
    artifact_kinds = {item["artifact_kind"] for item in payload["data"]["artifacts"]}
    assert "runtime-status" in artifact_kinds
    assert "runtime-artifact-item" in artifact_kinds


def test_runtime_document_contracts_report_missing_files_honestly(tmp_path: Path) -> None:
    run_id = "run-missing-1"
    run_dir = _seed_run(tmp_path, run_id)
    (run_dir / "artifacts" / "review_packet.json").unlink()
    client = TestClient(create_app(AppConfig(base_dir=tmp_path, docs_enabled=False)))

    response = client.get(f"/api/v1/runs/{run_id}/review-packet")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["review_packet"]["availability"] == "missing"
