# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
import shutil

from click.testing import CliRunner

from bijux_proteomics.interfaces.cli import cli


_FIXTURE_ROOT = Path(__file__).resolve().parent.parent / "fixtures" / "quant"


def test_chunked_peptide_matrix_command_matches_precursor_output() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(_FIXTURE_ROOT / "peptide_matrix_precursors.tsv", "precursors.tsv")
        eager = runner.invoke(
            cli,
            [
                "peptide-matrix",
                "precursors.tsv",
                "--input-kind",
                "precursor",
                "--grouping-mode",
                "modified_peptide",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
            ],
        )
        chunked = runner.invoke(
            cli,
            [
                "peptide-matrix",
                "precursors.tsv",
                "--input-kind",
                "precursor",
                "--grouping-mode",
                "modified_peptide",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--chunk-size-rows",
                "2",
            ],
        )

        assert eager.exit_code == 0
        assert chunked.exit_code == 0
        assert json.loads(chunked.output) == json.loads(eager.output)


def test_chunked_peptide_matrix_command_matches_psm_output() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(_FIXTURE_ROOT / "peptide_matrix_psms.tsv", "psms.tsv")
        eager = runner.invoke(
            cli,
            [
                "peptide-matrix",
                "psms.tsv",
                "--input-kind",
                "psm",
                "--grouping-mode",
                "modified_peptide",
                "--run-column",
                "run_id",
                "--spectrum-id-column",
                "spectrum_id",
                "--modified-peptide-column",
                "modified_peptide",
                "--score-column",
                "score",
            ],
        )
        chunked = runner.invoke(
            cli,
            [
                "peptide-matrix",
                "psms.tsv",
                "--input-kind",
                "psm",
                "--grouping-mode",
                "modified_peptide",
                "--run-column",
                "run_id",
                "--spectrum-id-column",
                "spectrum_id",
                "--modified-peptide-column",
                "modified_peptide",
                "--score-column",
                "score",
                "--chunk-size-rows",
                "2",
            ],
        )

        assert eager.exit_code == 0
        assert chunked.exit_code == 0
        assert json.loads(chunked.output) == json.loads(eager.output)
