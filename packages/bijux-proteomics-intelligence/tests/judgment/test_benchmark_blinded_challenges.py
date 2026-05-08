# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.judgment.benchmark_blinded_challenges import (
    BlindedRecommendationRevealState,
    build_workflow_blinded_recommendation_challenge,
    list_workflow_blinded_recommendation_challenges,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


def test_blinded_recommendation_challenges_cover_five_flagship_families() -> None:
    reports = list_workflow_blinded_recommendation_challenges()

    assert [report.workflow_family for report in reports] == [
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    ]
    assert all(report.artifact_path.startswith("artifacts/") for report in reports)


def test_holdout_backed_families_publish_hit_and_overconfidence_rows() -> None:
    dda = build_workflow_blinded_recommendation_challenge(KnowledgeWorkflowFamily.DDA)

    assert dda.hit_count == 1
    assert dda.overconfidence_count == 1
    assert dda.miss_count == 0
    assert [finding.revealed_outcome for finding in dda.findings] == [
        BlindedRecommendationRevealState.HIT,
        BlindedRecommendationRevealState.OVERCONFIDENT,
    ]


def test_targeted_blinded_challenge_keeps_interference_miss_visible() -> None:
    targeted = build_workflow_blinded_recommendation_challenge(
        KnowledgeWorkflowFamily.TARGETED
    )

    assert targeted.hit_count == 1
    assert targeted.overconfidence_count == 1
    assert targeted.miss_count == 1
    assert any(
        finding.finding_id.endswith("interference-carryover-follow-up")
        and finding.revealed_outcome is BlindedRecommendationRevealState.MISS
        for finding in targeted.findings
    )
