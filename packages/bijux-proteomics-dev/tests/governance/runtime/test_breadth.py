from __future__ import annotations

from bijux_proteomics_dev.governance.runtime.breadth import (
    RUNTIME_BREADTH_PATH,
    build_runtime_breadth_report,
    run,
    validate_runtime_breadth,
)


def test_runtime_breadth_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_runtime_breadth_report_pairs_surface_growth_with_owned_logic() -> None:
    report = build_runtime_breadth_report()
    metrics = report.metrics
    guard = report.guard

    assert RUNTIME_BREADTH_PATH.exists()
    assert metrics.total_breadth_count == guard.baseline_total_breadth_count
    assert metrics.first_level_subtree_count == 8
    assert metrics.total_breadth_count == 26
    assert metrics.owner_execution_module_count == 139
    assert metrics.owner_execution_modules_per_surface >= 5.35
    assert metrics.thin_module_count == 26


def test_runtime_breadth_release_guard_has_no_failures() -> None:
    assert validate_runtime_breadth() == ()
