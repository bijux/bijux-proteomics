"""Tests for repository OpenAPI drift checks."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.api.openapi_drift import run as run_openapi_drift


def test_openapi_drift_passes_for_repository() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    assert run_openapi_drift(repo_root) == 0
