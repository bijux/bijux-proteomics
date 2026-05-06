from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.governance.runtime.live_contracts import (
    validate_runtime_live_contract,
)


def test_runtime_live_api_contract_matches_checked_in_schema() -> None:
    repo_root = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())
    assert validate_runtime_live_contract(repo_root) == []
