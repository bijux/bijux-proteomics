"""Tests for repository API freeze contract checks."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.api.contracts.freeze_contracts import run as run_api_freeze_contracts


def test_api_freeze_contracts_pass_for_repository() -> None:
    repo_root = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())
    assert run_api_freeze_contracts(repo_root) == 0
