"""Compatibility CLI entrypoint for the `proteomics-runtime` distribution."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from bijux_proteomics_runtime.api.cli import cli as runtime_cli

__all__ = ["main"]


def main(argv: Sequence[str] | None = None) -> int:
    """Run the canonical runtime CLI with the alias package name."""
    return cast(
        int,
        runtime_cli.main(
            args=list(argv) if argv is not None else None,
            prog_name="proteomics-runtime",
            standalone_mode=False,
        ),
    )
