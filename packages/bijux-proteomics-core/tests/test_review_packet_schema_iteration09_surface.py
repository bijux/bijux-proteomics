# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review_iteration09 import (
    ReviewPacketDecisionEntry,
    ReviewPacketEvidenceEntry,
    ReviewPacketRiskEntry,
    build_review_packet_schema,
)


def test_build_review_packet_schema_bundles_review_surfaces() -> None:
    packet = build_review_packet_schema(
        packet_id="packet-1",
        run_id="run-22",
        evidence=(
            ReviewPacketEvidenceEntry(
                evidence_id="E2",
                claim="protein is increased",
                source="study-a",
                trust_score=0.8,
            ),
            ReviewPacketEvidenceEntry(
                evidence_id="E1",
                claim="protein is detectable",
                source="study-b",
                trust_score=0.7,
            ),
        ),
        trust_scores={"cand-1": 0.77},
        contradictions=(),
        qc_caveats=(),
        assay_plans=(),
        risks=(
            ReviewPacketRiskEntry(
                risk_id="risk-1",
                severity="medium",
                message="limited replicate count",
                mitigation="add one replicate",
            ),
        ),
        decisions=(
            ReviewPacketDecisionEntry(
                decision_id="d-1",
                candidate_id="cand-1",
                decision_state="deferred",
                rationale="awaiting orthogonal validation",
                evidence_ids=("E1", "E2"),
            ),
        ),
    )

    assert packet.packet_id == "packet-1"
    assert packet.evidence[0].evidence_id == "E1"
    assert packet.decisions[0].decision_state == "deferred"
