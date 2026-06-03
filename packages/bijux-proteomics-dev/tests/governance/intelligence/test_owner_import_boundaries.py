from __future__ import annotations

from bijux_proteomics_dev.governance.intelligence.owner_import_boundaries import (
    BANNED_MODULES,
    INTELLIGENCE_OWNER_IMPORT_BOUNDARIES_PATH,
    build_intelligence_owner_import_boundary_report,
    run,
    validate_intelligence_owner_import_boundaries,
)


def test_intelligence_owner_import_boundary_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_intelligence_owner_import_boundary_report_tracks_zero_violations() -> None:
    report = build_intelligence_owner_import_boundary_report()
    metrics = report.metrics
    guard = report.guard

    assert INTELLIGENCE_OWNER_IMPORT_BOUNDARIES_PATH.exists()
    assert metrics.scanned_module_count == 72
    assert metrics.banned_module_count == len(BANNED_MODULES)
    assert metrics.banned_module_count == 5
    assert metrics.violation_count == guard.baseline_violation_count
    assert metrics.violation_count == 0
    assert metrics.violations == ()


def test_intelligence_owner_import_boundaries_have_no_failures() -> None:
    assert validate_intelligence_owner_import_boundaries() == ()
