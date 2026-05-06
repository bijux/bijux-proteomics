# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics_knowledge.memory.models.claims import ClaimStatus, build_claim
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStrength,
)


@pytest.fixture
def supported_progression_bundle() -> EvidenceBundle:
    """Representative review input owned by the review family."""

    return EvidenceBundle(
        bundle_id="bundle-review",
        target_id="target-review",
        records=[
            EvidenceRecord(
                evidence_id="review-1",
                kind=EvidenceKind.ASSAY,
                title="assay support",
                source="lab",
                claim="Candidate meets progression gate.",
                decision_tags=["progression"],
                confidence=0.82,
                strength=EvidenceStrength.SUPPORTING,
                endpoint="activity_ratio",
            )
        ],
    )


@pytest.fixture
def supported_progression_claims() -> list[object]:
    """Review-ready supported claim list for the shared progression case."""

    return [
        build_claim(
            claim_id="claim-review-1",
            target_id="target-review",
            statement="Candidate can progress.",
            evidence_ids=["review-1"],
            status=ClaimStatus.SUPPORTED,
            resolution_assays=["orthogonal assay"],
        )
    ]


@pytest.fixture
def contradictory_progression_bundle() -> EvidenceBundle:
    """Representative review input with explicit contradiction signals."""

    return EvidenceBundle(
        bundle_id="bundle-graph-explain",
        target_id="target-graph-explain",
        records=[
            EvidenceRecord(
                evidence_id="ev-support",
                kind=EvidenceKind.ASSAY,
                title="supportive assay",
                source="lab",
                claim="candidate supports progression",
                decision_tags=["progression"],
                confidence=0.84,
                strength=EvidenceStrength.DECISIVE,
                endpoint="activity_ratio",
            ),
            EvidenceRecord(
                evidence_id="ev-contradict",
                kind=EvidenceKind.STRUCTURE,
                title="structure caution",
                source="model",
                claim="candidate may miss progression",
                decision_tags=["progression"],
                confidence=0.66,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )


@pytest.fixture
def contradictory_progression_claims() -> list[object]:
    """Supported claims with tracked contradiction evidence for review outputs."""

    return [
        build_claim(
            claim_id="claim-support",
            target_id="target-graph-explain",
            statement="candidate can progress",
            evidence_ids=["ev-support"],
            contradicting_evidence_ids=["ev-contradict"],
            status=ClaimStatus.SUPPORTED,
            resolution_assays=["orthogonal assay"],
        )
    ]
