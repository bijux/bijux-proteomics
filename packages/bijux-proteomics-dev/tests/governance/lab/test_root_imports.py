from __future__ import annotations

from bijux_proteomics_dev.governance.lab.root_imports import (
    BANNED_ROOTS,
    LAB_ROOT_IMPORTS_PATH,
    build_lab_root_import_report,
    run,
    validate_lab_root_imports,
)


def test_lab_root_import_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_lab_root_import_report_tracks_zero_owner_violations() -> None:
    report = build_lab_root_import_report()
    metrics = report.metrics
    guard = report.guard

    assert LAB_ROOT_IMPORTS_PATH.exists()
    assert metrics.scanned_module_count == 39
    assert metrics.banned_root_count == len(BANNED_ROOTS)
    assert metrics.banned_root_count == 5
    assert metrics.violation_count == guard.baseline_violation_count
    assert metrics.violation_count == 0
    assert metrics.violations == ()


def test_lab_root_import_release_guard_has_no_failures() -> None:
    assert validate_lab_root_imports() == ()
