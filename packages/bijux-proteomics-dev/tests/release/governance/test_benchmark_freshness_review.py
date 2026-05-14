from __future__ import annotations

from datetime import date

import pytest

from bijux_proteomics_dev.release.governance.benchmark_freshness_review import (
    build_benchmark_freshness_review,
    run,
)


def test_benchmark_freshness_review_page_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_benchmark_freshness_review_covers_all_flagship_families() -> None:
    entries = build_benchmark_freshness_review()
    by_family = {entry.workflow_family.value: entry for entry in entries}

    assert tuple(by_family) == ("dda", "dia", "lfq", "multiplex", "ptm", "targeted")
    assert by_family["dda"].review_state == "current"
    assert by_family["dda"].remote_reference_state == "recorded_available"
    assert by_family["dda"].release_language_floor == "outsider_auditable_bounded"
    assert by_family["multiplex"].release_language_floor == "internal_support_only"


def test_benchmark_freshness_review_downgrades_when_review_window_expires(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.benchmark_freshness_review._today",
        lambda: date(2028, 5, 9),
    )

    entries = {
        entry.workflow_family.value: entry
        for entry in build_benchmark_freshness_review()
    }

    assert entries["dda"].review_state == "overdue"
    assert entries["dda"].release_language_floor == "review_grade_bounded"
    assert entries["dda"].blockers
