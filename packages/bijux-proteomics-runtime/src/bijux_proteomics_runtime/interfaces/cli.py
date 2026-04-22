"""CLI entrypoint for bijux-proteomics-runtime."""

from __future__ import annotations

import click

from bijux_proteomics_runtime.runtime_identity import runtime_banner


@click.group(help="Canonical CLI surface for the bijux-proteomics runtime package.")
def cli() -> None:
    """CLI command group."""


@cli.command("identity")
def identity_command() -> None:
    """Print the canonical runtime identity banner."""
    click.echo(runtime_banner())
