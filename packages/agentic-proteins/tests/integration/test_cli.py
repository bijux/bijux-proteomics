# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from agentic_proteins.interfaces.cli import cli


def test_cli_run_requires_sequence_or_fasta() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--json"])
    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    assert payload["command"] == "run"
    assert "Provide --sequence or --fasta" in payload["error"]


def test_cli_run_rejects_sequence_and_fasta() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fasta = Path("input.fasta")
        fasta.write_text(">seq\nACDE")
        result = runner.invoke(
            cli,
            [
                "run",
                "--sequence",
                "ACDE",
                "--fasta",
                str(fasta),
                "--json",
            ],
        )
    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    assert payload["command"] == "run"
    assert "Provide either --sequence or --fasta" in payload["error"]


def test_cli_run_dry_run() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "run",
                "--sequence",
                "ACDE",
                "--dry-run",
                "--no-logs",
                "--json",
            ],
        )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["run_id"]
