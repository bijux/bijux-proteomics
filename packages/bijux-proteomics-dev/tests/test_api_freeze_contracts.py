"""Tests for repository API freeze contract checks."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.api.freeze_contracts import run as run_api_freeze_contracts


def test_api_freeze_contracts_pass_for_repository() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    assert run_api_freeze_contracts(repo_root) == 0
