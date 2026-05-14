from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.package_fixture_scenario_coverage import (
    PACKAGE_FIXTURE_SCENARIO_COVERAGE_PATH,
    build_package_fixture_scenario_coverage_report,
    run,
    validate_package_fixture_scenario_coverage,
)
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    workspace_package_names,
)


def test_package_fixture_scenario_coverage_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_fixture_scenario_coverage_report_tracks_fixture_depth_categories() -> (
    None
):
    report = build_package_fixture_scenario_coverage_report()
    entries = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_FIXTURE_SCENARIO_COVERAGE_PATH.exists()
    assert set(entries) == set(workspace_package_names())
    assert report.guard.min_total_medium_realistic_fixture_count >= 1
    assert report.guard.min_total_negative_fixture_count >= 1
    assert report.guard.min_total_ambiguity_fixture_count >= 1
    assert report.guard.min_total_contradiction_fixture_count >= 1
    assert report.guard.min_total_degraded_provenance_fixture_count >= 1
    assert report.guard.min_total_benchmark_fixture_count >= 1
    assert entries["bijux-proteomics-runtime"].degraded_provenance_fixture_count >= 1
    assert entries["bijux-proteomics-intelligence"].ambiguity_fixture_count >= 1
    assert entries["bijux-proteomics-core"].contradiction_fixture_count >= 1
    assert entries["bijux-proteomics-lab"].degraded_provenance_fixture_count >= 1


def test_package_fixture_scenario_coverage_release_guard_has_no_failures() -> None:
    assert validate_package_fixture_scenario_coverage() == ()
