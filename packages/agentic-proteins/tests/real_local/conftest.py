# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.paths import repo_root


@pytest.fixture(scope="session")
def ROOT() -> Path:
    """Return the repository root path."""
    return repo_root()


@pytest.fixture(scope="session")
def ARTIFACTS_DIR(ROOT: Path) -> Path:
    """Return the base artifacts directory for real-local tests."""
    return ROOT / "artifacts" / "real_local_tests"


@pytest.fixture()
def run_output_dir(ARTIFACTS_DIR: Path) -> callable:
    """Create and return a per-run output directory."""

    def _make(case_name: str, provider: str) -> Path:
        outdir = ARTIFACTS_DIR / case_name / provider
        outdir.mkdir(parents=True, exist_ok=True)
        return outdir

    return _make
