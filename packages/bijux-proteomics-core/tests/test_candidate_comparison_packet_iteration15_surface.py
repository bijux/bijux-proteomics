# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.intelligence_iteration15 import (
    CandidateComparisonInput,
    build_candidate_comparison_packet,
)


def test_build_candidate_comparison_packet_explains_ranking_with_evidence_links() -> (
    None
):
    packet = build_candidate_comparison_packet(
        preferred=CandidateComparisonInput(
            candidate_id="cand-a",
            rank=1,
            evidence_score=0.9,
            novelty_score=0.7,
            feasibility_score=0.8,
            risk_penalty=0.2,
            caveat_ids=("cav-1",),
            evidence_pointer_ids=("ev-2",),
        ),
        other=CandidateComparisonInput(
            candidate_id="cand-b",
            rank=2,
            evidence_score=0.7,
            novelty_score=0.6,
            feasibility_score=0.5,
            risk_penalty=0.4,
            caveat_ids=("cav-2",),
            evidence_pointer_ids=("ev-1",),
        ),
    )

    assert packet.preferred_candidate_id == "cand-a"
    assert "stronger evidence support" in packet.reasons[0]
    assert packet.evidence_pointer_ids == ("ev-1", "ev-2")
