from __future__ import annotations

from bijux_proteomics_dev.api.core.compatibility_exports import (
    CORE_COMPATIBILITY_EXPORTS_PATH,
    build_core_compatibility_export_report,
    run,
    validate_core_compatibility_exports,
)


def test_core_compatibility_export_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_core_compatibility_export_report_tracks_remaining_wrappers() -> None:
    report = build_core_compatibility_export_report()

    assert CORE_COMPATIBILITY_EXPORTS_PATH.exists()
    assert report.entries == ()
    assert report.guard.max_compatibility_exports == 0
    assert report.guard.require_root_level_only is True


def test_core_compatibility_export_guard_has_no_failures() -> None:
    assert validate_core_compatibility_exports() == ()
