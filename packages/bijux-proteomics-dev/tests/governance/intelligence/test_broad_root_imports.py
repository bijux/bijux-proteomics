from __future__ import annotations

from bijux_proteomics_dev.governance.intelligence.broad_root_imports import (
    BANNED_ROOTS,
    INTELLIGENCE_BROAD_ROOT_IMPORTS_PATH,
    build_intelligence_broad_root_import_report,
    run,
    validate_intelligence_broad_root_imports,
)


def test_intelligence_broad_root_import_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_intelligence_broad_root_import_report_tracks_zero_owner_violations() -> None:
    report = build_intelligence_broad_root_import_report()
    metrics = report.metrics
    guard = report.guard

    assert INTELLIGENCE_BROAD_ROOT_IMPORTS_PATH.exists()
    assert metrics.scanned_module_count == 72
    assert metrics.banned_root_count == len(BANNED_ROOTS)
    assert metrics.banned_root_count == 3
    assert metrics.violation_count == guard.baseline_violation_count
    assert metrics.violation_count == 0
    assert metrics.violations == ()


def test_intelligence_broad_root_import_release_guard_has_no_failures() -> None:
    assert validate_intelligence_broad_root_imports() == ()
