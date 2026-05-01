# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review_iteration09 import (
    ReviewPacketDecisionEntry,
    ReviewPacketEvidenceEntry,
    ReviewerChallengeEntry,
    build_review_packet_schema,
    run_reviewer_challenge_workflow,
)


def test_run_reviewer_challenge_workflow_flags_missing_evidence_pointers() -> None:
    packet = build_review_packet_schema(
        packet_id="packet-1",
        run_id="run-10",
        evidence=(
            ReviewPacketEvidenceEntry(
                evidence_id="E1",
                claim="claim",
                source="study",
                trust_score=0.8,
            ),
        ),
        trust_scores={"cand-1": 0.8},
        contradictions=(),
        qc_caveats=(),
        assay_plans=(),
        risks=(),
        decisions=(
            ReviewPacketDecisionEntry(
                decision_id="d-1",
                candidate_id="cand-1",
                decision_state="accepted",
                rationale="evidence is sufficient",
                evidence_ids=("E1",),
            ),
        ),
    )

    report = run_reviewer_challenge_workflow(
        packet,
        (
            ReviewerChallengeEntry(
                challenge_id="c-1",
                reviewer_id="r-1",
                candidate_id="cand-1",
                challenge_surface="trust",
                reason="weight seems high",
                evidence_ids=("E1",),
            ),
            ReviewerChallengeEntry(
                challenge_id="c-2",
                reviewer_id="r-2",
                candidate_id="cand-1",
                challenge_surface="claim",
                reason="contradicting literature",
                evidence_ids=("E404",),
            ),
        ),
    )

    assert report.resolved_count == 1
    assert report.open_count == 1
    assert report.resolutions[1].status == "needs_follow_up"
