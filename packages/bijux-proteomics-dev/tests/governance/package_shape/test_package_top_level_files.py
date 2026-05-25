from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.package_top_level_files import (
    PACKAGE_TOP_LEVEL_FILES_PATH,
    build_package_top_level_file_report,
    run,
    validate_package_top_level_files,
)


def test_package_top_level_file_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_top_level_file_report_tracks_current_root_file_rationale() -> None:
    report = build_package_top_level_file_report()
    entries = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_TOP_LEVEL_FILES_PATH.exists()
    assert len(report.entries) == 16
    assert report.guard.max_total_top_level_file_count == 38
    assert entries["bijux-proteomics-core"].top_level_files == (
        "__init__.py",
        "_scientific_tables.py",
        "_tabular.py",
        "programs.py",
        "public_api.py",
    )
    assert entries["bijux-proteomics-foundation"].top_level_files == (
        "__init__.py",
        "_package_aliases.py",
        "public_api.py",
    )
    assert entries["bijux-proteomics-lab"].top_level_files == (
        "__init__.py",
        "public_api.py",
    )
    assert entries["bijux-proteomics-runtime"].top_level_files == (
        "__init__.py",
        "public_api.py",
    )


def test_package_top_level_file_release_guard_has_no_failures() -> None:
    assert validate_package_top_level_files() == ()
