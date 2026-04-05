# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""CLI for Bijux Proteomics program manifests."""

from __future__ import annotations

import json
from pathlib import Path

import click

from bijux_proteomics.programs import ProgramSpec, create_program_spec, program_summary


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")


@click.group()
def cli() -> None:
    """Manage program manifests for Bijux Proteomics."""


@cli.command("program-template")
@click.option("--program-id", required=True, help="Stable program identifier.")
@click.option("--name", required=True, help="Program name.")
@click.option("--objective", required=True, help="Scientific objective.")
@click.option("--target-id", required=True, help="Stable target identifier.")
@click.option("--target-name", required=True, help="Target name.")
@click.option("--sequence", required=True, help="Reference amino-acid sequence.")
@click.option("--organism", required=True, help="Source organism.")
@click.option("--mechanism", required=True, help="Working target hypothesis.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the JSON document.",
)
def program_template(
    program_id: str,
    name: str,
    objective: str,
    target_id: str,
    target_name: str,
    sequence: str,
    organism: str,
    mechanism: str,
    out_path: Path,
) -> None:
    """Write a starter program manifest."""
    program = create_program_spec(
        program_id=program_id,
        name=name,
        objective=objective,
        target_id=target_id,
        target_name=target_name,
        sequence=sequence,
        organism=organism,
        mechanism=mechanism,
    )
    _write_json(out_path, program.model_dump(mode="json"))
    click.echo(json.dumps(program_summary(program), sort_keys=True))


@cli.command("summarize-program")
@click.argument("program_file", type=click.Path(exists=True, path_type=Path))
def summarize_program(program_file: Path) -> None:
    """Print a compact summary for a program document."""
    program = ProgramSpec.model_validate_json(program_file.read_text())
    click.echo(json.dumps(program_summary(program), sort_keys=True))


if __name__ == "__main__":
    cli()
