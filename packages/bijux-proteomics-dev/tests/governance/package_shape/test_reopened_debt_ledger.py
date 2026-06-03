from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.reopened_debt_ledger import (
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
    assert len(report.entries) == 16
    assert "agentic-proteins:reopened-completion-claim" in debt_ids
    assert "bijux-proteomics:reopened-completion-claim" in debt_ids
    assert "bijux-proteomics-core:mixed-responsibility-modules" in debt_ids
    assert "bijux-proteomics-dev:mixed-responsibility-modules" in debt_ids
    assert "bijux-proteomics-intelligence:mixed-responsibility-modules" in debt_ids
    assert "bijux-proteomics-knowledge:mixed-responsibility-modules" in debt_ids
    assert "bijux-proteomics-runtime:mixed-responsibility-modules" in debt_ids
    assert "bijux-proteomics-lab:mixed-responsibility-modules" in debt_ids
    assert "proteomics-core:reopened-completion-claim" in debt_ids
    assert "proteomics-runtime:reopened-completion-claim" in debt_ids
    assert not any(debt_id.endswith(":test-tree-gaps") for debt_id in debt_ids)
    assert not any(
        debt_id.startswith("bijux-proteomics-foundation:reopened-completion-claim")
        for debt_id in debt_ids
    )
    assert any(entry.severity == "high" for entry in report.entries)


def test_reopened_debt_ledger_entries_are_valid() -> None:
    assert validate_reopened_debt_ledger() == ()
