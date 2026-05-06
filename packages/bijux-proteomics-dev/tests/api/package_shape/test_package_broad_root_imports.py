from __future__ import annotations

from bijux_proteomics_dev.api.package_shape.package_broad_root_imports import (
    PACKAGE_BROAD_ROOT_IMPORTS_PATH,
    build_package_broad_root_import_report,
    run,
    validate_package_broad_root_imports,
)


def test_package_broad_root_import_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_broad_root_import_report_tracks_owner_path_rewrites() -> None:
    report = build_package_broad_root_import_report()

    assert PACKAGE_BROAD_ROOT_IMPORTS_PATH.exists()
    assert report.entries == ()
    assert report.guard.max_total_broad_root_import_count == 0


def test_package_broad_root_import_release_guard_has_no_failures() -> None:
    assert validate_package_broad_root_imports() == ()
