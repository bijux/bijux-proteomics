from __future__ import annotations

from bijux_proteomics_intelligence.governance.charter import (
    DEFAULT_INTELLIGENCE_CAPABILITY_MAP,
    DEFAULT_INTELLIGENCE_CHARTER_ENTRIES,
    IntelligenceAnalyticalBand,
    IntelligenceCharterCapability,
)


def test_benchmark_review_charter_entry_stays_release_blocking() -> None:
    review_entry = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_CHARTER_ENTRIES
        if entry.capability is IntelligenceCharterCapability.REVIEW_REASONING
    )

    assert "reviews/benchmarks.py" in review_entry.required_modules
    assert "trusted or challenged" in review_entry.release_blocker


def test_benchmark_review_band_keeps_release_scope_explicit() -> None:
    review_band = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_CAPABILITY_MAP
        if entry.band is IntelligenceAnalyticalBand.REVIEWS
    )

    assert "reviews/benchmarks.py" in review_band.required_modules
    assert any("benchmark-backed" in refusal for refusal in review_band.refusal_scope)
