# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys

import pytest

from bijux_proteomics_foundation.testing.pytest_markers import (
    apply_default_test_markers,
)

sys.dont_write_bytecode = True
CORE_CLEAN_ROOTS = (
    Path("packages/bijux-proteomics-core/src/bijux_proteomics"),
    Path("packages/bijux-proteomics-core/tests"),
)


def _remove_core_bytecode_artifacts() -> None:
    for root in CORE_CLEAN_ROOTS:
        if not root.exists():
            continue
        for current_root, dirnames, filenames in os.walk(root, topdown=False):
            current_path = Path(current_root)
            for dirname in dirnames:
                if dirname != "__pycache__":
                    continue
                shutil.rmtree(current_path / dirname, ignore_errors=True)
            for filename in filenames:
                path = current_path / filename
                if path.suffix in {".pyc", ".pyo"}:
                    path.unlink(missing_ok=True)


def pytest_sessionstart(session: pytest.Session) -> None:
    _remove_core_bytecode_artifacts()


def pytest_sessionfinish(session: pytest.Session, exitstatus: pytest.ExitCode) -> None:
    _remove_core_bytecode_artifacts()


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    apply_default_test_markers(
        items,
        benchmark_dirs=("benchmarks", "performance"),
        integration_dirs=("cli",),
    )


@pytest.fixture
def fasta_fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures" / "fasta"
