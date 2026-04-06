# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Repository contracts for evidence and claims."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from pydantic import ConfigDict, Field

from bijux_proteomics_knowledge.claims import ClaimPolarity, ClaimStatus, ClaimType, EvidenceClaim
from bijux_proteomics_knowledge.evidence import EvidenceBundle, EvidenceRecord
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


def query_claims(claims: list[EvidenceClaim], query: ClaimQuery) -> list[EvidenceClaim]:
    """Filter claims for one target using structured query fields."""
    filtered = [claim for claim in claims if claim.target_id == query.target_id]
    if query.status is not None:
        filtered = [claim for claim in filtered if claim.status is query.status]
    if query.claim_type is not None:
        filtered = [claim for claim in filtered if claim.claim_type is query.claim_type]
    if query.polarity is not None:
        filtered = [claim for claim in filtered if claim.polarity is query.polarity]
    return filtered
