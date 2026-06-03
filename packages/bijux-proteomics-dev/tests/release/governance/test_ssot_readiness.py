from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.release.governance.ssot_readiness import (
    build_ssot_readiness_report,
    validate_ssot_readiness,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_ssot_readiness_report_covers_every_ownership_check() -> None:
    report = build_ssot_readiness_report(REPO_ROOT)

    assert {entry.check_id for entry in report} == {
        "compatibility-bridge",
        "duplicate-model-ownership",
        "package-substance",
        "public-symbol-ownership",
        "scientific-concept-ownership",
    }
    assert all(entry.ready for entry in report)
    assert all(entry.issue_count == 0 for entry in report)


def test_ssot_readiness_is_release_clean() -> None:
    assert validate_ssot_readiness(REPO_ROOT) == ()
