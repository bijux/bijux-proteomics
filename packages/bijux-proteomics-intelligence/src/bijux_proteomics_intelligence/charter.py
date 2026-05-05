# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Machine-readable charter for intelligence-owned analytical behavior."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class IntelligenceCharterCapability(StrEnum):
    """Capabilities intelligence must own as a real analytical product."""

    PRIORITIZATION = "prioritization"
    CONTRADICTION_HANDLING = "contradiction_handling"
    REVIEW_REASONING = "review_reasoning"
    INTERPRETATION_DISCIPLINE = "interpretation_discipline"
    RECOMMENDATION = "recommendation"


class IntelligenceProductCharter(JsonModel):
    """Durable product charter for intelligence package ownership."""

    model_config = ConfigDict(extra="forbid")

    package_name: str = Field(..., min_length=1)
    value_statement: str = Field(..., min_length=1)
    capabilities: tuple[IntelligenceCharterCapability, ...] = Field(
        default_factory=tuple
    )
    required_inputs: tuple[str, ...] = Field(default_factory=tuple)
    excluded_ownership: tuple[str, ...] = Field(default_factory=tuple)


DEFAULT_INTELLIGENCE_CHARTER = IntelligenceProductCharter(
    package_name="bijux-proteomics-intelligence",
    value_statement=(
        "turn ranked evidence, contradiction posture, and workflow interpretation into "
        "explicit analytical judgment without taking over scientific truth, runtime "
        "execution, knowledge curation, or lab scheduling"
    ),
    capabilities=(
        IntelligenceCharterCapability.PRIORITIZATION,
        IntelligenceCharterCapability.CONTRADICTION_HANDLING,
        IntelligenceCharterCapability.REVIEW_REASONING,
        IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,
        IntelligenceCharterCapability.RECOMMENDATION,
    ),
    required_inputs=(
        "core-owned scientific models",
        "knowledge-owned evidence bundles and references",
        "lab-owned assay feasibility and operational constraints",
    ),
    excluded_ownership=(
        "scientific parsing and normalization",
        "runtime execution and artifact transport",
        "knowledge curation and reference registry maintenance",
        "lab queueing and operational handoff authority",
    ),
)


def list_intelligence_capabilities() -> tuple[IntelligenceCharterCapability, ...]:
    """Return the exact analytical capabilities intelligence is allowed to own."""
    return DEFAULT_INTELLIGENCE_CHARTER.capabilities


__all__ = [
    "DEFAULT_INTELLIGENCE_CHARTER",
    "IntelligenceCharterCapability",
    "IntelligenceProductCharter",
    "list_intelligence_capabilities",
]
