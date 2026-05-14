from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_dev.quality.architecture.runtime_boundaries import run

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)

pytestmark = pytest.mark.slow


def test_runtime_boundary_runner_passes_for_current_repository() -> None:
    assert run(REPO_ROOT) == 0
