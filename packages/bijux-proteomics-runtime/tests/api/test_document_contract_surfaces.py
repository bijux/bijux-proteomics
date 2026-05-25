from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path

from pytest import MonkeyPatch

from bijux_proteomics_foundation.testing.skip_policy import (
    SkipCategory,
    import_or_skip,
)
from bijux_proteomics_runtime.api import AppConfig, create_app

fastapi_testclient = import_or_skip(
    "fastapi.testclient",
    category=SkipCategory.OPTIONAL_DEPENDENCY,
    reason="httpx is required for the runtime api document-contract surface",
)
TestClient = fastapi_testclient.TestClient


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _seed_run(
    base_dir: Path,
    run_id: str,
    *,
    workflow_state: str = "done",
    outcome: str = "accepted",
    started_at: str = "2026-05-05T10:00:00+00:00",
) -> Path:
    run_dir = base_dir / "artifacts" / run_id
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, object] = {
        "run_id": run_id,
        "candidate_id": f"{run_id}-c0",
        "command": "run",
        "execution_status": "completed",
        "workflow_state": workflow_state,
        "outcome": outcome,
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
    _write_json(
        run_dir / "run_context.json",
        {
            "run_id": run_id,
            "started_at": started_at,
        },
    )
    _write_json(artifacts_dir / "evidence_bundle.json", {"bundle_id": "bundle-1"})
    _write_json(artifacts_dir / "review_packet.json", {"packet_id": "review-1"})
    return run_dir


def test_runtime_status_contract_reports_evidence_and_review_documents(
    tmp_path: Path,
) -> None:
    run_id = "run-status-1"
    _seed_run(tmp_path, run_id)
    client = TestClient(create_app(AppConfig(base_dir=tmp_path, docs_enabled=False)))

    response = client.get(
        f"/api/v1/runs/{run_id}/status", params={"include_documents": "true"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["request_id"]
    assert payload["meta"]["trace_id"]
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


def test_runtime_document_contracts_report_missing_files_honestly(
    tmp_path: Path,
) -> None:
    run_id = "run-missing-1"
    run_dir = _seed_run(tmp_path, run_id)
    (run_dir / "artifacts" / "review_packet.json").unlink()
    client = TestClient(create_app(AppConfig(base_dir=tmp_path, docs_enabled=False)))

    response = client.get(f"/api/v1/runs/{run_id}/review-packet")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["review_packet"]["availability"] == "missing"


def test_runtime_health_contract_distinguishes_component_failures(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "apis" / "bijux-proteomics-runtime" / "v1").mkdir(parents=True)
    for name in ("schema.yaml", "pinned_openapi.json", "schema.hash"):
        (tmp_path / "apis" / "bijux-proteomics-runtime" / "v1" / name).write_text(
            "ok",
            encoding="utf-8",
        )
    client = TestClient(create_app(AppConfig(base_dir=tmp_path, docs_enabled=False)))
    monkeypatch.setattr(
        "bijux_proteomics_runtime.api.catalog.provider_requirements",
        lambda name: {"provider": name},
    )

    response = client.get("/api/v1/runtime-health")

    assert response.status_code == 200
    payload = response.json()
    components = {item["component"]: item for item in payload["data"]["components"]}
    assert components["storage"]["state"] == "healthy"
    assert components["cache"]["state"] == "degraded"
    assert components["tooling"]["state"] == "healthy"
    assert components["manifest"]["state"] == "healthy"


def test_runtime_document_contract_applies_inline_ingestion_guard(
    tmp_path: Path,
) -> None:
    run_id = "run-large-1"
    run_dir = _seed_run(tmp_path, run_id)
    (run_dir / "artifacts" / "evidence_bundle.json").write_text(
        json.dumps({"payload": "x" * 2048}),
        encoding="utf-8",
    )
    client = TestClient(create_app(AppConfig(base_dir=tmp_path, docs_enabled=False)))

    response = client.get(
        f"/api/v1/runs/{run_id}/evidence-bundle",
        params={"include_document": "true", "max_inline_bytes": "128"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["evidence_bundle"]["availability"] == "too_large"
    assert payload["data"]["evidence_bundle"]["guard_limit_bytes"] == 128


def test_runtime_lookup_contracts_filter_runs_artifacts_and_documents(
    tmp_path: Path,
) -> None:
    first_run = _seed_run(tmp_path, "history-a")
    _seed_run(tmp_path, "history-b")
    (first_run / "artifacts" / "review_packet.json").unlink()
    client = TestClient(create_app(AppConfig(base_dir=tmp_path, docs_enabled=False)))

    history_response = client.get(
        "/api/v1/runs/history",
        params={"candidate_id": "history-a-c0"},
    )
    artifact_response = client.get(
        "/api/v1/artifacts",
        params={"artifact_kind": "runtime-status"},
    )
    evidence_response = client.get(
        "/api/v1/evidence",
        params={"document_kind": "review_packet", "availability": "missing"},
    )

    assert history_response.status_code == 200
    assert artifact_response.status_code == 200
    assert evidence_response.status_code == 200
    assert len(history_response.json()["data"]["runs"]) == 1
    assert len(artifact_response.json()["data"]["artifacts"]) == 2
    documents = evidence_response.json()["data"]["documents"]
    assert len(documents) == 1
    assert documents[0]["run_id"] == "history-a"


def test_runtime_lookup_contracts_apply_pagination_and_query_cost(
    tmp_path: Path,
) -> None:
    for run_id in ("page-a", "page-b", "page-c"):
        _seed_run(tmp_path, run_id)
    client = TestClient(create_app(AppConfig(base_dir=tmp_path, docs_enabled=False)))

    paged_response = client.get(
        "/api/v1/runs/history",
        params={"page_size": "2", "cursor": "1", "max_query_cost": "10"},
    )
    rejected_response = client.get(
        "/api/v1/runs/history",
        params={"page_size": "2", "max_query_cost": "4"},
    )

    assert paged_response.status_code == 200
    paged_payload = paged_response.json()
    assert len(paged_payload["data"]["runs"]) == 2
    assert paged_payload["data"]["page"]["next_cursor"] is None
    assert rejected_response.status_code == 422
    error_payload = rejected_response.json()["error"]
    assert error_payload["failure_class"] == "input"
    assert error_payload["remediation_hint"]
    assert error_payload["evidence_pointer"] is None


def test_runtime_history_contract_orders_resumed_and_partial_runs_stably(
    tmp_path: Path,
) -> None:
    _seed_run(
        tmp_path,
        "history-complete",
        workflow_state="done",
        outcome="accepted",
        started_at="2026-05-05T10:00:00+00:00",
    )
    _seed_run(
        tmp_path,
        "history-paused",
        workflow_state="paused",
        outcome="inconclusive",
        started_at="2026-05-05T11:00:00+00:00",
    )
    _seed_run(
        tmp_path,
        "history-review",
        workflow_state="awaiting_human_review",
        outcome="needs_review",
        started_at="2026-05-05T12:00:00+00:00",
    )
    client = TestClient(create_app(AppConfig(base_dir=tmp_path, docs_enabled=False)))

    history_response = client.get("/api/v1/runs/history")
    review_response = client.get(
        "/api/v1/runs/history",
        params={"workflow_state": "awaiting_human_review"},
    )

    assert history_response.status_code == 200
    run_ids = [item["run_id"] for item in history_response.json()["data"]["runs"]]
    assert run_ids[:3] == ["history-review", "history-paused", "history-complete"]
    assert review_response.status_code == 200
    assert [item["run_id"] for item in review_response.json()["data"]["runs"]] == [
        "history-review"
    ]


def test_runtime_import_endpoint_uses_runtime_owned_import_surface(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "external" / "import-result.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(json.dumps({"proteins": ["P12345"]}), encoding="utf-8")
    client = TestClient(create_app(AppConfig(base_dir=tmp_path, docs_enabled=False)))

    response = client.post(
        "/api/v1/import",
        json={
            "sequence": "MPEPTIDE",
            "source_path": str(source_path),
            "engine_name": "maxquant",
            "engine_version": "2.1.0",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"]["command"] == "import"
    assert payload["data"]["provider"] == "maxquant"
