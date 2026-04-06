# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Evidence bundles for scientific review."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import (
    DocumentSchema,
    EvidenceId,
    JsonModel,
    TargetId,
)

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


class EvidenceSourceType(StrEnum):
    """Source categories used for trust weighting."""

    LITERATURE = "literature"
    STRUCTURE_MODEL = "structure_model"
    LAB_ASSAY = "lab_assay"
    CURATED_NOTE = "curated_note"
    EXTERNAL_DATABASE = "external_database"


class EvidenceOrigin(StrEnum):
    """Origin of an evidence record."""

    OBSERVED = "observed"
    INFERRED = "inferred"
    IMPORTED = "imported"
    SYNTHETIC = "synthetic"


class EvidenceExtractionMethod(StrEnum):
    """How the evidence record was produced."""

    MANUAL_CURATION = "manual_curation"
    AUTOMATED_IMPORT = "automated_import"
    MODEL_INFERENCE = "model_inference"
    LAB_CAPTURE = "lab_capture"


class EvidenceRecord(JsonModel):
    """Single evidence statement."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: EvidenceId = Field(..., description="Stable evidence identifier.")
    kind: EvidenceKind = Field(..., description="Evidence family.")
    title: str = Field(..., min_length=1, description="Short title.")
    source: str = Field(..., min_length=1, description="Source location or system.")
    source_type: EvidenceSourceType = Field(
        default=EvidenceSourceType.CURATED_NOTE,
        description="Source category for trust policies.",
    )
    source_uri: str | None = Field(
        default=None,
        description="Stable URI or locator for the source.",
    )
    origin: EvidenceOrigin = Field(
        default=EvidenceOrigin.OBSERVED,
        description="Whether the evidence was observed, inferred, imported, or synthetic.",
    )
    extraction_method: EvidenceExtractionMethod = Field(
        default=EvidenceExtractionMethod.MANUAL_CURATION,
        description="How the evidence record was produced.",
    )
    curator: str | None = Field(
        default=None,
        description="Human or system responsible for producing the record.",
    )
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
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the evidence was produced or observed.",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Optional point after which the evidence should be treated as stale.",
    )


class EvidenceBundle(JsonModel):
    """Set of evidence attached to a program or target."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: EvidenceId = Field(..., description="Stable bundle identifier.")
    target_id: TargetId = Field(..., description="Target identifier.")
    document_schema: DocumentSchema = Field(
        default_factory=lambda: DocumentSchema(created_by="bijux-proteomics-knowledge"),
        description="Schema and provenance metadata.",
    )
    records: list[EvidenceRecord] = Field(
        default_factory=list,
        description="Evidence records in the bundle.",
    )


class EvidenceCoverage(JsonModel):
    """Coverage and strength of the current evidence bundle."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: EvidenceId = Field(..., description="Stable bundle identifier.")
    target_id: TargetId = Field(..., description="Target identifier.")
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

    target_id: TargetId = Field(..., description="Target identifier.")
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


class EvidenceConflict(JsonModel):
    """Two records that appear to disagree about the same decision area."""

    model_config = ConfigDict(extra="forbid")

    left_evidence_id: str = Field(..., min_length=1, description="First evidence identifier.")
    right_evidence_id: str = Field(..., min_length=1, description="Second evidence identifier.")
    reason: str = Field(..., min_length=1, description="Why the pair is considered conflicting.")


class BundleTrustReport(JsonModel):
    """Trust summary for an evidence bundle."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1, description="Stable bundle identifier.")
    target_id: str = Field(..., min_length=1, description="Target identifier.")
    trust_score: float = Field(..., ge=0.0, le=1.0, description="Overall trust score.")
    stale_records: list[str] = Field(
        default_factory=list,
        description="Evidence identifiers that should be refreshed.",
    )
    conflicts: list[EvidenceConflict] = Field(
        default_factory=list,
        description="Detected evidence conflicts.",
    )
    duplicate_groups: list[list[str]] = Field(
        default_factory=list,
        description="Potential duplicate evidence identifiers.",
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


def weight_source_type(source_type: EvidenceSourceType) -> float:
    """Return a trust weight for the source category."""
    return {
        EvidenceSourceType.LAB_ASSAY: 1.0,
        EvidenceSourceType.LITERATURE: 0.9,
        EvidenceSourceType.EXTERNAL_DATABASE: 0.8,
        EvidenceSourceType.STRUCTURE_MODEL: 0.75,
        EvidenceSourceType.CURATED_NOTE: 0.65,
    }[source_type]


def score_evidence_record(
    record: EvidenceRecord,
    *,
    now: datetime | None = None,
) -> float:
    """Compute a trust score for a single evidence record."""
    now = now or datetime.now(UTC)
    strength_weight = {
        EvidenceStrength.EXPLORATORY: 0.5,
        EvidenceStrength.SUPPORTING: 0.8,
        EvidenceStrength.DECISIVE: 1.0,
    }[record.strength]
    stale_penalty = 0.5 if record.expires_at is not None and record.expires_at < now else 1.0
    return round(record.confidence * weight_source_type(record.source_type) * strength_weight * stale_penalty, 4)


def stale_records(
    bundle: EvidenceBundle,
    *,
    now: datetime | None = None,
) -> list[EvidenceRecord]:
    """Return records whose explicit expiry has passed."""
    now = now or datetime.now(UTC)
    return [
        record
        for record in bundle.records
        if record.expires_at is not None and record.expires_at < now
    ]


def deduplicate_records(bundle: EvidenceBundle) -> list[list[str]]:
    """Group records that look like duplicates."""
    grouped: dict[tuple[str, str, str], list[str]] = {}
    for record in bundle.records:
        key = (
            record.kind.value,
            record.claim.strip().lower(),
            record.source.strip().lower(),
        )
        grouped.setdefault(key, []).append(record.evidence_id)
    return [ids for ids in grouped.values() if len(ids) > 1]


def flag_conflicting_evidence(bundle: EvidenceBundle) -> list[EvidenceConflict]:
    """Identify conflicting evidence with opposite decision tags on the same target."""
    conflicts: list[EvidenceConflict] = []
    for index, left in enumerate(bundle.records):
        left_tags = set(left.decision_tags)
        for right in bundle.records[index + 1 :]:
            if left.kind is not right.kind:
                continue
            if not left_tags.intersection(right.decision_tags):
                continue
            if left.claim.strip().lower() == right.claim.strip().lower():
                continue
            if {left.strength, right.strength} == {
                EvidenceStrength.DECISIVE,
                EvidenceStrength.EXPLORATORY,
            }:
                conflicts.append(
                    EvidenceConflict(
                        left_evidence_id=left.evidence_id,
                        right_evidence_id=right.evidence_id,
                        reason="same decision tag but materially different claim strength",
                    )
                )
    return conflicts


def compute_bundle_trust(
    bundle: EvidenceBundle,
    *,
    now: datetime | None = None,
) -> BundleTrustReport:
    """Compute overall trust after staleness, conflicts, and deduplication."""
    now = now or datetime.now(UTC)
    record_scores = [score_evidence_record(record, now=now) for record in bundle.records]
    base_score = sum(record_scores) / len(record_scores) if record_scores else 0.0
    stale = stale_records(bundle, now=now)
    conflicts = flag_conflicting_evidence(bundle)
    duplicate_groups = deduplicate_records(bundle)
    penalty = (0.05 * len(stale)) + (0.1 * len(conflicts)) + (0.03 * len(duplicate_groups))
    return BundleTrustReport(
        bundle_id=bundle.bundle_id,
        target_id=bundle.target_id,
        trust_score=max(0.0, round(base_score - penalty, 4)),
        stale_records=[record.evidence_id for record in stale],
        conflicts=conflicts,
        duplicate_groups=duplicate_groups,
    )
