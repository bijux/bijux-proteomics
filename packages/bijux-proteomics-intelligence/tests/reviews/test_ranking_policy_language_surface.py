# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.reviews.candidates import (
    RankingPolicyRule,
    build_ranking_policy_language_document,
)


def test_build_ranking_policy_language_document_normalizes_weights() -> None:
    document = build_ranking_policy_language_document(
        policy_id="policy-review-board",
        policy_version="v1.0.0",
        rules=(
            RankingPolicyRule(metric="evidence_score", weight=2.0),
            RankingPolicyRule(metric="risk_penalty", weight=1.0, direction="minimize"),
        ),
    )

    assert len(document.policy_digest) == 64
    total_weight = sum(rule.weight for rule in document.rules)
    assert round(total_weight, 6) == 1.0
