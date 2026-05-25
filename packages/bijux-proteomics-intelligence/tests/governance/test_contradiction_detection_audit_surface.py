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


def test_contradiction_band_keeps_ptm_correction_scope_explicit() -> None:
    contradictions_band = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_CAPABILITY_MAP
        if entry.band is IntelligenceAnalyticalBand.CONTRADICTIONS
    )

    assert contradictions_band.required_modules == ("contradictions.py",)
    assert any(
        "protein-steady and PTM-shifted pairs" in scope
        for scope in contradictions_band.decision_scope
    )


def test_contradiction_module_audit_points_to_live_owner_module() -> None:
    detection_entry = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_MODULE_AUDIT
        if entry.module_path == "contradictions.py"
    )

    assert (
        detection_entry.classification
        is IntelligenceModuleClassification.ANALYTICAL_VALUE
    )
    assert detection_entry.anchor_capabilities == (
        IntelligenceCharterCapability.CONTRADICTION_HANDLING,
        IntelligenceCharterCapability.REVIEW_REASONING,
    )
    assert (INTELLIGENCE_SRC_ROOT / "contradictions.py").exists()
