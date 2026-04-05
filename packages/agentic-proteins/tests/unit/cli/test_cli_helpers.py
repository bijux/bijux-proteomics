# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from types import SimpleNamespace
from pathlib import Path

import pytest
from click.testing import CliRunner

from agentic_proteins.interfaces import cli as cli_module
from agentic_proteins.interfaces.cli import cli
from agentic_proteins.runtime.infra import RunConfig


def test_read_sequence_from_fasta(tmp_path: Path) -> None:
    fasta = tmp_path / "input.fasta"
    fasta.write_text(">seq\nACD\nEFG\n")
    assert cli_module._read_sequence(None, fasta) == "ACDEFG"


def test_read_sequence_validation_errors(tmp_path: Path) -> None:
    fasta = tmp_path / "input.fasta"
    fasta.write_text(">seq\n")
    with pytest.raises(ValueError, match="Provide either --sequence or --fasta"):
        cli_module._read_sequence("ACD", fasta)
    with pytest.raises(ValueError, match="No sequence found in FASTA"):
        cli_module._read_sequence(None, fasta)
    with pytest.raises(ValueError, match="Empty sequence"):
        cli_module._read_sequence("   ", None)
    with pytest.raises(ValueError, match="Provide --sequence or --fasta"):
        cli_module._read_sequence(None, None)


def test_cli_result_contract() -> None:
    with pytest.raises(ValueError, match="payload required"):
        cli_module.CliResult(status="ok", command="run")
    with pytest.raises(ValueError, match="error required"):
        cli_module.CliResult(status="error", command="run", error="")


def test_build_run_config_limits() -> None:
    config = cli_module._build_run_config(
        rounds=1,
        dry_run=False,
        no_logs=False,
        provider="esmfold",
        artifacts_dir=None,
        execution_mode="auto",
    )
    assert config.predictors_enabled == ["local_esmfold"]
    assert config.resource_limits["gpu_seconds"] == 1.0
    with pytest.raises(ValueError, match="--rounds must be >= 1"):
        cli_module._build_run_config(
            rounds=0,
            dry_run=False,
            no_logs=False,
            provider=None,
            artifacts_dir=None,
            execution_mode="auto",
        )
    with pytest.raises(ValueError, match="--provider must be one of"):
        cli_module._build_run_config(
            rounds=1,
            dry_run=False,
            no_logs=False,
            provider="bad",
            artifacts_dir=None,
            execution_mode="auto",
        )


def test_artifact_hashes(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True)
    (artifacts_dir / "one.json").write_text('{"a":1}')
    hashes = cli_module._artifact_hashes(run_dir)
    assert "one.json" in hashes
    with pytest.raises(FileNotFoundError, match="Artifacts not found"):
        cli_module._artifact_hashes(tmp_path / "missing")


def test_load_run_config_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Config not found"):
        cli_module._load_run_config(tmp_path)


def test_export_report_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Report not found"):
        cli_module._export_report_payload(tmp_path, "run-1")


def test_emit_run_summary_human(capsys: pytest.CaptureFixture[str]) -> None:
    cli_module._emit_run_summary_human(
        {
            "execution_status": "completed",
            "run_id": "run-1",
            "provider": "heuristic",
            "tool_status": "degraded",
            "qc_status": "accept",
            "workflow_state": "awaiting_human_review",
            "candidate_id": "cand-1",
            "artifacts_dir": "/tmp/run-1",
        }
    )
    out = capsys.readouterr().out
    assert "Run completed" in out
    assert "agentic-proteins inspect-candidate cand-1" in out


def test_cli_run_json_success(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(cli_module, "_read_sequence", lambda *_: "ACD")
    monkeypatch.setattr(cli_module, "_validate_sequence", lambda *_: None)
    monkeypatch.setattr(
        cli_module, "_build_run_config", lambda *_, **__: RunConfig()
    )
    monkeypatch.setattr(
        cli_module,
        "_run_sequence",
        lambda *_: {"run_id": "run-1"},
    )
    monkeypatch.setattr(
        cli_module.RunOutput,
        "model_validate",
        lambda *_: SimpleNamespace(run_id="run-1"),
    )
    monkeypatch.setattr(
        cli_module,
        "_load_run_summary",
        lambda *_: {"run_id": "run-1", "artifacts_dir": "/tmp/run-1"},
    )
    result = runner.invoke(cli, ["run", "--sequence", "ACD", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["run_id"] == "run-1"


def test_cli_resume_json_success(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        cli_module,
        "_resume_candidate",
        lambda *_: {"run_id": "run-2"},
    )
    monkeypatch.setattr(
        cli_module.RunOutput,
        "model_validate",
        lambda *_: SimpleNamespace(run_id="run-2"),
    )
    monkeypatch.setattr(
        cli_module,
        "_load_run_summary",
        lambda *_: {"run_id": "run-2", "artifacts_dir": "/tmp/run-2"},
    )
    result = runner.invoke(cli, ["resume", "cand-1", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["run_id"] == "run-2"


def test_cli_compare_json_success(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        cli_module,
        "_compare_runs_payload",
        lambda *_: {"delta": 1},
    )
    result = runner.invoke(cli, ["compare", "run-a", "run-b", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["delta"] == 1


def test_cli_inspect_candidate_json_success(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    dummy = SimpleNamespace(model_dump=lambda: {"candidate_id": "cand-1"})
    monkeypatch.setattr(cli_module, "_inspect_candidate", lambda *_: dummy)
    result = runner.invoke(cli, ["inspect-candidate", "cand-1", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["candidate_id"] == "cand-1"


def test_cli_export_report_json_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = CliRunner()
    output = tmp_path / "report.json"
    monkeypatch.setattr(cli_module, "_export_report_payload", lambda *_: "report")
    result = runner.invoke(
        cli, ["export-report", "run-1", "--json", "--output", str(output)]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["output_path"] == str(output)


def test_cli_api_serve_uses_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    called: dict[str, object] = {}

    def fake_run(app: object, host: str, port: int, reload: bool) -> None:
        called.update({"app": app, "host": host, "port": port, "reload": reload})

    def fake_create_app(config: object) -> str:
        return "app"

    monkeypatch.setattr(cli_module.uvicorn, "run", fake_run)
    monkeypatch.setattr("agentic_proteins.api.create_app", fake_create_app)
    result = runner.invoke(cli, ["api", "serve", "--port", "9000"])
    assert result.exit_code == 0
    assert called["host"] == "127.0.0.1"
    assert called["port"] == 9000


def test_cli_reproduce_missing_run_returns_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["reproduce", "missing-run", "--json"])
    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    assert payload["command"] == "reproduce"


def test_cli_run_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(cli_module, "_read_sequence", lambda *_: (_ for _ in ()).throw(ValueError("boom")))
    result = runner.invoke(cli, ["run", "--sequence", "ACD", "--json"])
    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    result = runner.invoke(cli, ["run", "--sequence", "ACD"])
    assert result.exit_code != 0
    assert "Error: boom" in result.output


def test_cli_compare_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        cli_module,
        "_compare_runs_payload",
        lambda *_: (_ for _ in ()).throw(RuntimeError("compare-fail")),
    )
    result = runner.invoke(cli, ["compare", "a", "b", "--json"])
    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    result = runner.invoke(cli, ["compare", "a", "b"])
    assert result.exit_code != 0
    assert "Error: compare-fail" in result.output


def test_cli_inspect_candidate_error(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        cli_module,
        "_inspect_candidate",
        lambda *_: (_ for _ in ()).throw(RuntimeError("inspect-fail")),
    )
    result = runner.invoke(cli, ["inspect-candidate", "cand-1", "--json"])
    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload["status"] == "error"


def test_cli_export_report_error(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        cli_module,
        "_export_report_payload",
        lambda *_: (_ for _ in ()).throw(FileNotFoundError("missing")),
    )
    result = runner.invoke(cli, ["export-report", "run-1", "--json"])
    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload["status"] == "error"


def test_cli_reproduce_success_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = CliRunner()

    class _Store:
        def get_candidate(self, candidate_id: str) -> str:
            return candidate_id

    class _Manager:
        def __init__(self, *_args, **_kwargs) -> None:
            return None

        def run_candidate(self, *_args, **_kwargs) -> None:
            return None

    monkeypatch.setattr(cli_module, "CandidateStore", lambda *_: _Store())
    monkeypatch.setattr(cli_module, "RunManager", _Manager)
    monkeypatch.setattr(cli_module, "_artifact_hashes", lambda *_: {"a": "1"})

    with runner.isolated_filesystem():
        run_dir = Path("artifacts") / "run-1"
        run_dir.mkdir(parents=True)
        (run_dir / "run_summary.json").write_text(json.dumps({"candidate_id": "cand-1"}))
        (run_dir / "config.json").write_text(json.dumps(RunConfig().model_dump()))
        result = runner.invoke(cli, ["reproduce", "run-1", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["artifact_hashes_match"] is True


def test_resume_candidate_validation_and_flow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValueError, match="--rounds must be >= 1"):
        cli_module._resume_candidate(
            tmp_path,
            "cand-1",
            rounds=0,
            provider=None,
            artifacts_dir=None,
            execution_mode="auto",
        )

    class _Store:
        def get_candidate(self, candidate_id: str) -> str:
            return candidate_id

    class _Manager:
        def __init__(self, *_args, **_kwargs) -> None:
            return None

        def run_candidate(self, candidate: str) -> dict:
            return {"run_id": f"run-{candidate}"}

    monkeypatch.setattr(cli_module, "CandidateStore", lambda *_: _Store())
    monkeypatch.setattr(cli_module, "RunManager", _Manager)
    monkeypatch.setattr(
        cli_module, "_build_run_config", lambda *_, **__: RunConfig()
    )

    result = cli_module._resume_candidate(
        tmp_path,
        "cand-1",
        rounds=1,
        provider=None,
        artifacts_dir=None,
        execution_mode="auto",
    )
    assert result["run_id"] == "run-cand-1"


def test_cli_helpers_emit_and_paths(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cli_module._emit_json_payload({"ok": True}, pretty=True)
    assert "\"ok\": true" in capsys.readouterr().out
    cli_module._emit_json_payload({"ok": True}, pretty=False)
    assert "\"ok\": true" in capsys.readouterr().out

    output_path = tmp_path / "out.txt"
    cli_module._write_output(output_path, "payload")
    assert output_path.read_text() == "payload"

    paths = cli_module._artifact_paths(tmp_path, "run-1", None)
    assert paths["run_dir"].endswith("run-1")


def test_cli_helpers_load_and_inspect(tmp_path: Path) -> None:
    run_dir = tmp_path / "artifacts" / "run-1"
    run_dir.mkdir(parents=True)
    summary = {"run_id": "run-1"}
    (run_dir / "run_summary.json").write_text(json.dumps(summary))
    loaded = cli_module._load_run_summary(tmp_path, "run-1", None)
    assert loaded["run_id"] == "run-1"
