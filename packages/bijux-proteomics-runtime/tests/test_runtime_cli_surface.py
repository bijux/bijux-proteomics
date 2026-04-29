from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from bijux_proteomics_runtime.interfaces.cli import (
    _artifact_hashes,
    _artifact_paths,
    _build_run_config,
    _emit_json_payload,
    _emit_run_summary_human,
    _export_report_payload,
    _load_run_config,
    _load_run_summary,
    _read_sequence,
    _resume_candidate,
    _write_output,
    cli,
)


def test_runtime_cli_help_contract() -> None:
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "bijux-proteomics-runtime" in result.output


def test_runtime_cli_exports_input_and_config_helpers() -> None:
    assert _read_sequence is not None
    assert _build_run_config is not None
    assert _resume_candidate is not None


def test_runtime_cli_exports_artifact_and_report_helpers() -> None:
    assert _export_report_payload is not None
    assert _write_output is not None
    assert _artifact_paths is not None
    assert _emit_json_payload is not None
    assert _load_run_summary is not None
    assert _load_run_config is not None
    assert _emit_run_summary_human is not None
    assert _artifact_hashes is not None


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def test_runtime_api_status_cli_uses_canonical_envelope(
    monkeypatch, tmp_path: Path
) -> None:
    run_id = "cli-status-1"
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "artifacts" / run_id
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
            "artifacts_dir": str(run_dir),
            "warnings": [],
            "failure": None,
            "version": {"app": "0+local", "git_commit": "unknown", "tool_versions": {}},
        },
    )
    _write_json(artifacts_dir / "evidence_bundle.json", {"bundle_id": "bundle-cli"})

    runner = CliRunner()
    result = runner.invoke(cli, ["api", "status", run_id], catch_exceptions=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "ok"
    assert payload["data"]["summary"]["run_id"] == run_id
    assert payload["data"]["evidence_bundle"]["availability"] == "available"


def test_runtime_run_json_output_uses_api_envelope(monkeypatch, tmp_path: Path) -> None:
    run_id = "cli-run-1"
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "artifacts" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
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
            "artifacts_dir": str(run_dir),
            "warnings": [],
            "failure": None,
            "version": {"app": "0+local", "git_commit": "unknown", "tool_versions": {}},
        },
    )

    def _fake_run_sequence(base_dir: Path, sequence: str, config: object) -> dict[str, object]:
        return {
            "run_id": run_id,
            "candidate_id": f"{run_id}-c0",
            "lifecycle_state": "done",
            "status": "success",
            "failure_type": "none",
            "plan_fingerprint": "plan-1",
            "tool_status": "success",
            "report": {},
            "qc_status": "acceptable",
            "coordinator_decision": "TerminateRun",
            "errors": [],
            "warnings": [],
            "version_info": {"app_version": "0+local", "git_commit": "unknown", "tool_versions": {}},
        }

    runner = CliRunner()
    monkeypatch.setattr(
        "bijux_proteomics_runtime.interfaces.cli._run_sequence",
        _fake_run_sequence,
    )
    result = runner.invoke(
        cli,
        ["run", "--sequence", "MPEPTIDE", "--json"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "ok"
    assert payload["data"]["run_id"] == run_id


def test_runtime_api_health_cli_uses_component_report(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "apis" / "bijux-proteomics-runtime" / "v1").mkdir(parents=True)
    for name in ("schema.yaml", "pinned_openapi.json", "schema.hash"):
        (tmp_path / "apis" / "bijux-proteomics-runtime" / "v1" / name).write_text(
            "ok",
            encoding="utf-8",
        )

    runner = CliRunner()
    monkeypatch.setattr(
        "bijux_proteomics_runtime.api.catalog.provider_requirements",
        lambda name: {"provider": name},
    )
    result = runner.invoke(cli, ["api", "health"], catch_exceptions=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "ok"
    components = {item["component"]: item for item in payload["data"]["components"]}
    assert components["manifest"]["state"] == "healthy"


def test_runtime_api_evidence_cli_surfaces_large_document_guard(
    monkeypatch, tmp_path: Path
) -> None:
    run_id = "cli-large-1"
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "artifacts" / run_id / "artifacts"
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(tmp_path / "artifacts" / run_id / "run_summary.json", {
        "run_id": run_id,
        "candidate_id": f"{run_id}-c0",
        "command": "run",
        "execution_status": "completed",
        "workflow_state": "done",
        "outcome": "accepted",
        "provider": "heuristic_proxy",
        "tool_status": "success",
        "qc_status": "acceptable",
        "artifacts_dir": str(tmp_path / "artifacts" / run_id),
        "warnings": [],
        "failure": None,
        "version": {"app": "0+local", "git_commit": "unknown", "tool_versions": {}},
    })
    (run_dir / "evidence_bundle.json").write_text(
        json.dumps({"payload": "x" * 2048}),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "api",
            "evidence-bundle",
            run_id,
            "--include-document",
            "--max-inline-bytes",
            "128",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["data"]["evidence_bundle"]["availability"] == "too_large"
    assert payload["data"]["evidence_bundle"]["guard_limit_bytes"] == 128
