"""Tests for repository OpenAPI drift checks."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.governance.contracts.openapi_drift import (
    run as run_openapi_drift,
)


def test_openapi_drift_passes_for_repository() -> None:
    repo_root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )
    assert run_openapi_drift(repo_root) == 0
