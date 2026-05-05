from __future__ import annotations

from bijux_proteomics_dev.api.package_oversized_mixed_modules import (
    PACKAGE_OVERSIZED_MIXED_MODULES_PATH,
    build_package_oversized_mixed_module_report,
    run,
    validate_package_oversized_mixed_modules,
)


def test_package_oversized_mixed_module_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_oversized_mixed_module_report_tracks_split_follow_up_pressure() -> None:
    report = build_package_oversized_mixed_module_report()
    module_paths = {entry.module_path for entry in report.entries}

    assert PACKAGE_OVERSIZED_MIXED_MODULES_PATH.exists()
    assert len(report.entries) >= 10
    assert report.guard.max_largest_nonempty_line_count >= 2500
    assert (
        "packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/plans.py"
        in module_paths
    )
    assert (
        "packages/bijux-proteomics-lab/src/bijux_proteomics_lab/planning/assays.py"
        in module_paths
    )


def test_package_oversized_mixed_module_release_guard_has_no_failures() -> None:
    assert validate_package_oversized_mixed_modules() == ()
