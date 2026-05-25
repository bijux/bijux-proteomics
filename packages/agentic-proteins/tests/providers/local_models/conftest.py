# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from agentic_proteins_testsupport.paths import repo_root


@pytest.fixture(scope="session")
def ROOT() -> Path:
    """Return the repository root path."""
    return repo_root()


@pytest.fixture(scope="session")
def PACKAGE_ROOT(ROOT: Path) -> Path:
    """Return the agentic-proteins package root."""

    return ROOT / "packages" / "agentic-proteins"


@pytest.fixture(scope="session")
def ARTIFACTS_DIR(ROOT: Path) -> Path:
    """Return the base artifacts directory for real-local tests."""
    return ROOT / "artifacts" / "local_model_tests"


@pytest.fixture()
def run_output_dir(ARTIFACTS_DIR: Path) -> Callable[[str, str], Path]:
    """Create and return a per-run output directory."""

    def _make(case_name: str, provider: str) -> Path:
        outdir = ARTIFACTS_DIR / case_name / provider
        outdir.mkdir(parents=True, exist_ok=True)
        return outdir

    return _make
