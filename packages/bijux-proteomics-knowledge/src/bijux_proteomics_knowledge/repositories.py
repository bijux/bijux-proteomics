# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Repository contracts for evidence and claims."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from pydantic import ConfigDict, Field

from bijux_proteomics_knowledge.claims import (
    ClaimPolarity,
    ClaimResolutionState,
    ClaimStatus,
    ClaimType,
    EvidenceClaim,
)
from bijux_proteomics_knowledge.evidence import EvidenceBundle, EvidenceKind, EvidenceRecord, EvidenceSourceType
from bijux_proteomics_knowledge.resolution import ConflictResolution
from bijux_proteomics_knowledge.serialization import JsonModel


class EvidenceBundleRepository(Protocol):
    """Persistence contract for evidence bundles."""

    def save_bundle(self, bundle: EvidenceBundle) -> None:
        """Persist an evidence bundle."""

    def load_bundle(self, bundle_id: str) -> EvidenceBundle:
        """Load an evidence bundle by identifier."""

    def list_target_bundles(self, target_id: str) -> list[EvidenceBundle]:
        """List bundles associated with a target."""


class EvidenceRecordRepository(Protocol):
    """Persistence contract for individual evidence records."""

    def save_record(self, record: EvidenceRecord) -> None:
        """Persist one evidence record."""

    def list_target_records(self, target_id: str) -> list[EvidenceRecord]:
        """List evidence records associated with a target."""


class EvidenceClaimRepository(Protocol):
    """Persistence contract for claim documents."""

    def save_claim(self, claim: EvidenceClaim) -> None:
        """Persist an evidence-backed claim."""

    def list_target_claims(self, target_id: str) -> list[EvidenceClaim]:
        """List claims associated with a target."""


class ClaimResolutionRecord(JsonModel):
    """Persisted conflict-resolution outcome for claim support decisions."""

    model_config = ConfigDict(extra="forbid")

    record_id: str = Field(..., min_length=1, description="Stable resolution record id.")
    target_id: str = Field(..., min_length=1, description="Target identifier.")
    decision_tag: str = Field(..., min_length=1, description="Decision dimension affected.")
    resolution: ConflictResolution = Field(
        ...,
        description="Resolution applied for a conflicting evidence pair.",
    )
    recorded_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the resolution was recorded.",
    )
    recorded_by: str = Field(..., min_length=1, description="Actor recording the resolution.")


class ClaimResolutionRepository(Protocol):
    """Persistence contract for claim resolution history."""

    def save_resolution_record(self, record: ClaimResolutionRecord) -> None:
        """Persist one claim resolution record."""

    def list_target_resolution_records(self, target_id: str) -> list[ClaimResolutionRecord]:
        """List resolution history records for a target."""


class ClaimQuery(JsonModel):
    """Structured query for filtering target claims."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1, description="Target identifier.")
    status: ClaimStatus | None = Field(default=None, description="Optional status filter.")
    claim_type: ClaimType | None = Field(default=None, description="Optional claim-type filter.")
    polarity: ClaimPolarity | None = Field(default=None, description="Optional polarity filter.")
    resolution_state: ClaimResolutionState | None = Field(default=None, description="Optional resolution-state filter.")
    minimum_confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Optional confidence floor.")
    decision_impact: str | None = Field(default=None, description="Optional decision-impact filter.")
    contradiction_group: str | None = Field(default=None, description="Optional contradiction-group filter.")


class ResolutionRecordQuery(JsonModel):
    """Structured query for filtering resolution history records."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1, description="Target identifier.")
    decision_tag: str | None = Field(default=None, description="Optional decision-tag filter.")
    recorded_by: str | None = Field(default=None, description="Optional actor filter.")
    recorded_after: datetime | None = Field(default=None, description="Optional inclusive lower bound for record time.")


class EvidenceRecordQuery(JsonModel):
    """Structured query for filtering evidence records."""

    model_config = ConfigDict(extra="forbid")

    decision_tag: str | None = Field(default=None, description="Optional decision-tag filter.")
    kind: EvidenceKind | None = Field(default=None, description="Optional evidence kind filter.")
    source_type: EvidenceSourceType | None = Field(default=None, description="Optional source type filter.")
    minimum_confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Optional confidence floor.")
    observed_after: datetime | None = Field(default=None, description="Optional inclusive lower bound for observed_at.")
    sort_by: str | None = Field(default=None, description="Optional sort key: confidence or observed_at.")
    descending: bool = Field(default=True, description="Whether sorting should be descending.")


def query_claims(claims: list[EvidenceClaim], query: ClaimQuery) -> list[EvidenceClaim]:
    """Filter claims for one target using structured query fields."""
    filtered = [claim for claim in claims if claim.target_id == query.target_id]
    if query.status is not None:
        filtered = [claim for claim in filtered if claim.status is query.status]
    if query.claim_type is not None:
        filtered = [claim for claim in filtered if claim.claim_type is query.claim_type]
    if query.polarity is not None:
        filtered = [claim for claim in filtered if claim.polarity is query.polarity]
    if query.resolution_state is not None:
        filtered = [claim for claim in filtered if claim.resolution_state is query.resolution_state]
    if query.minimum_confidence is not None:
        filtered = [claim for claim in filtered if claim.confidence >= query.minimum_confidence]
    if query.decision_impact is not None:
        filtered = [claim for claim in filtered if claim.decision_impact == query.decision_impact]
    if query.contradiction_group is not None:
        filtered = [claim for claim in filtered if claim.contradiction_group == query.contradiction_group]
    return filtered


def query_resolution_records(
    records: list[ClaimResolutionRecord],
    query: ResolutionRecordQuery,
) -> list[ClaimResolutionRecord]:
    """Filter resolution records using structured query fields."""
    filtered = [record for record in records if record.target_id == query.target_id]
    if query.decision_tag is not None:
        filtered = [record for record in filtered if record.decision_tag == query.decision_tag]
    if query.recorded_by is not None:
        filtered = [record for record in filtered if record.recorded_by == query.recorded_by]
    if query.recorded_after is not None:
        filtered = [record for record in filtered if record.recorded_at >= query.recorded_after]
    return filtered


def query_evidence_records(
    records: list[EvidenceRecord],
    query: EvidenceRecordQuery,
) -> list[EvidenceRecord]:
    """Filter evidence records using structured fields."""
    filtered = list(records)
    if query.decision_tag is not None:
        filtered = [record for record in filtered if query.decision_tag in record.decision_tags]
    if query.kind is not None:
        filtered = [record for record in filtered if record.kind is query.kind]
    if query.source_type is not None:
        filtered = [record for record in filtered if record.source_type is query.source_type]
    if query.minimum_confidence is not None:
        filtered = [record for record in filtered if record.confidence >= query.minimum_confidence]
    if query.observed_after is not None:
        filtered = [record for record in filtered if record.observed_at >= query.observed_after]
    if query.sort_by == "confidence":
        filtered = sorted(filtered, key=lambda record: record.confidence, reverse=query.descending)
    elif query.sort_by == "observed_at":
        filtered = sorted(filtered, key=lambda record: record.observed_at, reverse=query.descending)
    return filtered
