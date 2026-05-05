from __future__ import annotations

from bijux_proteomics_dev.api.reopened_debt_ledger import (
    REOPENED_DEBT_LEDGER_PATH,
    build_reopened_debt_ledger_report,
    run,
    validate_reopened_debt_ledger,
)


def test_reopened_debt_ledger_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_reopened_debt_ledger_tracks_live_structural_debt() -> None:
    report = build_reopened_debt_ledger_report()
    debt_ids = {entry.debt_id for entry in report.entries}

    assert REOPENED_DEBT_LEDGER_PATH.exists()
    assert "bijux-proteomics-core:mixed-responsibility-modules" in debt_ids
    assert "bijux-proteomics-foundation:compatibility-surfaces" in debt_ids
    assert "bijux-proteomics-runtime:reopened-completion-claim" in debt_ids
    assert "bijux-proteomics-lab:docs-claim-gap" in debt_ids
    assert any(entry.severity == "high" for entry in report.entries)


def test_reopened_debt_ledger_entries_are_valid() -> None:
    assert validate_reopened_debt_ledger() == ()
