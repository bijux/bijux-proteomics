from __future__ import annotations

from bijux_proteomics_dev.api.foundation_size_reuse import (
    FOUNDATION_SIZE_REUSE_PATH,
    build_foundation_size_reuse_report,
    run,
    validate_foundation_size_reuse,
)


def test_foundation_size_reuse_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_foundation_size_reuse_report_keeps_root_breadth_paired_with_reuse() -> None:
    report = build_foundation_size_reuse_report()
    metrics = report.metrics
    guard = report.guard

    assert FOUNDATION_SIZE_REUSE_PATH.exists()
    assert metrics.root_public_symbol_count == guard.baseline_root_public_symbol_count
    assert metrics.root_consumer_module_count == guard.baseline_root_consumer_module_count
    assert metrics.root_consumer_distribution_count == 6
    assert metrics.root_consumer_modules_per_symbol >= 7.4
    assert metrics.live_compatibility_wrapper_count == 0
    assert metrics.dead_direct_export_count > metrics.live_direct_export_count


def test_foundation_size_reuse_release_guard_has_no_failures() -> None:
    assert validate_foundation_size_reuse() == ()
