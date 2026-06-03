from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.package_surface_pressure import (
    PACKAGE_SURFACE_PRESSURE_PATH,
    build_package_surface_pressure_report,
    run,
    validate_package_surface_pressure,
)


def test_package_surface_pressure_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_surface_pressure_report_tracks_public_breadth_vs_owner_depth() -> None:
    report = build_package_surface_pressure_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_SURFACE_PRESSURE_PATH.exists()
    assert by_package["bijux-proteomics-foundation"].root_export_symbol_count >= 10
    assert by_package["bijux-proteomics-core"].public_breadth_count == 13
    assert by_package["bijux-proteomics-runtime"].breadth_to_owner_ratio < 1.0
    assert any(entry.breadth_outpaces_owner_logic for entry in report.entries)


def test_package_surface_pressure_release_guard_has_no_failures() -> None:
    assert validate_package_surface_pressure() == ()
