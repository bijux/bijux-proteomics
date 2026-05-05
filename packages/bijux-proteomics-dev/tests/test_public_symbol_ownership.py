from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.api.public_symbol_ownership import (
    CANONICAL_PUBLIC_SYMBOL_OWNERSHIP_PATH,
    build_public_symbol_ownership,
    run,
    validate_public_symbol_ownership,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_public_symbol_ownership_map_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_public_symbol_ownership_assigns_one_owner_per_symbol() -> None:
    entries = build_public_symbol_ownership()
    owners_by_symbol: dict[str, set[str]] = {}
    for entry in entries:
        owners_by_symbol.setdefault(entry.symbol_name, set()).add(
            entry.owner_distribution_name
        )

    assert len(entries) >= 500
    assert owners_by_symbol["DocumentSchema"] == {"bijux-proteomics-foundation"}
    assert owners_by_symbol["EvidenceTrustScoreInput"] == {
        "bijux-proteomics-knowledge"
    }
    assert owners_by_symbol["AnalyticalContrastRecommendation"] == {
        "bijux-proteomics-intelligence"
    }
    assert CANONICAL_PUBLIC_SYMBOL_OWNERSHIP_PATH.exists()


def test_public_symbol_ownership_rejects_duplicate_canonical_root_exports() -> None:
    assert validate_public_symbol_ownership() == ()
