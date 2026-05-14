from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast

from bijux_proteomics_dev.governance.foundation.root_api_policy import (
    run,
    validate_foundation_root_api_policy,
)
import bijux_proteomics_foundation

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
FOUNDATION_ROOT = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-foundation"
    / "src"
    / "bijux_proteomics_foundation"
    / "__init__.py"
)
FOUNDATION_ROOT_API_POLICY = (
    REPO_ROOT / "configs" / "package-governance" / "foundation-root-api.toml"
)


def _policy() -> dict[str, Any]:
    return tomllib.loads(FOUNDATION_ROOT_API_POLICY.read_text(encoding="utf-8"))


def _symbol_entries(policy: dict[str, Any]) -> list[dict[str, Any]]:
    entries = policy["symbol"]
    assert isinstance(entries, list)
    assert all(isinstance(entry, dict) for entry in entries)
    return [cast(dict[str, Any], entry) for entry in entries]


def _budget(policy: dict[str, Any]) -> dict[str, int]:
    budget = policy["budget"]
    assert isinstance(budget, dict)
    return {
        "max_public_symbols": int(budget["max_public_symbols"]),
        "max_init_lines": int(budget["max_init_lines"]),
    }


def test_foundation_root_api_policy_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_foundation_root_api_matches_curated_policy() -> None:
    policy = _policy()
    entries = _symbol_entries(policy)

    assert [entry["name"] for entry in entries] == list(
        bijux_proteomics_foundation.__all__
    )
    assert all(entry["owner_module"] for entry in entries)
    assert all(entry["rationale"] for entry in entries)


def test_foundation_root_api_stays_within_budget() -> None:
    policy = _policy()
    budget = _budget(policy)
    init_lines = FOUNDATION_ROOT.read_text(encoding="utf-8").splitlines()

    assert len(bijux_proteomics_foundation.__all__) <= budget["max_public_symbols"]
    assert len(init_lines) <= budget["max_init_lines"]


def test_foundation_root_api_excludes_removed_convenience_exports() -> None:
    removed = {
        "build_identifier",
        "ContractConflictError",
        "ContractNotFoundError",
        "CycleId",
        "IdentifierKind",
        "PromotionId",
        "ReviewId",
        "SchemaCompatibility",
        "assess_schema_compatibility",
    }

    assert removed.isdisjoint(bijux_proteomics_foundation.__all__)


def test_foundation_root_api_policy_has_no_validation_failures() -> None:
    assert validate_foundation_root_api_policy() == ()
