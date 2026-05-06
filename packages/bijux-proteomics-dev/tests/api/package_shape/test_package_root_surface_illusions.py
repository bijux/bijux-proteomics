from __future__ import annotations

from bijux_proteomics_dev.api.package_shape.package_root_surface_illusions import (
    PACKAGE_ROOT_SURFACE_ILLUSIONS_PATH,
    build_package_root_surface_illusion_report,
    run,
    validate_package_root_surface_illusions,
)


def test_package_root_surface_illusion_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_root_surface_illusion_report_tracks_root_export_masking() -> None:
    report = build_package_root_surface_illusion_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_ROOT_SURFACE_ILLUSIONS_PATH.exists()
    assert by_package["bijux-proteomics-foundation"].illusion_reasons == ()
    assert by_package["bijux-proteomics-foundation"].root_surface_hides_owner_depth is False
    assert by_package["bijux-proteomics-core"].compatibility_surfaces == ()
    assert any(entry.root_surface_hides_owner_depth for entry in report.entries)


def test_package_root_surface_illusion_release_guard_has_no_failures() -> None:
    assert validate_package_root_surface_illusions() == ()
