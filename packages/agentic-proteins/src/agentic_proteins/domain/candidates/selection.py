# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Candidate selection and ranking logic."""

from __future__ import annotations

from dataclasses import dataclass

from agentic_proteins.domain.candidates.filters import filter_candidates
from agentic_proteins.domain.candidates.model import (
    Candidate,
    CandidateScore,
    CandidateSelection,
)


@dataclass(frozen=True)
class RankingWeights:
    """RankingWeights."""

    confidence: float = 0.5
    stability: float = 0.3
    novelty: float = 0.2


def rank_candidates(
    candidates: list[Candidate],
    weights: RankingWeights | None = None,
) -> list[CandidateScore]:
    """rank_candidates."""
    weights = weights or RankingWeights()
    scored: list[CandidateScore] = []
    for candidate in candidates:
        confidence = _confidence_score(candidate)
        stability = float(candidate.metrics.get("mean_plddt", 0.0)) / 100.0
        novelty = float(candidate.metrics.get("novelty", 0.0))
        score = (
            weights.confidence * confidence
            + weights.stability * stability
            + weights.novelty * novelty
        )
        scored.append(
            CandidateScore(
                candidate_id=candidate.candidate_id,
                score=score,
                rank=0,
                reasons=[
                    f"confidence={confidence:.3f}",
                    f"stability={stability:.3f}",
                    f"novelty={novelty:.3f}",
                ],
            )
        )
    scored.sort(key=lambda item: (-item.score, item.candidate_id))
    return [
        CandidateScore(
            candidate_id=item.candidate_id,
            score=item.score,
            rank=idx + 1,
            reasons=item.reasons,
        )
        for idx, item in enumerate(scored)
    ]


def pareto_frontier(candidates: list[Candidate]) -> list[str]:
    """pareto_frontier."""
    frontier: list[Candidate] = []
    for candidate in candidates:
        dominated = False
        for other in candidates:
            if candidate.candidate_id == other.candidate_id:
                continue
            if _dominates(other, candidate):
                dominated = True
                break
        if not dominated:
            frontier.append(candidate)
    frontier.sort(key=lambda c: c.candidate_id)
    return [c.candidate_id for c in frontier]


def select_candidates(
    candidates: list[Candidate],
    top_n: int = 3,
) -> CandidateSelection:
    """select_candidates."""
    filtered = filter_candidates(candidates)
    scores = rank_candidates(filtered)
    front = pareto_frontier(filtered)
    frozen_ids = [s.candidate_id for s in scores[:top_n]]
    return CandidateSelection(
        candidates=filtered,
        scores=scores,
        pareto_front=front,
        frozen_ids=frozen_ids,
        human_required=True,
        metadata={"top_n": top_n},
    )


def _dominates(a: Candidate, b: Candidate) -> bool:
    """_dominates."""
    return (
        _confidence_score(a) >= _confidence_score(b)
        and float(a.metrics.get("mean_plddt", 0.0))
        >= float(b.metrics.get("mean_plddt", 0.0))
        and float(a.metrics.get("novelty", 0.0)) >= float(b.metrics.get("novelty", 0.0))
        and (
            _confidence_score(a) > _confidence_score(b)
            or float(a.metrics.get("mean_plddt", 0.0))
            > float(b.metrics.get("mean_plddt", 0.0))
            or float(a.metrics.get("novelty", 0.0))
            > float(b.metrics.get("novelty", 0.0))
        )
    )


def _confidence_score(candidate: Candidate) -> float:
    """_confidence_score."""
    return (
        candidate.confidence.structural * 0.5
        + candidate.confidence.computational * 0.3
        + candidate.confidence.functional * 0.2
    )
