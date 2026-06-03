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


def test_belief_audit_band_keeps_top_claim_coverage_explicit() -> None:
    belief_audit_band = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_CAPABILITY_MAP
        if entry.band is IntelligenceAnalyticalBand.BELIEF_AUDIT
    )

    assert belief_audit_band.required_modules == ("belief_audit.py",)
    assert any(
        "top claims" in scope or "every claim" in scope
        for scope in belief_audit_band.decision_scope + belief_audit_band.refusal_scope
    )


def test_belief_audit_module_audit_points_to_live_owner_module() -> None:
    belief_audit_entry = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_MODULE_AUDIT
        if entry.module_path == "belief_audit.py"
    )

    assert (
        belief_audit_entry.classification
        is IntelligenceModuleClassification.ANALYTICAL_VALUE
    )
    assert belief_audit_entry.anchor_capabilities == (
        IntelligenceCharterCapability.CONTRADICTION_HANDLING,
        IntelligenceCharterCapability.REVIEW_REASONING,
    )
    assert (INTELLIGENCE_SRC_ROOT / "belief_audit.py").exists()
