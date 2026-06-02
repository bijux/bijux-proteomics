"""Compatibility CLI entrypoint for the `proteomics-core` distribution."""

from __future__ import annotations

from collections.abc import Sequence

from bijux_proteomics_foundation._package_aliases import dispatch_alias_entrypoint

__all__ = ["main"]


def main(argv: Sequence[str] | None = None) -> int:
    """Run the canonical core CLI with the alias package name."""
    return dispatch_alias_entrypoint(
        canonical_module="bijux_proteomics.interfaces.cli",
        attribute_name="cli",
        prog_name="proteomics-core",
        argv=argv,
    )
