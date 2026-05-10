"""Compatibility CLI entrypoint for the `proteomics` distribution."""

from __future__ import annotations

from collections.abc import Sequence

from bijux_proteomics.interfaces.cli import cli as runtime_cli

__all__ = ["main"]


def main(argv: Sequence[str] | None = None) -> int:
    """Run the canonical core CLI with the alias package name."""
    return runtime_cli.main(
        args=list(argv) if argv is not None else None,
        prog_name="proteomics",
        standalone_mode=False,
    )
