# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

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
KNOWLEDGE_CLEAN_ROOTS = (
    Path("packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge"),
    Path("packages/bijux-proteomics-knowledge/tests"),
)


def _remove_knowledge_bytecode_artifacts() -> None:
    for root in KNOWLEDGE_CLEAN_ROOTS:
        for path in root.rglob("*"):
            if path.is_dir() and path.name == "__pycache__":
                shutil.rmtree(path)
                continue
            if path.suffix in {".pyc", ".pyo"}:
                path.unlink()


def pytest_sessionstart(session: pytest.Session) -> None:
    _remove_knowledge_bytecode_artifacts()


def pytest_sessionfinish(session: pytest.Session, exitstatus: pytest.ExitCode) -> None:
    _remove_knowledge_bytecode_artifacts()


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    apply_default_test_markers(items, external_data_dirs=("references",))
