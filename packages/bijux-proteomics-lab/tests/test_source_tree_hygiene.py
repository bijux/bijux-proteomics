# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path


LAB_SRC_ROOT = Path("packages/bijux-proteomics-lab/src/bijux_proteomics_lab")
LAB_TEST_ROOT = Path("packages/bijux-proteomics-lab/tests")


def test_lab_source_tree_excludes_bytecode_artifacts() -> None:
    forbidden_paths = sorted(
        path.relative_to(LAB_SRC_ROOT)
        for path in LAB_SRC_ROOT.rglob("*")
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}
    )
    forbidden_paths.extend(
        sorted(
            path.relative_to(LAB_TEST_ROOT)
            for path in LAB_TEST_ROOT.rglob("*")
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}
        )
    )

    assert forbidden_paths == []
