from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.package_root_line_counts import (
    PACKAGE_ROOT_LINE_COUNTS_PATH,
    build_package_root_line_count_report,
    run,
    validate_package_root_line_count_report,
)


def test_package_root_line_count_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_root_line_count_report_tracks_current_root_shape() -> None:
    report = build_package_root_line_count_report()
    entries = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_ROOT_LINE_COUNTS_PATH.exists()
    assert len(report.entries) == 8
    assert report.guard.max_total_init_line_count == 146
    assert report.guard.max_total_top_level_python_module_count == 8
    assert entries["bijux-proteomics-foundation"].init_line_count == 45
    assert entries["bijux-proteomics-lab"].init_line_count == 11
    assert entries["bijux-proteomics-runtime"].top_level_python_module_count == 1


def test_package_root_line_count_release_guard_has_no_failures() -> None:
    assert validate_package_root_line_count_report() == ()
