# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )


def test_public_api_smoke_support_stays_outside_dev_source_tree() -> None:
    repo_root = _repo_root()

    support_path = (
        repo_root
        / "packages"
        / "bijux-proteomics-dev"
        / "tests"
        / "package"
        / "public_api_smoke_support.py"
    )
    assert support_path.exists()
    assert "packages/bijux-proteomics-dev/tests/package/" in support_path.as_posix()
    assert "packages/bijux-proteomics-dev/src/" not in support_path.as_posix()


def test_public_api_smoke_support_does_not_import_dev_package() -> None:
    support_path = (
        _repo_root()
        / "packages"
        / "bijux-proteomics-dev"
        / "tests"
        / "package"
        / "public_api_smoke_support.py"
    )
    tree = ast.parse(support_path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert not node.module.startswith("bijux_proteomics_dev"), (
                "public api smoke support should stay independent from the dev package"
            )
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("bijux_proteomics_dev"), (
                    "public api smoke support should stay independent from the dev package"
                )
