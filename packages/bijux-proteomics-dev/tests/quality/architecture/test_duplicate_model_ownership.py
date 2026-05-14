from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_dev.quality.architecture.duplicate_model_ownership import (
    DUPLICATE_MODEL_OWNERSHIP_CSV_PATH,
    DUPLICATE_MODEL_OWNERSHIP_SUMMARY_PATH,
    build_duplicate_model_inventory,
    run,
    validate_duplicate_model_ownership,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


@pytest.mark.slow
def test_duplicate_model_ownership_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_duplicate_model_inventory_tracks_canonical_product_models() -> None:
    definitions = build_duplicate_model_inventory(REPO_ROOT)
    package_names = {definition.package_name for definition in definitions}

    assert package_names == {
        "bijux-proteomics-core",
        "bijux-proteomics-foundation",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
    }
    assert all(definition.model_name for definition in definitions)
    assert DUPLICATE_MODEL_OWNERSHIP_CSV_PATH.exists()
    assert DUPLICATE_MODEL_OWNERSHIP_SUMMARY_PATH.exists()


def test_duplicate_model_ownership_is_release_clean() -> None:
    assert validate_duplicate_model_ownership(REPO_ROOT) == ()


def test_duplicate_model_ownership_summary_reports_zero_drift() -> None:
    summary_text = DUPLICATE_MODEL_OWNERSHIP_SUMMARY_PATH.read_text(encoding="utf-8")

    assert "current duplicate model issues: 0" in summary_text
