from __future__ import annotations

from bijux_proteomics_dev.governance.intelligence.capability_map import (
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


def test_intelligence_capability_map_keeps_governed_analytical_families() -> None:
    report = build_intelligence_capability_map_report()
    metrics = report.metrics
    guard = report.guard

    assert INTELLIGENCE_CAPABILITY_MAP_PATH.exists()
    assert list_intelligence_analytical_bands() == (
        IntelligenceAnalyticalBand.BELIEF_AUDIT,
        IntelligenceAnalyticalBand.CANDIDATES,
        IntelligenceAnalyticalBand.CLAIMS,
        IntelligenceAnalyticalBand.CONTRADICTIONS,
        IntelligenceAnalyticalBand.FALSIFIERS,
        IntelligenceAnalyticalBand.REFUSAL,
        IntelligenceAnalyticalBand.NEXT_STEPS,
        IntelligenceAnalyticalBand.QUERY,
        IntelligenceAnalyticalBand.JUDGMENT,
        IntelligenceAnalyticalBand.POSTURE,
        IntelligenceAnalyticalBand.INTERPRETATION,
        IntelligenceAnalyticalBand.REVIEWS,
        IntelligenceAnalyticalBand.LEARNING,
    )
    assert metrics.analytical_band_count == guard.baseline_analytical_band_count
    assert metrics.analytical_band_count == 13
    assert metrics.owned_surface_count == 13
    assert metrics.required_module_count == 31
    assert metrics.decision_scope_count == 28
    assert metrics.refusal_scope_count == 26
    assert len(list_intelligence_capability_map()) == metrics.owned_surface_count


def test_intelligence_capability_map_release_guard_has_no_failures() -> None:
    assert validate_intelligence_capability_map() == ()
