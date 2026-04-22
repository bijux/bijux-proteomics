from __future__ import annotations

from click.testing import CliRunner

from bijux_proteomics_runtime.interfaces.cli import cli


def test_runtime_cli_help_contract() -> None:
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "bijux-proteomics-runtime" in result.output
