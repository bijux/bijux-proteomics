# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review_iteration09 import (
    EvidenceGapItem,
    prioritize_evidence_gaps,
)


def test_prioritize_evidence_gaps_ranks_by_decision_impact_and_effort() -> None:
    report = prioritize_evidence_gaps(
        (
            EvidenceGapItem(
                gap_id="gap-1",
                candidate_id="cand-1",
                description="missing orthogonal assay",
                decision_surfaces=("review", "lab"),
                decision_impact=0.9,
                uncertainty=0.7,
                collection_effort=0.5,
            ),
            EvidenceGapItem(
                gap_id="gap-2",
                candidate_id="cand-2",
                description="missing extra replicate",
                decision_surfaces=("review",),
                decision_impact=0.7,
                uncertainty=0.4,
                collection_effort=0.4,
            ),
        )
    )

    assert report.entries[0].gap_id == "gap-1"
    assert report.entries[0].priority_rank == 1
    assert report.entries[1].priority_rank == 2
