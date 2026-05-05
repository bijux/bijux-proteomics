from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.release.package_family_readiness import (
    build_package_family_readiness_reports,
    validate_package_family_readiness,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_package_family_readiness_reports_cover_declared_families() -> None:
    reports = build_package_family_readiness_reports(REPO_ROOT)

    assert len(reports) == 3
    assert {report.family_id for report in reports} == {
        "compatibility-bridge",
        "scientific-platform",
        "runtime-service",
    }
    assert all(report.ready for report in reports)


def test_package_family_readiness_manifest_is_valid_for_current_repo() -> None:
    assert validate_package_family_readiness(REPO_ROOT) == ()
