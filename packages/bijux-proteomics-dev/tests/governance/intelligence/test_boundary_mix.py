from __future__ import annotations

from bijux_proteomics_dev.governance.intelligence.boundary_mix import (
    INTELLIGENCE_BOUNDARY_MIX_PATH,
    build_intelligence_boundary_mix_report,
    run,
    validate_intelligence_boundary_mix,
)


def test_intelligence_boundary_mix_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_intelligence_boundary_mix_report_tracks_governed_hotspots() -> None:
    report = build_intelligence_boundary_mix_report()
    metrics = report.metrics
    guard = report.guard

    assert INTELLIGENCE_BOUNDARY_MIX_PATH.exists()
    assert metrics.scanned_module_count == 33
    assert metrics.hotspot_count == guard.baseline_hotspot_count
    assert metrics.max_touched_band_count == guard.baseline_max_touched_band_count
    assert guard.baseline_hotspot_modules == (
        "belief_audit.py",
        "candidates/ranking.py",
        "judgment/paths.py",
        "reviews/decision_briefs.py",
    )


def test_intelligence_boundary_mix_release_guard_has_no_failures() -> None:
    assert validate_intelligence_boundary_mix() == ()
