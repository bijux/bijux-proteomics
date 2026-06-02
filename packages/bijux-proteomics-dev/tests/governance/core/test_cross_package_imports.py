from __future__ import annotations

import pytest

from bijux_proteomics_dev.governance.core.cross_package_imports import (
    CORE_CROSS_PACKAGE_IMPORTS_PATH,
    build_core_cross_package_import_report,
    run,
    validate_core_cross_package_imports,
)


@pytest.mark.slow
def test_core_cross_package_import_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_core_cross_package_import_report_tracks_live_edges() -> None:
    report = build_core_cross_package_import_report()
    importers = {entry.importer_module_path for entry in report.entries}
    owner_counts = {
        owner_distribution: sum(
            1
            for entry in report.entries
            if entry.owner_distribution == owner_distribution
        )
        for owner_distribution in {
            "bijux-proteomics-runtime",
            "bijux-proteomics-intelligence",
            "bijux-proteomics-lab",
        }
    }

    assert CORE_CROSS_PACKAGE_IMPORTS_PATH.exists()
    assert "interfaces/execution/runtime_adapter.py" in importers
    assert "interfaces/runtime_plans.py" in importers
    assert "ptm/cards/review.py" in importers
    assert owner_counts["bijux-proteomics-runtime"] == report.guard.max_runtime_edges
    assert (
        owner_counts["bijux-proteomics-intelligence"]
        == report.guard.max_intelligence_edges
    )
    assert owner_counts["bijux-proteomics-lab"] == report.guard.max_lab_edges


def test_core_cross_package_import_guard_has_no_failures() -> None:
    assert validate_core_cross_package_imports() == ()
