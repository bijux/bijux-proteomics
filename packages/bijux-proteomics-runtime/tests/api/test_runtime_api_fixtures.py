from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from pytest import MonkeyPatch

from bijux_proteomics_runtime.api.catalog import (
    build_artifact_lookup_response,
    build_evidence_lookup_response,
    build_run_history_response,
    build_runtime_health_response,
    build_runtime_status_response,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _seed_run(base_dir: Path, run_id: str) -> None:
    run_dir = base_dir / "artifacts" / run_id
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        run_dir / "run_summary.json",
        {
            "run_id": run_id,
            "candidate_id": f"{run_id}-c0",
            "command": "run",
            "execution_status": "completed",
            "workflow_state": "done",
            "outcome": "accepted",
            "provider": "heuristic_proxy",
            "tool_status": "success",
            "qc_status": "acceptable",
            "artifacts_dir": f"<workspace>/artifacts/{run_id}",
            "warnings": [],
            "failure": None,
            "version": {"app": "0+local", "git_commit": "unknown", "tool_versions": {}},
        },
    )
    _write_json(run_dir / "config.json", {"provider": "heuristic_proxy"})
    _write_json(run_dir / "plan.json", {"steps": ["plan"]})
    _write_json(run_dir / "state.json", {"status": "ready"})
    _write_json(run_dir / "report.json", {"report": "ok"})
    _write_json(run_dir / "telemetry.json", {"events": []})
    _write_json(
        artifacts_dir / "evidence_bundle.json", {"bundle_id": f"bundle-{run_id}"}
    )
    _write_json(artifacts_dir / "review_packet.json", {"packet_id": f"review-{run_id}"})


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "api" / name


def _normalize_paths(value: object, base_dir: Path) -> object:
    base_text = str(base_dir)
    if isinstance(value, dict):
        return {key: _normalize_paths(item, base_dir) for key, item in value.items()}
    if isinstance(value, list):
        normalized = [_normalize_paths(item, base_dir) for item in value]
        if normalized and all(isinstance(item, dict) for item in normalized):
            normalized_dicts = cast(list[dict[str, object]], normalized)
            return sorted(
                normalized_dicts,
                key=lambda item: (
                    str(item.get("run_id", "")),
                    str(item.get("artifact_key", "")),
                    str(item.get("path", "")),
                ),
            )
        return normalized
    if isinstance(value, str):
        return value.replace(base_text, "<workspace>")
    return value


def test_runtime_api_reference_fixtures_remain_deterministic(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    for run_id in ("fixture-a", "fixture-b"):
        _seed_run(tmp_path, run_id)
    (tmp_path / "apis" / "bijux-proteomics-runtime" / "v1").mkdir(parents=True)
    for name in ("schema.yaml", "pinned_openapi.json", "schema.hash"):
        (tmp_path / "apis" / "bijux-proteomics-runtime" / "v1" / name).write_text(
            "ok",
            encoding="utf-8",
        )
    monkeypatch.setattr(
        "bijux_proteomics_runtime.api.catalog.provider_requirements",
        lambda name: {"provider": name},
    )

    payloads = {
        "runtime_status_response.json": build_runtime_status_response(
            tmp_path,
            "fixture-a",
        ).model_dump(mode="json"),
        "artifact_lookup_response.json": build_artifact_lookup_response(
            tmp_path,
            artifact_kind="runtime-status",
        ).model_dump(mode="json"),
        "evidence_lookup_response.json": build_evidence_lookup_response(
            tmp_path,
            document_kind="evidence_bundle",
        ).model_dump(mode="json"),
        "run_history_response.json": build_run_history_response(tmp_path).model_dump(
            mode="json"
        ),
        "runtime_health_response.json": build_runtime_health_response(
            tmp_path
        ).model_dump(mode="json"),
    }

    for filename, payload in payloads.items():
        expected = json.loads(_fixture_path(filename).read_text(encoding="utf-8"))
        assert _normalize_paths(payload, tmp_path) == expected
