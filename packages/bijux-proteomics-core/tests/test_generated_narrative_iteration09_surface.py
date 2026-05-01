# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review_iteration09 import (
    ReviewPacketDecisionEntry,
    ReviewPacketEvidenceEntry,
    build_review_packet_schema,
    generate_review_narrative_from_structured_facts,
)


def test_generate_review_narrative_uses_structured_facts_with_links() -> None:
    packet = build_review_packet_schema(
        packet_id="packet-2",
        run_id="run-20",
        evidence=(
            ReviewPacketEvidenceEntry(
                evidence_id="E1",
                claim="target peptide is reproducibly detected",
                source="study-a",
                trust_score=0.84,
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
                rationale="signal is stable",
                evidence_ids=("E1",),
            ),
        ),
    )

    narrative = generate_review_narrative_from_structured_facts(packet)

    assert narrative.claim_count == 1
    assert narrative.lines[0].section == "decision"
    assert narrative.lines[0].evidence_ids == ("E1",)
    assert "study-a" in narrative.lines[0].text
