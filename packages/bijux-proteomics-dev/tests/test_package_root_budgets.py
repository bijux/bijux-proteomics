from __future__ import annotations

from bijux_proteomics_dev.api.package_root_budgets import (
    PACKAGE_ROOT_BUDGETS_PATH,
    build_package_root_budget_report,
    run,
    validate_package_root_budgets,
)


def test_package_root_budget_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_root_budget_report_keeps_roots_within_governed_budgets() -> None:
    report = build_package_root_budget_report()
    entries = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_ROOT_BUDGETS_PATH.exists()
    assert report.total_init_line_count == 170
    assert report.over_budget_packages == ()
    assert entries["bijux-proteomics-foundation"].max_init_lines == 45
    assert entries["bijux-proteomics-foundation"].within_budget is True
    assert entries["bijux-proteomics-lab"].max_public_symbols == 4
    assert entries["bijux-proteomics-lab"].within_budget is True
    assert entries["agentic-proteins"].max_init_lines is None


def test_package_root_budget_release_guard_has_no_failures() -> None:
    assert validate_package_root_budgets() == ()
