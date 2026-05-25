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
PACKAGE_TREES = tuple(Path("packages").glob("*"))


def _remove_workspace_bytecode_artifacts() -> None:
    for root in PACKAGE_TREES:
        for path in root.rglob("*"):
            if path.is_dir() and path.name == "__pycache__":
                shutil.rmtree(path)
                continue
            if path.suffix in {".pyc", ".pyo"}:
                path.unlink()


def pytest_sessionstart(session: pytest.Session) -> None:
    _remove_workspace_bytecode_artifacts()


def pytest_sessionfinish(session: pytest.Session, exitstatus: pytest.ExitCode) -> None:
    _remove_workspace_bytecode_artifacts()


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    apply_default_test_markers(items)
