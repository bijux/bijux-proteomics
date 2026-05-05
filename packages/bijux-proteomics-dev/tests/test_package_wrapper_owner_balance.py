from __future__ import annotations

from bijux_proteomics_dev.api.package_wrapper_owner_balance import (
    PACKAGE_WRAPPER_OWNER_BALANCE_PATH,
    build_package_wrapper_owner_balance_report,
    run,
    validate_package_wrapper_owner_balance,
)


def test_package_wrapper_owner_balance_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_wrapper_owner_balance_report_tracks_wrapper_pressure_against_owner_depth() -> None:
    report = build_package_wrapper_owner_balance_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_WRAPPER_OWNER_BALANCE_PATH.exists()
    assert by_package["bijux-proteomics-foundation"].wrapper_module_count == 0
    assert by_package["bijux-proteomics-foundation"].wrapper_to_owner_ratio == 0.0
    assert by_package["bijux-proteomics-core"].wrapper_module_count == 4
    assert by_package["bijux-proteomics-runtime"].owner_logic_module_count > 10
    assert any(entry.wrapper_module_count for entry in report.entries)


def test_package_wrapper_owner_balance_release_guard_has_no_failures() -> None:
    assert validate_package_wrapper_owner_balance() == ()
