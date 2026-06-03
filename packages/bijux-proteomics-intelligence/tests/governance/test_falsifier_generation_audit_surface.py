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


def test_falsifier_band_keeps_claim_surface_specificity_explicit() -> None:
    falsifier_band = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_CAPABILITY_MAP
        if entry.band is IntelligenceAnalyticalBand.FALSIFIERS
    )

    assert falsifier_band.required_modules == ("falsifiers.py",)
    assert any(
        "protein, PTM, pathway, regulator, and biomarker" in scope
        for scope in falsifier_band.refusal_scope
    )


def test_falsifier_module_audit_points_to_live_owner_module() -> None:
    falsifier_entry = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_MODULE_AUDIT
        if entry.module_path == "falsifiers.py"
    )

    assert (
        falsifier_entry.classification
        is IntelligenceModuleClassification.ANALYTICAL_VALUE
    )
    assert falsifier_entry.anchor_capabilities == (
        IntelligenceCharterCapability.REVIEW_REASONING,
        IntelligenceCharterCapability.RECOMMENDATION,
    )
    assert (INTELLIGENCE_SRC_ROOT / "falsifiers.py").exists()
