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


def test_claim_support_band_keeps_graph_validation_scope_explicit() -> None:
    claims_band = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_CAPABILITY_MAP
        if entry.band is IntelligenceAnalyticalBand.CLAIMS
    )

    assert claims_band.required_modules == ("claims/support.py",)
    assert any(
        "evidence-graph support" in scope for scope in claims_band.decision_scope
    )


def test_claim_support_module_audit_points_to_live_owner_module() -> None:
    support_entry = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_MODULE_AUDIT
        if entry.module_path == "claims/support.py"
    )

    assert (
        support_entry.classification
        is IntelligenceModuleClassification.ANALYTICAL_VALUE
    )
    assert support_entry.anchor_capabilities == (
        IntelligenceCharterCapability.CONTRADICTION_HANDLING,
        IntelligenceCharterCapability.REVIEW_REASONING,
    )
    assert (INTELLIGENCE_SRC_ROOT / "claims/support.py").exists()
