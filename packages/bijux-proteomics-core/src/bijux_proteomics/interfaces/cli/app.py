
# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""CLI assembler for Bijux Proteomics command modules."""

from __future__ import annotations

import click

from bijux_proteomics.interfaces.cli.commands import GROUP_COMMANDS, ROOT_COMMANDS
from bijux_proteomics.interfaces.cli.commands.groups import GROUPS
from bijux_proteomics.workflow.orchestrator import (
    run_proteomics_workflow as run_proteomics_workflow,
)


@click.group()
def cli() -> None:
    """CLI for Bijux Proteomics domain and FASTA operations."""


for command in ROOT_COMMANDS:
    cli.add_command(command)

for group in GROUPS:
    for command in GROUP_COMMANDS.get(group, ()):  # pragma: no branch
        group.add_command(command)
    cli.add_command(group)
