# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from agentic_proteins.tools.heuristic import HeuristicStructureTool
from agentic_proteins.tools.schemas import InvocationInput
from agentic_proteins_testsupport.paths import package_tests_root


def _read_fasta(path: Path) -> str:
    lines = path.read_text().splitlines()
    return "".join(line.strip() for line in lines if not line.startswith(">"))


def test_real_protein_regression() -> None:
    fixtures = {
        "small_enzyme.fasta": "89cc49be82577b86c9b4e766c5d8ab8788dd7ac1233a0f65331e0f5c44815cf9",
        "membrane_protein.fasta": "b2fa5c729ac59d361bb123cae9b798099369ada64bc299da2c28b3b9449a8c74",
        "disordered_protein.fasta": "736dfdbd59a6878397cf077ed6a98b2598e54211f7ab1e25f3e4109a365d153e",
    }
    tool = HeuristicStructureTool()
    for name, expected_hash in fixtures.items():
        seq_path = package_tests_root() / "fixtures" / "proteins" / name
        sequence = _read_fasta(seq_path)
        result = tool.run(
            invocation_id="invocation-1",
            inputs=[InvocationInput(name="sequence", value=sequence)],
        )
        outputs = {item.name: item.value for item in result.outputs}
        data = json.dumps(outputs, sort_keys=True, separators=(",", ":"))
        actual_hash = __import__("hashlib").sha256(data.encode()).hexdigest()
        assert actual_hash == expected_hash
