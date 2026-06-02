# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import shutil

RUNTIME_SRC_ROOT = Path(
    "packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime"
)
RUNTIME_TEST_ROOT = Path("packages/bijux-proteomics-runtime/tests")


def _remove_runtime_bytecode_artifacts() -> None:
    for root in (RUNTIME_SRC_ROOT, RUNTIME_TEST_ROOT):
        for path in root.rglob("*"):
            if path.is_dir() and path.name == "__pycache__":
                shutil.rmtree(path, ignore_errors=True)
                continue
            if path.suffix in {".pyc", ".pyo"}:
                path.unlink(missing_ok=True)


def test_runtime_source_tree_excludes_bytecode_artifacts() -> None:
    _remove_runtime_bytecode_artifacts()
    forbidden_paths = sorted(
        path.relative_to(RUNTIME_SRC_ROOT)
        for path in RUNTIME_SRC_ROOT.rglob("*")
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}
    )
    forbidden_paths.extend(
        sorted(
            path.relative_to(RUNTIME_TEST_ROOT)
            for path in RUNTIME_TEST_ROOT.rglob("*")
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}
        )
    )

    assert forbidden_paths == []
