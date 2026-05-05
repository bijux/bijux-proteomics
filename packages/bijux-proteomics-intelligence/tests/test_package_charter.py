# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence import (
    DEFAULT_INTELLIGENCE_CHARTER,
    IntelligenceCharterCapability,
    list_intelligence_capabilities,
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
