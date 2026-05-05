from __future__ import annotations

from pathlib import Path
import tomllib

import bijux_proteomics_foundation


REPO_ROOT = Path(__file__).resolve().parents[3]
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


def _policy() -> dict[str, object]:
    return tomllib.loads(FOUNDATION_ROOT_API_POLICY.read_text(encoding="utf-8"))


def test_foundation_root_api_matches_curated_policy() -> None:
    policy = _policy()
    entries = policy["symbol"]

    assert [entry["name"] for entry in entries] == list(
        bijux_proteomics_foundation.__all__
    )
    assert all(entry["owner_module"] for entry in entries)
    assert all(entry["rationale"] for entry in entries)


def test_foundation_root_api_stays_within_budget() -> None:
    policy = _policy()
    budget = policy["budget"]
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
