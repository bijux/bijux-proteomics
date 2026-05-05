from __future__ import annotations

from bijux_proteomics_dev.api.source_delivery_history import (
    SOURCE_DELIVERY_HISTORY_PATH,
    build_source_delivery_history_report,
    run,
    validate_source_delivery_history,
)


def test_source_delivery_history_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_source_delivery_history_report_keeps_delivery_sequence_out_of_source_text() -> None:
    report = build_source_delivery_history_report()

    assert SOURCE_DELIVERY_HISTORY_PATH.exists()
    assert report.entries == ()
    assert report.guard.max_total_violation_count == 0


def test_source_delivery_history_release_guard_has_no_failures() -> None:
    assert validate_source_delivery_history() == ()
