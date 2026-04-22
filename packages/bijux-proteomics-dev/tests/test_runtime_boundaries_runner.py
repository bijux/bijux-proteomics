from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.architecture.runtime_boundaries import run

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_runtime_boundary_runner_passes_for_current_repository() -> None:
    assert run(REPO_ROOT) == 0
