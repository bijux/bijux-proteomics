# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys

import pytest

from bijux_proteomics_foundation.testing.pytest_artifacts import (
    configure_hypothesis_artifacts,
)
from bijux_proteomics_foundation.testing.pytest_markers import (
    apply_default_test_markers,
)

ROOT = Path(__file__).resolve().parents[3]
configure_hypothesis_artifacts(ROOT)
sys.dont_write_bytecode = True
PACKAGE_TREES = tuple(Path("packages").glob("*"))


def _remove_workspace_bytecode_artifacts() -> None:
    for root in PACKAGE_TREES:
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
    _remove_workspace_bytecode_artifacts()


def pytest_sessionfinish(session: pytest.Session, exitstatus: pytest.ExitCode) -> None:
    _remove_workspace_bytecode_artifacts()


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    apply_default_test_markers(items)
