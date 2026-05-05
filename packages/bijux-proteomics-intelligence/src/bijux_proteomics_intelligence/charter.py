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


class IntelligenceModuleClassification(StrEnum):
    """Allowed audit outcomes for intelligence source modules."""

    ANALYTICAL_VALUE = "analytical_value"
    THIN_ABSTRACTION = "thin_abstraction"
    DUPLICATE_MODEL = "duplicate_model"
    WRONG_PACKAGE_LOGIC = "wrong_package_logic"


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


class IntelligenceCharterEntry(JsonModel):
    """One durable capability owned by the intelligence package."""

    model_config = ConfigDict(extra="forbid")

    capability: IntelligenceCharterCapability
    owned_surface: str = Field(..., min_length=1)
    required_modules: tuple[str, ...] = Field(..., min_length=1)
    release_blocker: str = Field(..., min_length=1)


class IntelligenceModuleAuditEntry(JsonModel):
    """Audit record for one intelligence source module."""

    model_config = ConfigDict(extra="forbid")

    module_path: str = Field(..., min_length=1)
    classification: IntelligenceModuleClassification
    anchor_capabilities: tuple[IntelligenceCharterCapability, ...] = Field(
        default_factory=tuple
    )
    reason: str = Field(..., min_length=1)


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


DEFAULT_INTELLIGENCE_CHARTER_ENTRIES: tuple[IntelligenceCharterEntry, ...] = (
    IntelligenceCharterEntry(
        capability=IntelligenceCharterCapability.PRIORITIZATION,
        owned_surface="Transparent multi-objective ranking that weighs evidence strength, reproducibility, assay feasibility, novelty, and execution burden.",
        required_modules=("briefs.py", "policies.py", "decision_paths.py"),
        release_blocker="Intelligence cannot ship if candidate ordering collapses into opaque scores or policy-only prose.",
    ),
    IntelligenceCharterEntry(
        capability=IntelligenceCharterCapability.CONTRADICTION_HANDLING,
        owned_surface="Explicit contradiction, freshness, and uncertainty posture that can refuse overconfident recommendations.",
        required_modules=("evidence_posture.py", "evaluators.py", "decision_paths.py"),
        release_blocker="Intelligence cannot ship if contradictory or stale evidence still produces confident progression output.",
    ),
    IntelligenceCharterEntry(
        capability=IntelligenceCharterCapability.REVIEW_REASONING,
        owned_surface="Review-board packets and skeptical challenge reports that survive scientific and software scrutiny.",
        required_modules=(
            "evaluators.py",
            "decision_paths.py",
            "skeptical_review.py",
            "benchmark_reviews.py",
        ),
        release_blocker="Intelligence cannot ship if review consumers cannot see why a recommendation should be trusted or challenged.",
    ),
    IntelligenceCharterEntry(
        capability=IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,
        owned_surface="Typed interpretation contracts that separate technical anomalies, biological signal, and pathway-overclaim risks.",
        required_modules=("interpretation.py", "decision_paths.py"),
        release_blocker="Intelligence cannot ship if interpretation helpers blur cautionary caveats into confident scientific claims.",
    ),
    IntelligenceCharterEntry(
        capability=IntelligenceCharterCapability.RECOMMENDATION,
        owned_surface="End-to-end decision paths that add analytical value beyond core workflow models and runtime delivery surfaces.",
        required_modules=("briefs.py", "evaluators.py", "skeptical_review.py"),
        release_blocker="Intelligence cannot ship if downstream packages could recreate its outputs by stitching together core models and runtime wrappers alone.",
    ),
)


DEFAULT_INTELLIGENCE_MODULE_AUDIT: tuple[IntelligenceModuleAuditEntry, ...] = (
    IntelligenceModuleAuditEntry(
        module_path="__init__.py",
        classification=IntelligenceModuleClassification.THIN_ABSTRACTION,
        reason="The package root is an export surface that aggregates stable analytical entrypoints.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="benchmark_reviews.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.REVIEW_REASONING,),
        reason="Benchmark-backed review outputs keep release-facing workflow claims tied to checked-in datasets, owner surfaces, and explicit scientific limits.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="briefs.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.PRIORITIZATION,
            IntelligenceCharterCapability.RECOMMENDATION,
        ),
        reason="Ranking logic and explainability live here instead of being recreated by downstream consumers.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="candidates.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.REVIEW_REASONING,),
        reason="Candidate lifecycle and risk summaries give review outputs analytical substance beyond transport formatting.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="charter.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.PRIORITIZATION,
            IntelligenceCharterCapability.RECOMMENDATION,
        ),
        reason="The machine-readable charter and module audit keep analytical ownership explicit and release-blocking.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="decision_paths.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.REVIEW_REASONING,
            IntelligenceCharterCapability.RECOMMENDATION,
        ),
        reason="Decision paths turn scored evidence into explicit reviewable recommendations with unresolved questions intact.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="evaluators.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.CONTRADICTION_HANDLING,
            IntelligenceCharterCapability.REVIEW_REASONING,
            IntelligenceCharterCapability.RECOMMENDATION,
        ),
        reason="Scenario evaluators and review packets are core analytical behavior, not downstream display glue.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="evidence_posture.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.CONTRADICTION_HANDLING,
            IntelligenceCharterCapability.RECOMMENDATION,
        ),
        reason="Freshness and contradiction posture make recommendation confidence defensible.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="interpretation.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,),
        reason="Typed interpretation discipline keeps technical artifacts and biological claims distinct.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="outcomes.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.PRIORITIZATION,
            IntelligenceCharterCapability.RECOMMENDATION,
        ),
        reason="Structured rejection and follow-through planning keep scoring outcomes reviewable instead of implicit.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="policies.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.PRIORITIZATION,),
        reason="Policy lineage and factor validation make ranking reproducible instead of ad hoc.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="skeptical_review.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.REVIEW_REASONING,
            IntelligenceCharterCapability.RECOMMENDATION,
        ),
        reason="Skeptical review pressure proves recommendation quality against software and scientific objections.",
    ),
)


def list_intelligence_capabilities() -> tuple[IntelligenceCharterCapability, ...]:
    """Return the exact analytical capabilities intelligence is allowed to own."""
    return DEFAULT_INTELLIGENCE_CHARTER.capabilities


def list_intelligence_charter_entries() -> tuple[IntelligenceCharterEntry, ...]:
    """Return the exact capability charter entries intelligence must satisfy."""
    return DEFAULT_INTELLIGENCE_CHARTER_ENTRIES


__all__ = [
    "DEFAULT_INTELLIGENCE_CHARTER",
    "DEFAULT_INTELLIGENCE_CHARTER_ENTRIES",
    "DEFAULT_INTELLIGENCE_MODULE_AUDIT",
    "IntelligenceCharterCapability",
    "IntelligenceCharterEntry",
    "IntelligenceModuleAuditEntry",
    "IntelligenceModuleClassification",
    "IntelligenceProductCharter",
    "list_intelligence_capabilities",
    "list_intelligence_charter_entries",
]
