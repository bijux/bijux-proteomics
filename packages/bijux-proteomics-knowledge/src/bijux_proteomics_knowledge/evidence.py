# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Evidence bundles for scientific review."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_knowledge.schema import SchemaMetadata
from bijux_proteomics_knowledge.serialization import JsonModel

class EvidenceKind(StrEnum):
    """Evidence families tracked by the platform."""

    LITERATURE = "literature"
    STRUCTURE = "structure"
    ASSAY = "assay"
    PATHWAY = "pathway"
    SAFETY = "safety"


class EvidenceStrength(StrEnum):
    """How strongly an evidence record supports a claim."""

    EXPLORATORY = "exploratory"
    SUPPORTING = "supporting"
    DECISIVE = "decisive"


class EvidenceRecord(JsonModel):
    """Single evidence statement."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(
        ...,
        min_length=1,
        description="Stable evidence identifier.",
    )
    kind: EvidenceKind = Field(..., description="Evidence family.")
    title: str = Field(..., min_length=1, description="Short title.")
    source: str = Field(..., min_length=1, description="Source location or system.")
    claim: str = Field(..., min_length=1, description="Human-readable claim.")
    related_targets: list[str] = Field(
        default_factory=list,
        description="Related target identifiers.",
    )
    decision_tags: list[str] = Field(
        default_factory=list,
        description="Decision dimensions informed by the record.",
    )
    derived_from: list[str] = Field(
        default_factory=list,
        description="Upstream evidence identifiers or source records.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the record.",
    )
    strength: EvidenceStrength = Field(..., description="Support level.")


class EvidenceBundle(JsonModel):
    """Set of evidence attached to a program or target."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1, description="Stable bundle identifier.")
    target_id: str = Field(..., min_length=1, description="Target identifier.")
    document_schema: SchemaMetadata = Field(
        default_factory=SchemaMetadata,
        description="Schema and provenance metadata.",
    )
    records: list[EvidenceRecord] = Field(
        default_factory=list,
        description="Evidence records in the bundle.",
    )


class EvidenceCoverage(JsonModel):
    """Coverage and strength of the current evidence bundle."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1, description="Stable bundle identifier.")
    target_id: str = Field(..., min_length=1, description="Target identifier.")
    by_kind: dict[str, int] = Field(
        default_factory=dict,
        description="Count of records grouped by evidence kind.",
    )
    missing_kinds: list[str] = Field(
        default_factory=list,
        description="Required kinds that are still missing.",
    )
    decisive_records: int = Field(
        default=0,
        ge=0,
        description="Number of decisive records in the bundle.",
    )
    mean_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Average confidence across records.",
    )


class DecisionReadiness(JsonModel):
    """Whether the current evidence is strong enough for a program decision."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1, description="Target identifier.")
    ready: bool = Field(..., description="Whether the bundle is decision-ready.")
    blockers: list[str] = Field(
        default_factory=list,
        description="Specific reasons a decision should not proceed yet.",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Concrete actions to improve readiness.",
    )
    coverage: EvidenceCoverage = Field(
        ...,
        description="Coverage report used for the readiness call.",
    )


def summarize_bundle(bundle: EvidenceBundle) -> dict[str, object]:
    """Build a compact evidence summary."""
    by_kind = {kind.value: 0 for kind in EvidenceKind}
    decisive = 0
    for record in bundle.records:
        by_kind[record.kind.value] += 1
        if record.strength is EvidenceStrength.DECISIVE:
            decisive += 1
    return {
        "bundle_id": bundle.bundle_id,
        "target_id": bundle.target_id,
        "schema_version": bundle.document_schema.schema_version,
        "record_count": len(bundle.records),
        "decisive_records": decisive,
        "by_kind": by_kind,
    }


def evidence_gaps(bundle: EvidenceBundle, required_kinds: list[str]) -> list[str]:
    """Return required evidence kinds that are still missing."""
    present = {record.kind.value for record in bundle.records}
    return [kind for kind in required_kinds if kind not in present]


def coverage_report(
    bundle: EvidenceBundle,
    required_kinds: list[str],
) -> EvidenceCoverage:
    """Summarize required coverage for a decision."""
    summary = summarize_bundle(bundle)
    record_count = len(bundle.records)
    mean_confidence = (
        sum(record.confidence for record in bundle.records) / record_count
        if record_count
        else 0.0
    )
    return EvidenceCoverage(
        bundle_id=bundle.bundle_id,
        target_id=bundle.target_id,
        by_kind=summary["by_kind"],
        missing_kinds=evidence_gaps(bundle, required_kinds),
        decisive_records=summary["decisive_records"],
        mean_confidence=round(mean_confidence, 4),
    )


def assess_decision_readiness(
    bundle: EvidenceBundle,
    required_kinds: list[str],
    *,
    minimum_mean_confidence: float = 0.7,
    minimum_decisive_records: int = 1,
) -> DecisionReadiness:
    """Assess whether a bundle is strong enough for a gated decision."""
    coverage = coverage_report(bundle, required_kinds)
    blockers: list[str] = []
    recommendations: list[str] = []

    if coverage.missing_kinds:
        blockers.append(
            "missing required evidence kinds: " + ", ".join(coverage.missing_kinds)
        )
        recommendations.append(
            "collect " + ", ".join(coverage.missing_kinds) + " evidence before signoff"
        )
    if coverage.decisive_records < minimum_decisive_records:
        blockers.append("not enough decisive evidence for an irreversible decision")
        recommendations.append("add decisive assay or structural evidence")
    if coverage.mean_confidence < minimum_mean_confidence:
        blockers.append(
            f"mean confidence {coverage.mean_confidence:.2f} is below "
            f"{minimum_mean_confidence:.2f}"
        )
        recommendations.append("replace exploratory evidence with stronger corroboration")

    return DecisionReadiness(
        target_id=bundle.target_id,
        ready=not blockers,
        blockers=blockers,
        recommendations=recommendations,
        coverage=coverage,
    )
