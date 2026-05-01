# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review_iteration09 import (
    ReviewPacketDecisionEntry,
    ReviewPacketEvidenceEntry,
    build_review_packet_schema,
    diff_review_packets,
)


def test_diff_review_packets_reports_added_and_changed_surfaces() -> None:
    before = build_review_packet_schema(
        packet_id="packet-before",
        run_id="run-1",
        evidence=(
            ReviewPacketEvidenceEntry(
                evidence_id="E1",
                claim="old claim",
                source="study-a",
                trust_score=0.7,
            ),
        ),
        trust_scores={"cand-1": 0.7},
        contradictions=(),
        qc_caveats=(),
        assay_plans=(),
        risks=(),
        decisions=(
            ReviewPacketDecisionEntry(
                decision_id="d-1",
                candidate_id="cand-1",
                decision_state="deferred",
                rationale="pending",
                evidence_ids=("E1",),
            ),
        ),
    )
    after = build_review_packet_schema(
        packet_id="packet-after",
        run_id="run-2",
        evidence=(
            ReviewPacketEvidenceEntry(
                evidence_id="E1",
                claim="new claim",
                source="study-a",
                trust_score=0.8,
            ),
            ReviewPacketEvidenceEntry(
                evidence_id="E2",
                claim="extra claim",
                source="study-b",
                trust_score=0.6,
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
                rationale="confirmed",
                evidence_ids=("E1", "E2"),
            ),
        ),
    )

    diff = diff_review_packets(before, after)

    assert diff.added_count == 1
    assert diff.changed_count == 2
    assert diff.removed_count == 0
