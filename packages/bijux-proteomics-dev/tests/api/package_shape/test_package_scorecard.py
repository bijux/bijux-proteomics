from __future__ import annotations

from bijux_proteomics_dev.api.package_shape.package_scorecard import (
    PACKAGE_SCORECARD_PATH,
    build_package_scorecard_report,
    run,
    validate_package_scorecard,
)


def test_package_scorecard_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_scorecard_combines_owner_depth_breadth_and_proof() -> None:
    report = build_package_scorecard_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_SCORECARD_PATH.exists()
    assert len(report.entries) == 8
    assert by_package["bijux-proteomics-runtime"].proof_depth_count >= 1
    assert by_package["bijux-proteomics-foundation"].wrapper_module_count == 6
    assert by_package["bijux-proteomics-lab"].architectural_ready is False
    assert any(not entry.architectural_ready for entry in report.entries)


def test_package_scorecard_release_guard_has_no_failures() -> None:
    assert validate_package_scorecard() == ()
