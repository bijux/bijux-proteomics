from __future__ import annotations

from pathlib import Path

from bijux_proteomics_intelligence.governance.charter import (
    DEFAULT_INTELLIGENCE_CAPABILITY_MAP,
    DEFAULT_INTELLIGENCE_MODULE_AUDIT,
    IntelligenceAnalyticalBand,
    IntelligenceCharterCapability,
    IntelligenceModuleClassification,
)

INTELLIGENCE_SRC_ROOT = Path(
    "packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence"
)


def test_query_band_keeps_id_backed_answer_scope_explicit() -> None:
    query_band = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_CAPABILITY_MAP
        if entry.band is IntelligenceAnalyticalBand.QUERY
    )

    assert query_band.required_modules == ("query.py",)
    assert any("referenced IDs" in scope or "explicit IDs" in scope for scope in query_band.decision_scope + query_band.refusal_scope)


def test_query_module_audit_points_to_live_owner_module() -> None:
    query_entry = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_MODULE_AUDIT
        if entry.module_path == "query.py"
    )

    assert query_entry.classification is IntelligenceModuleClassification.ANALYTICAL_VALUE
    assert query_entry.anchor_capabilities == (
        IntelligenceCharterCapability.REVIEW_REASONING,
        IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,
    )
    assert (INTELLIGENCE_SRC_ROOT / "query.py").exists()
