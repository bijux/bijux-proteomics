# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path


def _looks_like_repository_root(path: Path) -> bool:
    return (
        (path / "pyproject.toml").exists()
        and (path / "configs" / "pytest.ini").exists()
        and (path / "packages" / "agentic-proteins").exists()
    )


def repo_root() -> Path:
    path = Path(__file__).resolve()
    for parent in [path] + list(path.parents):
        if _looks_like_repository_root(parent):
            return parent
    raise FileNotFoundError("repository root not found")


def package_tests_root() -> Path:
    return repo_root() / "packages" / "agentic-proteins" / "tests"
