from __future__ import annotations

from click.testing import CliRunner

from agentic_proteins.interfaces.cli import cli as compat_cli
from bijux_proteomics_runtime.interfaces.cli import cli as runtime_cli


def test_compat_cli_import_forwards_to_runtime_symbol() -> None:
    assert compat_cli is runtime_cli


def test_compat_and_runtime_cli_help_are_equivalent() -> None:
    compat_result = CliRunner().invoke(compat_cli, ["--help"])
    runtime_result = CliRunner().invoke(runtime_cli, ["--help"])
    assert compat_result.exit_code == 0
    assert runtime_result.exit_code == 0
    assert compat_result.output == runtime_result.output
