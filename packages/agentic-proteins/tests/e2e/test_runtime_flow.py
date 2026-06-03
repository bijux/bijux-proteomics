# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from agentic_proteins.orchestration.manager import RunManager
from agentic_proteins_testsupport.paths import package_tests_root


def _read_fasta(path: Path) -> str:
    lines = path.read_text().splitlines()
    return "".join(line.strip() for line in lines if not line.startswith(">"))


def test_runtime_flow_e2e(tmp_path: Path) -> None:
    seq_path = package_tests_root() / "fixtures" / "proteins" / "small_enzyme.fasta"
    sequence = _read_fasta(seq_path)
    manager = RunManager(tmp_path)
    result = manager.run(sequence)
    report = result["report"]
    outputs = report["outputs"]
    assert int(outputs["sequence_length"]) == len(sequence)
    assert float(outputs["mean_plddt"]) >= 50.0
    assert result["coordinator_decision"] == "ContinueExecution"
