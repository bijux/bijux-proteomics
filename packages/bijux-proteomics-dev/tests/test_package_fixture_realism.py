from __future__ import annotations

from bijux_proteomics_dev.api.package_fixture_realism import (
    PACKAGE_FIXTURE_REALISM_PATH,
    build_package_fixture_realism_report,
    run,
    validate_package_fixture_realism,
)


def test_package_fixture_realism_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_fixture_realism_report_tracks_serious_fixture_depth() -> None:
    report = build_package_fixture_realism_report()
    entries = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_FIXTURE_REALISM_PATH.exists()
    assert len(report.entries) == 8
    assert entries["bijux-proteomics-core"].toy_named_fixture_count == 1
    assert entries["bijux-proteomics-runtime"].realistic_fixture_count_ge_1024 == 6
    assert report.guard.max_total_toy_named_fixture_count == 1
    assert report.guard.min_serious_package_with_realistic_fixtures_count == 4


def test_package_fixture_realism_release_guard_has_no_failures() -> None:
    assert validate_package_fixture_realism() == ()
