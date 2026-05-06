# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path


CORE_SRC_ROOT = Path("packages/bijux-proteomics-core/src/bijux_proteomics")


def test_core_source_tree_excludes_bytecode_artifacts() -> None:
    forbidden_paths = sorted(
        path.relative_to(CORE_SRC_ROOT)
        for path in CORE_SRC_ROOT.rglob("*")
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}
    )

    assert forbidden_paths == []
