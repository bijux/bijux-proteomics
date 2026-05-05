from __future__ import annotations

from bijux_proteomics_dev.api.core_compatibility_exports import (
    CORE_COMPATIBILITY_EXPORTS_PATH,
    build_core_compatibility_export_report,
    run,
    validate_core_compatibility_exports,
)


def test_core_compatibility_export_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_core_compatibility_export_report_tracks_remaining_wrappers() -> None:
    report = build_core_compatibility_export_report()
    entry_by_module = {entry.module_path: entry for entry in report.entries}

    assert CORE_COMPATIBILITY_EXPORTS_PATH.exists()
    assert [entry.module_path for entry in report.entries] == [
        "liabilities.py",
        "search_adapters.py",
        "workflow_blueprint.py",
    ]
    assert report.guard.max_compatibility_exports == 3
    assert report.guard.require_root_level_only is True
    assert entry_by_module["liabilities.py"].source_consumer_modules == ()
    assert entry_by_module["liabilities.py"].test_consumer_modules != ()
    assert entry_by_module["search_adapters.py"].source_consumer_distributions == (
        "bijux-proteomics-runtime",
    )
    assert entry_by_module["workflow_blueprint.py"].source_consumer_modules == ()


def test_core_compatibility_export_guard_has_no_failures() -> None:
    assert validate_core_compatibility_exports() == ()
