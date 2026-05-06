from __future__ import annotations

from bijux_proteomics_dev.api.package_shape.package_wrapper_density import (
    PACKAGE_WRAPPER_DENSITY_PATH,
    build_package_wrapper_density_report,
    run,
    validate_package_wrapper_density,
)


def test_package_wrapper_density_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_wrapper_density_report_tracks_current_wrapper_pressure() -> None:
    report = build_package_wrapper_density_report()
    entries = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_WRAPPER_DENSITY_PATH.exists()
    assert len(report.entries) == 8
    assert report.guard.max_total_wrapper_module_count >= 20
    assert entries["bijux-proteomics-lab"].wrapper_module_count >= 4
    assert (
        entries["bijux-proteomics-lab"].max_wrapper_module_count
        == entries["bijux-proteomics-lab"].wrapper_module_count
    )
    assert entries["bijux-proteomics-runtime"].wrapper_module_count >= 4
    assert entries["agentic-proteins"].wrapper_density == 0.9932


def test_package_wrapper_density_release_guard_has_no_failures() -> None:
    assert validate_package_wrapper_density() == ()
