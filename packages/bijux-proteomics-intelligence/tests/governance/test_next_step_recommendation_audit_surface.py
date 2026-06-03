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


def test_next_steps_band_keeps_triggered_follow_up_scope_explicit() -> None:
    next_steps_band = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_CAPABILITY_MAP
        if entry.band is IntelligenceAnalyticalBand.NEXT_STEPS
    )

    assert next_steps_band.required_modules == ("next_steps.py",)
    assert any(
        "triggering result row" in scope or "specific weakness or opportunity" in scope
        for scope in next_steps_band.decision_scope + next_steps_band.refusal_scope
    )


def test_next_steps_module_audit_points_to_live_owner_module() -> None:
    next_steps_entry = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_MODULE_AUDIT
        if entry.module_path == "next_steps.py"
    )

    assert (
        next_steps_entry.classification
        is IntelligenceModuleClassification.ANALYTICAL_VALUE
    )
    assert next_steps_entry.anchor_capabilities == (
        IntelligenceCharterCapability.REVIEW_REASONING,
        IntelligenceCharterCapability.RECOMMENDATION,
    )
    assert (INTELLIGENCE_SRC_ROOT / "next_steps.py").exists()
