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


def test_refusal_band_keeps_claim_blocking_scope_explicit() -> None:
    refusal_band = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_CAPABILITY_MAP
        if entry.band is IntelligenceAnalyticalBand.REFUSAL
    )

    assert refusal_band.required_modules == ("refusal.py",)
    assert any(
        "design validity" in scope or "peptide support" in scope
        for scope in refusal_band.decision_scope + refusal_band.refusal_scope
    )


def test_refusal_module_audit_points_to_live_owner_module() -> None:
    refusal_entry = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_MODULE_AUDIT
        if entry.module_path == "refusal.py"
    )

    assert refusal_entry.classification is IntelligenceModuleClassification.ANALYTICAL_VALUE
    assert refusal_entry.anchor_capabilities == (
        IntelligenceCharterCapability.CONTRADICTION_HANDLING,
        IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,
    )
    assert (INTELLIGENCE_SRC_ROOT / "refusal.py").exists()
