# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import shutil
import sys

import pytest
from bijux_proteomics_foundation.testing.pytest_markers import (
    apply_default_test_markers,
)

sys.dont_write_bytecode = True
RUNTIME_CLEAN_ROOTS = (
    Path("packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime"),
    Path("packages/bijux-proteomics-runtime/tests"),
)


def remove_runtime_bytecode_artifacts() -> None:
    for root in RUNTIME_CLEAN_ROOTS:
        for path in root.rglob("*"):
            if path.is_dir() and path.name == "__pycache__":
                shutil.rmtree(path, ignore_errors=True)
                continue
            if path.suffix in {".pyc", ".pyo"}:
                path.unlink(missing_ok=True)


remove_runtime_bytecode_artifacts()


def pytest_sessionstart(session: pytest.Session) -> None:
    remove_runtime_bytecode_artifacts()


def pytest_sessionfinish(session: pytest.Session, exitstatus: pytest.ExitCode) -> None:
    remove_runtime_bytecode_artifacts()


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    apply_default_test_markers(
        items,
        benchmark_dirs=("performance",),
        integration_dirs=("api", "execution", "workflows"),
    )
