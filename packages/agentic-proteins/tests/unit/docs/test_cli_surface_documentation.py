# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import re

import click

from agentic_proteins.interfaces.cli import cli


def _collect_commands() -> set[str]:
    commands = set(cli.commands.keys())
    for name, command in cli.commands.items():
        if isinstance(command, click.Group):
            for sub in command.commands:
                commands.add(f"{name} {sub}")
    return commands


def _collect_flags() -> set[str]:
    flags: set[str] = set()

    def _options(command: click.Command) -> None:
        for param in command.params:
            if isinstance(param, click.Option):
                for opt in param.opts + param.secondary_opts:
                    if opt != "--help":
                        flags.add(opt)

    for command in cli.commands.values():
        _options(command)
        if isinstance(command, click.Group):
            for sub in command.commands.values():
                _options(sub)
    return flags


def _repo_root() -> Path:
    path = Path(__file__).resolve()
    for parent in [path] + list(path.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("pyproject.toml not found for repo root")


def test_cli_surface_documented() -> None:
    doc_path = _repo_root() / "docs/interface/cli_surface.md"
    text = doc_path.read_text()
    documented_commands = set(
        re.findall(r"^- ([a-z0-9-]+(?: [a-z0-9-]+)?)\s*$", text, re.M)
    )
    documented_flags = set(re.findall(r"--[a-z0-9-]+", text))

    commands = _collect_commands()
    flags = _collect_flags()

    assert commands <= documented_commands
    assert flags <= documented_flags
