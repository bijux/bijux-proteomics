from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.api.runtime_live_contracts import (
    validate_runtime_live_contract,
)


def test_runtime_live_api_contract_matches_checked_in_schema() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    assert validate_runtime_live_contract(repo_root) == []
