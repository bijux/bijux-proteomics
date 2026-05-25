# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.governance.charter import (
    DEFAULT_INTELLIGENCE_CAPABILITY_MAP,
    DEFAULT_INTELLIGENCE_CHARTER,
    DEFAULT_INTELLIGENCE_CHARTER_ENTRIES,
    DEFAULT_INTELLIGENCE_MODULE_AUDIT,
    IntelligenceAnalyticalBand,
    IntelligenceCharterCapability,
    IntelligenceModuleClassification,
    list_intelligence_analytical_bands,
    list_intelligence_capabilities,
    list_intelligence_capability_map,
    list_intelligence_charter_entries,
)


def test_intelligence_charter_exposes_exact_capabilities() -> None:
    assert list_intelligence_capabilities() == (
        IntelligenceCharterCapability.PRIORITIZATION,
        IntelligenceCharterCapability.CONTRADICTION_HANDLING,
        IntelligenceCharterCapability.REVIEW_REASONING,
        IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,
        IntelligenceCharterCapability.RECOMMENDATION,
    )


def test_intelligence_charter_keeps_non_owned_surfaces_explicit() -> None:
    assert DEFAULT_INTELLIGENCE_CHARTER.package_name == (
        "bijux-proteomics-intelligence"
    )
    assert "runtime execution and artifact transport" in (
        DEFAULT_INTELLIGENCE_CHARTER.excluded_ownership
    )
    assert "knowledge-owned evidence bundles and references" in (
        DEFAULT_INTELLIGENCE_CHARTER.required_inputs
    )


def test_intelligence_charter_entries_stay_release_blocking_and_module_backed() -> None:
    assert list_intelligence_charter_entries() == DEFAULT_INTELLIGENCE_CHARTER_ENTRIES
    assert {entry.capability for entry in DEFAULT_INTELLIGENCE_CHARTER_ENTRIES} == set(
        DEFAULT_INTELLIGENCE_CHARTER.capabilities
    )
    assert all(entry.required_modules for entry in DEFAULT_INTELLIGENCE_CHARTER_ENTRIES)
    assert all(entry.release_blocker for entry in DEFAULT_INTELLIGENCE_CHARTER_ENTRIES)


def test_intelligence_capability_map_keeps_stable_analytical_bands() -> None:
    assert list_intelligence_analytical_bands() == (
        IntelligenceAnalyticalBand.CANDIDATES,
        IntelligenceAnalyticalBand.CLAIMS,
        IntelligenceAnalyticalBand.CONTRADICTIONS,
        IntelligenceAnalyticalBand.FALSIFIERS,
        IntelligenceAnalyticalBand.REFUSAL,
        IntelligenceAnalyticalBand.QUERY,
        IntelligenceAnalyticalBand.JUDGMENT,
        IntelligenceAnalyticalBand.POSTURE,
        IntelligenceAnalyticalBand.INTERPRETATION,
        IntelligenceAnalyticalBand.REVIEWS,
        IntelligenceAnalyticalBand.LEARNING,
    )
    assert list_intelligence_capability_map() == DEFAULT_INTELLIGENCE_CAPABILITY_MAP
    assert all(entry.required_modules for entry in DEFAULT_INTELLIGENCE_CAPABILITY_MAP)
    assert all(entry.decision_scope for entry in DEFAULT_INTELLIGENCE_CAPABILITY_MAP)
    assert all(entry.refusal_scope for entry in DEFAULT_INTELLIGENCE_CAPABILITY_MAP)


def test_intelligence_module_audit_requires_substantial_analytical_surface() -> None:
    analytical_modules = [
        entry
        for entry in DEFAULT_INTELLIGENCE_MODULE_AUDIT
        if entry.classification is IntelligenceModuleClassification.ANALYTICAL_VALUE
    ]
    thin_modules = [
        entry
        for entry in DEFAULT_INTELLIGENCE_MODULE_AUDIT
        if entry.classification is IntelligenceModuleClassification.THIN_ABSTRACTION
    ]

    assert len(analytical_modules) >= 12
    assert len(thin_modules) <= 2
