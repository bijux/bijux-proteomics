# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics_knowledge.reviews.workflow_packets import (
    WorkflowClaimTier,
    build_canonical_evidence_review_packet,
)


def test_build_canonical_evidence_review_packet_preserves_claim_tier_and_artifact_path() -> (
    None
):
    packet = build_canonical_evidence_review_packet(
        workflow_id="flagship-a",
        artifact_path="artifacts/workflows/canonical-reviewable-proteomics/knowledge/review_packet.json",
        evidence_pointers=("knowledge.review_packet", "knowledge.contradictions"),
        accepted_claim_count=3,
        contested_claim_count=1,
    )

    assert packet.claim_tier is WorkflowClaimTier.RUNTIME_PROVEN_WORKFLOW
    assert packet.review_complete is True
    assert packet.artifact_path.startswith("artifacts/")
    assert "repository claim taxonomy" in packet.note


def test_build_canonical_evidence_review_packet_rejects_non_artifact_paths() -> None:
    with pytest.raises(ValueError, match="artifact_path"):
        build_canonical_evidence_review_packet(
            workflow_id="flagship-a",
            artifact_path="/tmp/review_packet.json",
            evidence_pointers=("knowledge.review_packet",),
            accepted_claim_count=1,
            contested_claim_count=0,
            claim_tier=WorkflowClaimTier.OWNED_CONTRACT,
        )
