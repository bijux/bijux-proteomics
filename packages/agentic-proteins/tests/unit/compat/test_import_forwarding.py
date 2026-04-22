from __future__ import annotations

from agentic_proteins.interfaces.cli import cli as compat_cli
from bijux_proteomics_runtime.interfaces.cli import cli as runtime_cli


def test_compat_cli_import_forwards_to_runtime_symbol() -> None:
    assert compat_cli is runtime_cli
