# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    path = Path(__file__).resolve()
    for parent in [path] + list(path.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("pyproject.toml not found for repo root")


def package_tests_root() -> Path:
    return repo_root() / "packages" / "agentic-proteins" / "tests"
