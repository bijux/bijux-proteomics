from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.package_topology_drift import (
    PACKAGE_TOPOLOGY_DRIFT_PATH,
    build_package_topology_drift_report,
    run,
    validate_package_topology_drift,
)


def test_package_topology_drift_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_topology_drift_report_tracks_flatness_and_doc_mismatch() -> None:
    report = build_package_topology_drift_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_TOPOLOGY_DRIFT_PATH.exists()
    assert len(report.entries) == 16
    assert by_package["bijux-proteomics-runtime"].undocumented_owner_families == ()
    assert by_package["bijux-proteomics-foundation"].historical_topology_mentions == ()
    assert by_package["bijux-proteomics-foundation"].undocumented_owner_families == ()
    assert all(not entry.docs_tree_contradiction for entry in report.entries)
    assert {
        entry.distribution_name
        for entry in report.entries
        if entry.historical_shape_dominates_design
    } == {"proteomics", "proteomics-core", "proteomics-runtime"}


def test_package_topology_drift_release_guard_has_no_failures() -> None:
    assert validate_package_topology_drift() == ()
