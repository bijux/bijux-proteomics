# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Candidate comparison, ranking, and outlier-linked review contracts."""

from __future__ import annotations

import hashlib
import json

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class QuantOutlierObservation(JsonModel):
    """Observed quant outlier bound to run/sample/protein context."""

    model_config = ConfigDict(extra="forbid")

    outlier_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    z_score: float
    batch_id: str = Field(..., min_length=1)


class RunQcSummaryLink(JsonModel):
    """QC linkage for one run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    qc_disposition: str = Field(..., min_length=1)
    qc_issue_codes: tuple[str, ...] = Field(default_factory=tuple)


class OutlierQcIntegratedEntry(JsonModel):
    """One outlier with integrated QC and batch/sample metadata context."""

    model_config = ConfigDict(extra="forbid")

    outlier_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    batch_id: str = Field(..., min_length=1)
    z_score: float
    qc_disposition: str = Field(..., min_length=1)
    qc_issue_codes: tuple[str, ...] = Field(default_factory=tuple)
    triage_priority: int = Field(..., ge=1, le=3)


class OutlierQcIntegratedReport(JsonModel):
    """Outlier analysis integrated with quant, QC, batch, and sample metadata."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[OutlierQcIntegratedEntry, ...] = Field(default_factory=tuple)


def build_outlier_qc_integrated_report(
    *,
    outliers: tuple[QuantOutlierObservation, ...],
    qc_summaries: tuple[RunQcSummaryLink, ...],
) -> OutlierQcIntegratedReport:
    """Connect outliers to run QC summaries, batch assignment, and sample-level metadata."""

    qc_by_run = {summary.run_id: summary for summary in qc_summaries}
    entries: list[OutlierQcIntegratedEntry] = []

    for outlier in outliers:
        qc = qc_by_run.get(outlier.run_id)
        if qc is None:
            qc_disposition = "unknown"
            qc_issue_codes: tuple[str, ...] = ()
            triage_priority = 3
        else:
            qc_disposition = qc.qc_disposition
            qc_issue_codes = qc.qc_issue_codes
            if qc.qc_disposition in {"failed", "refused"}:
                triage_priority = 1
            elif abs(outlier.z_score) >= 3.0 or qc_issue_codes:
                triage_priority = 2
            else:
                triage_priority = 3

        entries.append(
            OutlierQcIntegratedEntry(
                outlier_id=outlier.outlier_id,
                sample_id=outlier.sample_id,
                run_id=outlier.run_id,
                protein_id=outlier.protein_id,
                batch_id=outlier.batch_id,
                z_score=outlier.z_score,
                qc_disposition=qc_disposition,
                qc_issue_codes=qc_issue_codes,
                triage_priority=triage_priority,
            )
        )

    entries.sort(key=lambda entry: (entry.triage_priority, entry.outlier_id))
    return OutlierQcIntegratedReport(entries=tuple(entries))


class EvidenceGraphCandidate(JsonModel):
    """Candidate projection from the evidence graph for prioritization."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    evidence_strength: float = Field(..., ge=0.0, le=1.0)
    novelty_score: float = Field(..., ge=0.0, le=1.0)
    lab_feasibility: float = Field(..., ge=0.0, le=1.0)
    risk_score: float = Field(..., ge=0.0, le=1.0)
    missing_evidence_penalty: float = Field(..., ge=0.0, le=1.0)


class CandidatePriorityEntry(JsonModel):
    """Prioritization entry for one evidence-graph candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    priority_score: float = Field(..., ge=0.0)
    rank: int = Field(..., ge=1)


class CandidatePriorityReport(JsonModel):
    """Candidate ranking by evidence strength, novelty, feasibility, and risk."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[CandidatePriorityEntry, ...] = Field(default_factory=tuple)


def prioritize_candidates_from_evidence_graph(
    candidates: tuple[EvidenceGraphCandidate, ...],
) -> CandidatePriorityReport:
    """Rank candidates from evidence graph features without hiding risk penalties."""

    if not candidates:
        return CandidatePriorityReport(entries=())

    scored = [
        (
            candidate.candidate_id,
            0.35 * candidate.evidence_strength
            + 0.2 * candidate.novelty_score
            + 0.25 * candidate.lab_feasibility
            + 0.1 * (1.0 - candidate.risk_score)
            + 0.1 * (1.0 - candidate.missing_evidence_penalty),
        )
        for candidate in candidates
    ]
    scored.sort(key=lambda item: (-item[1], item[0]))

    entries = tuple(
        CandidatePriorityEntry(
            candidate_id=candidate_id, priority_score=score, rank=index + 1
        )
        for index, (candidate_id, score) in enumerate(scored)
    )
    return CandidatePriorityReport(entries=entries)


class MultiObjectiveRankingInput(JsonModel):
    """Candidate objective inputs for multi-objective ranking."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    evidence_score: float = Field(..., ge=0.0, le=1.0)
    novelty_score: float = Field(..., ge=0.0, le=1.0)
    lab_feasibility_score: float = Field(..., ge=0.0, le=1.0)
    cost_penalty: float = Field(..., ge=0.0, le=1.0)
    risk_penalty: float = Field(..., ge=0.0, le=1.0)
    expected_gain_score: float = Field(..., ge=0.0, le=1.0)


class MultiObjectiveRankingEntry(JsonModel):
    """Multi-objective score and ranking result for one candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    objective_score: float
    rank: int = Field(..., ge=1)


class MultiObjectiveRankingReport(JsonModel):
    """Ranking report across evidence, novelty, feasibility, cost, risk, and gain."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[MultiObjectiveRankingEntry, ...] = Field(default_factory=tuple)


def build_multi_objective_ranking_report(
    candidates: tuple[MultiObjectiveRankingInput, ...],
) -> MultiObjectiveRankingReport:
    """Rank candidates across weighted objectives while keeping penalties explicit."""

    scored = [
        (
            candidate.candidate_id,
            0.24 * candidate.evidence_score
            + 0.14 * candidate.novelty_score
            + 0.2 * candidate.lab_feasibility_score
            + 0.22 * candidate.expected_gain_score
            + 0.1 * (1.0 - candidate.cost_penalty)
            + 0.1 * (1.0 - candidate.risk_penalty),
        )
        for candidate in candidates
    ]
    scored.sort(key=lambda item: (-item[1], item[0]))
    return MultiObjectiveRankingReport(
        entries=tuple(
            MultiObjectiveRankingEntry(
                candidate_id=candidate_id,
                objective_score=score,
                rank=index + 1,
            )
            for index, (candidate_id, score) in enumerate(scored)
        )
    )


class RankingPolicyRule(JsonModel):
    """One ranking policy rule for inspectable scoring behavior."""

    model_config = ConfigDict(extra="forbid")

    metric: str = Field(..., min_length=1)
    weight: float = Field(..., ge=0.0)
    transform: str = Field(default="identity", min_length=1)
    direction: str = Field(default="maximize", pattern=r"^(maximize|minimize)$")


class RankingPolicyLanguageDocument(JsonModel):
    """Versioned and inspectable ranking policy language document."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1)
    policy_version: str = Field(..., min_length=1)
    rules: tuple[RankingPolicyRule, ...] = Field(default_factory=tuple)
    policy_digest: str = Field(..., min_length=64, max_length=64)


def build_ranking_policy_language_document(
    *,
    policy_id: str,
    policy_version: str,
    rules: tuple[RankingPolicyRule, ...],
) -> RankingPolicyLanguageDocument:
    """Build canonical versioned ranking policy with reproducible digest."""

    if not rules:
        raise ValueError("ranking policy requires at least one rule")
    total_weight = sum(rule.weight for rule in rules)
    if total_weight <= 0.0:
        raise ValueError("ranking policy total weight must be positive")

    normalized_rules = tuple(
        sorted(
            (
                RankingPolicyRule(
                    metric=rule.metric,
                    weight=rule.weight / total_weight,
                    transform=rule.transform,
                    direction=rule.direction,
                )
                for rule in rules
            ),
            key=lambda rule: (rule.metric, rule.direction, rule.transform),
        )
    )
    digest = hashlib.sha256(
        json.dumps(
            {
                "policy_id": policy_id,
                "policy_version": policy_version,
                "rules": [rule.model_dump(mode="json") for rule in normalized_rules],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return RankingPolicyLanguageDocument(
        policy_id=policy_id,
        policy_version=policy_version,
        rules=normalized_rules,
        policy_digest=digest,
    )


class CandidateComparisonInput(JsonModel):
    """Scored candidate inputs used to explain ranking differences."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    rank: int = Field(..., ge=1)
    evidence_score: float = Field(..., ge=0.0, le=1.0)
    novelty_score: float = Field(..., ge=0.0, le=1.0)
    feasibility_score: float = Field(..., ge=0.0, le=1.0)
    risk_penalty: float = Field(..., ge=0.0, le=1.0)
    caveat_ids: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointer_ids: tuple[str, ...] = Field(default_factory=tuple)


class CandidateComparisonPacket(JsonModel):
    """Justification packet for why one candidate outranks another."""

    model_config = ConfigDict(extra="forbid")

    preferred_candidate_id: str = Field(..., min_length=1)
    other_candidate_id: str = Field(..., min_length=1)
    reasons: tuple[str, ...] = Field(default_factory=tuple)
    caveat_ids: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointer_ids: tuple[str, ...] = Field(default_factory=tuple)


def build_candidate_comparison_packet(
    *,
    preferred: CandidateComparisonInput,
    other: CandidateComparisonInput,
) -> CandidateComparisonPacket:
    """Generate evidence-linked packet describing why one candidate outranks another."""

    reasons: list[str] = []
    if preferred.rank > other.rank:
        raise ValueError(
            "preferred candidate rank must be better or equal to comparator"
        )
    if preferred.evidence_score > other.evidence_score:
        reasons.append("preferred candidate has stronger evidence support")
    if preferred.novelty_score > other.novelty_score:
        reasons.append("preferred candidate offers higher novelty value")
    if preferred.feasibility_score > other.feasibility_score:
        reasons.append("preferred candidate is more feasible for lab follow-up")
    if preferred.risk_penalty < other.risk_penalty:
        reasons.append("preferred candidate carries lower risk burden")
    if not reasons:
        reasons.append(
            "preferred candidate retains tie-break priority in ranking policy"
        )

    merged_caveats = tuple(sorted(set(preferred.caveat_ids + other.caveat_ids)))
    merged_evidence = tuple(
        sorted(set(preferred.evidence_pointer_ids + other.evidence_pointer_ids))
    )
    return CandidateComparisonPacket(
        preferred_candidate_id=preferred.candidate_id,
        other_candidate_id=other.candidate_id,
        reasons=tuple(reasons),
        caveat_ids=merged_caveats,
        evidence_pointer_ids=merged_evidence,
    )
