from __future__ import annotations

from bijux_proteomics_dev.api.intelligence_capability_map import (
    INTELLIGENCE_CAPABILITY_MAP_PATH,
    build_intelligence_capability_map_report,
    run,
    validate_intelligence_capability_map,
)
from bijux_proteomics_intelligence.governance.charter import (
    IntelligenceAnalyticalBand,
    list_intelligence_analytical_bands,
    list_intelligence_capability_map,
)


def test_intelligence_capability_map_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_intelligence_capability_map_keeps_five_stable_analytical_bands() -> None:
    report = build_intelligence_capability_map_report()
    metrics = report.metrics
    guard = report.guard

    assert INTELLIGENCE_CAPABILITY_MAP_PATH.exists()
    assert list_intelligence_analytical_bands() == (
        IntelligenceAnalyticalBand.JUDGMENT,
        IntelligenceAnalyticalBand.EVIDENCE_POSTURE,
        IntelligenceAnalyticalBand.INTERPRETATION,
        IntelligenceAnalyticalBand.REVIEW,
        IntelligenceAnalyticalBand.LEARNING,
    )
    assert metrics.analytical_band_count == guard.baseline_analytical_band_count
    assert metrics.analytical_band_count == 5
    assert metrics.owned_surface_count == 5
    assert metrics.required_module_count == 14
    assert metrics.decision_scope_count == 11
    assert metrics.refusal_scope_count == 10
    assert len(list_intelligence_capability_map()) == metrics.owned_surface_count


def test_intelligence_capability_map_release_guard_has_no_failures() -> None:
    assert validate_intelligence_capability_map() == ()
