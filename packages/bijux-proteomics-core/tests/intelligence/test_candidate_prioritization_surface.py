# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.intelligence import (
    EvidenceGraphCandidate,
    prioritize_candidates_from_evidence_graph,
)


def test_prioritize_candidates_from_evidence_graph_orders_by_priority_score() -> None:
    report = prioritize_candidates_from_evidence_graph(
        (
            EvidenceGraphCandidate(
                candidate_id="c-high",
                evidence_strength=0.9,
                novelty_score=0.6,
                lab_feasibility=0.8,
                risk_score=0.2,
                missing_evidence_penalty=0.2,
            ),
            EvidenceGraphCandidate(
                candidate_id="c-low",
                evidence_strength=0.5,
                novelty_score=0.3,
                lab_feasibility=0.4,
                risk_score=0.7,
                missing_evidence_penalty=0.6,
            ),
        )
    )

    assert report.entries[0].candidate_id == "c-high"
    assert report.entries[0].rank == 1
