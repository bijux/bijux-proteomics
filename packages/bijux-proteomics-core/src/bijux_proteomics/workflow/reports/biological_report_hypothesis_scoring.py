# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned confidence scoring rules for biological hypothesis candidates."""

from __future__ import annotations

from bijux_proteomics.domain.confidence import coerce_confidence_tier
from bijux_proteomics.interpretation.pathway_activity import (
    PathwayConditionComparisonEntry,
)
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimCandidate,
    BiologicalClaimValidationEntry,
)
from bijux_proteomics.review.evidence_graph.evidence_graph_downgrades import (
    FinalClaimEvidenceTier,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCard,
)


def _protein_hypothesis_base_confidence(
    claim: BiologicalClaimCandidate | BiologicalClaimValidationEntry,
    *,
    card: ProteinMechanismCard | None,
) -> float:
    component_scores = [
        claim.robustness_score if claim.robustness_score is not None else 0.55,
        _evidence_tier_score(None if card is None else card.evidence_tier),
        _confidence_tier_score(None if card is None else card.confidence_tier.value),
    ]
    return round(sum(component_scores) / len(component_scores), 3)


def _pathway_hypothesis_base_confidence(
    claim: BiologicalClaimCandidate | BiologicalClaimValidationEntry,
    *,
    comparison: PathwayConditionComparisonEntry | None,
) -> float:
    delta_score = min(1.0, abs(claim.pathway_delta or 0.0) / 1.0)
    comparison_score = _pathway_confidence_score(
        None if comparison is None else comparison.comparison_confidence_status.value
    )
    return float(round((delta_score + comparison_score) / 2.0, 3))


def _regulator_hypothesis_base_confidence(
    claim: BiologicalClaimCandidate | BiologicalClaimValidationEntry,
    *,
    regulator_score: float | None,
) -> float:
    score = regulator_score if regulator_score is not None else claim.regulator_score
    if score is None:
        return 0.55
    return round(score, 3)


def _evidence_tier_score(evidence_tier: FinalClaimEvidenceTier | None) -> float:
    if evidence_tier is None:
        return 0.55
    if evidence_tier.value == "high_confidence":
        return 0.9
    if evidence_tier.value == "moderate_confidence":
        return 0.7
    return 0.55


def _confidence_tier_score(confidence_tier: str | None) -> float:
    normalized = coerce_confidence_tier(confidence_tier)
    if normalized is None:
        return 0.55
    if normalized.value == "high":
        return 0.9
    if normalized.value == "moderate":
        return 0.7
    return 0.55


def _pathway_confidence_score(confidence_status: str | None) -> float:
    normalized = coerce_confidence_tier(confidence_status)
    if normalized is not None and normalized.value == "high":
        return 0.85
    return 0.55
