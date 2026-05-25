# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import shutil
import sys

import pytest
from bijux_proteomics_foundation.testing.pytest_markers import (
    apply_default_test_markers,
)

sys.dont_write_bytecode = True
FOUNDATION_CLEAN_ROOTS = (
    Path("packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation"),
    Path("packages/bijux-proteomics-foundation/tests"),
)


def _remove_foundation_bytecode_artifacts() -> None:
    for root in FOUNDATION_CLEAN_ROOTS:
        for path in root.rglob("*"):
            if path.is_dir() and path.name == "__pycache__":
                shutil.rmtree(path)
                continue
            if path.suffix in {".pyc", ".pyo"}:
                path.unlink()


def pytest_sessionstart(session: pytest.Session) -> None:
    _remove_foundation_bytecode_artifacts()


def pytest_sessionfinish(session: pytest.Session, exitstatus: pytest.ExitCode) -> None:
    _remove_foundation_bytecode_artifacts()


def pytest_runtest_setup(item: pytest.Item) -> None:
    _remove_foundation_bytecode_artifacts()


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    apply_default_test_markers(items, benchmark_dirs=("performance",))
