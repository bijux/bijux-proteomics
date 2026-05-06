from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.release.readiness.package_family_readiness import (
    build_package_family_readiness_reports,
    validate_package_family_readiness,
)

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())


def test_package_family_readiness_reports_cover_declared_families() -> None:
    reports = build_package_family_readiness_reports(REPO_ROOT)
    by_family = {report.family_id: report for report in reports}

    assert len(reports) == 3
    assert {report.family_id for report in reports} == {
        "compatibility-bridge",
        "scientific-platform",
        "runtime-service",
    }
    assert any(not report.ready for report in reports)
    assert by_family["scientific-platform"].not_ready_package_names
    assert by_family["runtime-service"].publishable_package_count <= 2


def test_package_family_readiness_manifest_is_valid_for_current_repo() -> None:
    assert validate_package_family_readiness(REPO_ROOT) == ()
