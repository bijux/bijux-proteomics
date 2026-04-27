from __future__ import annotations

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
