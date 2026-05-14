# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

INTELLIGENCE_TREE_ROOTS = (
    Path("packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence"),
    Path("packages/bijux-proteomics-intelligence/tests"),
)


def test_intelligence_source_tree_has_no_bytecode_artifacts() -> None:
    offenders = sorted(
        str(path)
        for root in INTELLIGENCE_TREE_ROOTS
        for path in root.rglob("*")
        if (path.is_dir() and path.name == "__pycache__")
        or path.suffix in {".pyc", ".pyo"}
    )

    assert offenders == []
