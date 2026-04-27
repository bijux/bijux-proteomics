from __future__ import annotations

from click.testing import CliRunner

from bijux_proteomics_runtime.interfaces.cli import (
    _build_run_config,
    _read_sequence,
    _resume_candidate,
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
