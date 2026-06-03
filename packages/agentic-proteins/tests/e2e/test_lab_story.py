# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from agentic_proteins.orchestration.manager import RunManager
from agentic_proteins.orchestration.run_config import RunConfig
from agentic_proteins_testsupport.paths import package_tests_root


def _read_fasta(path: Path) -> str:
    lines = path.read_text().splitlines()
    return "".join(line.strip() for line in lines if not line.startswith(">"))


def test_lab_story_end_to_end(tmp_path: Path) -> None:
    seq_path = package_tests_root() / "fixtures" / "proteins" / "small_enzyme.fasta"
    sequence = _read_fasta(seq_path)
    config = RunConfig(loop_max_iterations=2, require_human_decision=True)
    manager = RunManager(tmp_path, config)
    result = manager.run(sequence)

    run_dir = tmp_path / "artifacts" / result["run_id"]
    assert (run_dir / "candidate_selection.json").exists()
    assert (run_dir / "human_decision.json").exists()
    assert (run_dir / "report.json").exists()
