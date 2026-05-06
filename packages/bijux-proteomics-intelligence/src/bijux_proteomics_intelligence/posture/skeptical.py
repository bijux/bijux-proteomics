# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Skeptical review helpers that challenge analytical recommendations explicitly."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel, ProgramId
from bijux_proteomics_intelligence.judgment.paths import ReviewBoardDecisionPath
from bijux_proteomics_intelligence.judgment.scenarios import ScenarioAction
from bijux_proteomics_foundation.outcomes.results import OperationDisposition


class ReviewChallengeDomain(StrEnum):
    """Perspective from which a recommendation is challenged."""

    SOFTWARE = "software"
    SCIENTIFIC = "scientific"


class ReviewChallengeSeverity(StrEnum):
    """Severity level for one skeptical review finding."""

    WARN = "warn"
    BLOCK = "block"


class ReviewChallenge(JsonModel):
    """One explicit skeptical review finding over an intelligence output."""

    model_config = ConfigDict(extra="forbid")

    domain: ReviewChallengeDomain
    severity: ReviewChallengeSeverity
    code: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    rationale: list[str] = Field(default_factory=list)
    required_follow_up: list[str] = Field(default_factory=list)


class AnalyticalValueSignal(JsonModel):
    """Concrete analytical value signal that differentiates intelligence from lower layers."""

    model_config = ConfigDict(extra="forbid")

    surface: str = Field(..., min_length=1)
    value_statement: str = Field(..., min_length=1)
    supporting_fields: tuple[str, ...] = Field(default_factory=tuple)


class SkepticalReviewReport(JsonModel):
    """Structured skeptical review over one review-board decision path."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    release_ready: bool = Field(
        ..., description="Whether skeptical review found any release-blocking issues."
    )
    software_findings: list[ReviewChallenge] = Field(default_factory=list)
    scientific_findings: list[ReviewChallenge] = Field(default_factory=list)
    analytical_value_signals: list[AnalyticalValueSignal] = Field(default_factory=list)
    recommended_action: str = Field(..., min_length=1)
    notes: list[str] = Field(default_factory=list)


def _top_candidate_fields(
    path: ReviewBoardDecisionPath,
) -> tuple[dict[str, object], dict[str, float]]:
    if not path.follow_up_path.ranking.ranked_candidates:
        return {}, {}
    explainability = path.follow_up_path.ranking.ranked_candidates[0].explainability
    multi_objective = explainability.get("multi_objective_profile", {})
    if not isinstance(multi_objective, dict):
        multi_objective = {}
    numeric_profile = {
        key: float(value)
        for key, value in multi_objective.items()
        if isinstance(value, (int, float))
    }
    return explainability, numeric_profile


def _collect_analytical_value_signals(
    path: ReviewBoardDecisionPath,
    explainability: dict[str, object],
) -> list[AnalyticalValueSignal]:
    signals: list[AnalyticalValueSignal] = []
    if explainability.get("policy_lineage"):
        signals.append(
            AnalyticalValueSignal(
                surface="ranking_policy_lineage",
                value_statement="Intelligence keeps ranking reproducible instead of leaving scoring semantics implicit in downstream callers.",
                supporting_fields=("policy_lineage", "factor_scores"),
            )
        )
    if path.packet.recommendation.gate_result is not None:
        signals.append(
            AnalyticalValueSignal(
                surface="recommendation_gate_result",
                value_statement="Intelligence can refuse or degrade recommendations when contradiction or evidence posture is not good enough.",
                supporting_fields=("gate_result", "reasons"),
            )
        )
    if path.unresolved_questions:
        signals.append(
            AnalyticalValueSignal(
                surface="unresolved_question_ledger",
                value_statement="Intelligence preserves explicit unresolved questions instead of collapsing uncertainty into one opaque confidence score.",
                supporting_fields=("unresolved_questions",),
            )
        )
    if path.packet.ranked_evidence:
        signals.append(
            AnalyticalValueSignal(
                surface="review_board_evidence_lines",
                value_statement="Intelligence aligns ranking, contradiction pressure, freshness pressure, and QC caveats in one reviewable evidence packet.",
                supporting_fields=(
                    "ranked_evidence",
                    "contradiction_pressure",
                    "freshness_pressure",
                ),
            )
        )
    rule_ids = explainability.get("knowledge_grounding_rule_ids", [])
    if isinstance(rule_ids, list) and rule_ids:
        signals.append(
            AnalyticalValueSignal(
                surface="knowledge_grounding_rules",
                value_statement="Intelligence ties non-obvious ranking behavior back to knowledge-owned grounded rules instead of package-local intuition.",
                supporting_fields=("knowledge_grounding_rule_ids",),
            )
        )
    return signals


def build_skeptical_review_report(
    path: ReviewBoardDecisionPath,
) -> SkepticalReviewReport:
    """Challenge a review-board path from software and scientific review angles."""
    explainability, multi_objective = _top_candidate_fields(path)
    software_findings: list[ReviewChallenge] = []
    scientific_findings: list[ReviewChallenge] = []
    analytical_value_signals = _collect_analytical_value_signals(path, explainability)

    if not explainability.get("policy_lineage"):
        software_findings.append(
            ReviewChallenge(
                domain=ReviewChallengeDomain.SOFTWARE,
                severity=ReviewChallengeSeverity.BLOCK,
                code="missing_policy_lineage",
                summary="top-ranked candidate does not expose policy lineage",
                rationale=[
                    "reviewers cannot reproduce ranking semantics without the policy lineage",
                ],
                required_follow_up=[
                    "publish ranking policy lineage with factor weights and tie-break rules",
                ],
            )
        )
    rule_ids = explainability.get("knowledge_grounding_rule_ids", [])
    if not isinstance(rule_ids, list) or not rule_ids:
        software_findings.append(
            ReviewChallenge(
                domain=ReviewChallengeDomain.SOFTWARE,
                severity=ReviewChallengeSeverity.BLOCK,
                code="missing_grounding_rules",
                summary="ranking output is missing knowledge-grounded rule identifiers",
                rationale=[
                    "non-obvious ranking behavior should stay tied to knowledge-owned grounded rules",
                ],
                required_follow_up=[
                    "attach grounded rule identifiers to the ranking explainability payload",
                ],
            )
        )
    if path.packet.recommendation.gate_result is None:
        software_findings.append(
            ReviewChallenge(
                domain=ReviewChallengeDomain.SOFTWARE,
                severity=ReviewChallengeSeverity.BLOCK,
                code="missing_gate_result",
                summary="recommendation packet omits the machine-readable gate result",
                rationale=[
                    "downstream review consumers need an explicit supported, refused, or degraded result contract",
                ],
                required_follow_up=[
                    "emit the recommendation gate result with the review packet",
                ],
            )
        )
    elif (
        path.packet.recommendation.gate_result.disposition
        is OperationDisposition.DEGRADED_SUCCESS
    ):
        software_findings.append(
            ReviewChallenge(
                domain=ReviewChallengeDomain.SOFTWARE,
                severity=ReviewChallengeSeverity.BLOCK,
                code="degraded_recommendation_support",
                summary="recommendation remains degraded and should not be treated as a clean conclusion",
                rationale=list(
                    path.packet.recommendation.gate_result.degradation_reasons
                )
                or [
                    "downstream review should not flatten a degraded gate result into a clean recommendation",
                ],
                required_follow_up=[
                    "resolve degraded evidence posture reasons before downstream handoff",
                ],
            )
        )
    if not path.packet.recommendation.reasons:
        software_findings.append(
            ReviewChallenge(
                domain=ReviewChallengeDomain.SOFTWARE,
                severity=ReviewChallengeSeverity.WARN,
                code="missing_recommendation_reasons",
                summary="recommendation packet does not explain its action with concrete reasons",
                rationale=[
                    "review outputs should remain readable without re-running the evaluator stack",
                ],
                required_follow_up=["attach explicit recommendation reasons"],
            )
        )
    if (
        path.packet.recommendation.action is ScenarioAction.HOLD
        and not path.unresolved_questions
    ):
        software_findings.append(
            ReviewChallenge(
                domain=ReviewChallengeDomain.SOFTWARE,
                severity=ReviewChallengeSeverity.BLOCK,
                code="opaque_hold_recommendation",
                summary="hold recommendation lacks unresolved questions",
                rationale=[
                    "a hold without explicit unresolved questions collapses judgment into an opaque stop signal",
                ],
                required_follow_up=[
                    "publish the unresolved questions that keep the recommendation on hold",
                ],
            )
        )
    if len(path.unresolved_questions) >= 3:
        software_findings.append(
            ReviewChallenge(
                domain=ReviewChallengeDomain.SOFTWARE,
                severity=ReviewChallengeSeverity.BLOCK,
                code="unresolved_question_burden",
                summary="recommendation carries too many unresolved questions for a clean handoff",
                rationale=[
                    f"review path still exposes {len(path.unresolved_questions)} unresolved questions",
                ],
                required_follow_up=[
                    "reduce unresolved question burden before downstream handoff",
                ],
            )
        )

    contradiction_pressure = 0.0
    freshness_pressure = 0.0
    evidence_support = 0.0
    if path.packet.ranked_evidence:
        top_line = path.packet.ranked_evidence[0]
        contradiction_pressure = top_line.contradiction_pressure
        freshness_pressure = top_line.freshness_pressure
        evidence_support = top_line.evidence_support

    if contradiction_pressure >= 0.45:
        scientific_findings.append(
            ReviewChallenge(
                domain=ReviewChallengeDomain.SCIENTIFIC,
                severity=ReviewChallengeSeverity.BLOCK,
                code="unresolved_contradiction_pressure",
                summary="contradiction pressure remains too high for confident follow-up",
                rationale=[
                    f"top ranked evidence line still carries contradiction pressure={contradiction_pressure:.2f}",
                ],
                required_follow_up=[
                    "run contradiction-resolving assays before progression",
                ],
            )
        )
    if freshness_pressure >= 0.45:
        scientific_findings.append(
            ReviewChallenge(
                domain=ReviewChallengeDomain.SCIENTIFIC,
                severity=ReviewChallengeSeverity.WARN,
                code="stale_supporting_evidence",
                summary="supporting evidence is aging into a stale decision basis",
                rationale=[
                    f"top ranked evidence line carries freshness pressure={freshness_pressure:.2f}",
                ],
                required_follow_up=["refresh key evidence before expensive follow-up"],
            )
        )
    if evidence_support < 0.65:
        scientific_findings.append(
            ReviewChallenge(
                domain=ReviewChallengeDomain.SCIENTIFIC,
                severity=ReviewChallengeSeverity.BLOCK,
                code="weak_evidence_support",
                summary="top candidate lacks enough evidence support for a confident handoff",
                rationale=[
                    f"top ranked evidence line only reports evidence_support={evidence_support:.2f}",
                ],
                required_follow_up=["add orthogonal evidence support before handoff"],
            )
        )
    if multi_objective.get("scientific_value", 0.0) < 0.65:
        scientific_findings.append(
            ReviewChallenge(
                domain=ReviewChallengeDomain.SCIENTIFIC,
                severity=ReviewChallengeSeverity.WARN,
                code="limited_scientific_value",
                summary="top candidate scientific value is too weak to justify strong recommendation language",
                rationale=[
                    f"scientific_value={multi_objective.get('scientific_value', 0.0):.2f}",
                ],
                required_follow_up=[
                    "tighten recommendation language or improve evidence quality"
                ],
            )
        )
    if multi_objective.get("assay_feasibility", 0.0) < 0.55:
        scientific_findings.append(
            ReviewChallenge(
                domain=ReviewChallengeDomain.SCIENTIFIC,
                severity=ReviewChallengeSeverity.BLOCK,
                code="weak_assay_feasibility",
                summary="recommended follow-up is not yet practical enough for lab progression",
                rationale=[
                    f"assay_feasibility={multi_objective.get('assay_feasibility', 0.0):.2f}",
                ],
                required_follow_up=[
                    "replace or redesign the follow-up assays before lab handoff",
                ],
            )
        )
    novelty_score = multi_objective.get("novelty", 0.0)
    scientific_value = multi_objective.get("scientific_value", 0.0)
    if novelty_score > scientific_value and evidence_support < 0.7:
        scientific_findings.append(
            ReviewChallenge(
                domain=ReviewChallengeDomain.SCIENTIFIC,
                severity=ReviewChallengeSeverity.BLOCK,
                code="novelty_outpaces_grounding",
                summary="recommendation novelty pressure outpaces its scientific grounding",
                rationale=[
                    f"novelty={novelty_score:.2f}",
                    f"scientific_value={scientific_value:.2f}",
                    f"evidence_support={evidence_support:.2f}",
                ],
                required_follow_up=[
                    "add stronger grounding before novelty-heavy follow-up is recommended",
                ],
            )
        )
    if multi_objective.get("operational_reliability", 0.0) < 0.55:
        scientific_findings.append(
            ReviewChallenge(
                domain=ReviewChallengeDomain.SCIENTIFIC,
                severity=ReviewChallengeSeverity.BLOCK,
                code="fragile_follow_up_plan",
                summary="recommended follow-up remains too operationally fragile for downstream handoff",
                rationale=[
                    (
                        "operational_reliability="
                        f"{multi_objective.get('operational_reliability', 0.0):.2f}"
                    ),
                ],
                required_follow_up=[
                    "reduce operational fragility before downstream handoff",
                ],
            )
        )

    release_ready = not any(
        finding.severity is ReviewChallengeSeverity.BLOCK
        for finding in [*software_findings, *scientific_findings]
    )
    if release_ready:
        recommended_action = "proceed with review-board recommendation"
    elif any(
        finding.code == "unresolved_contradiction_pressure"
        for finding in scientific_findings
    ):
        recommended_action = (
            "hold recommendation until contradiction-resolving evidence is collected"
        )
    elif any(
        finding.code
        in {
            "degraded_recommendation_support",
            "unresolved_question_burden",
            "novelty_outpaces_grounding",
            "fragile_follow_up_plan",
        }
        for finding in [*software_findings, *scientific_findings]
    ):
        recommended_action = "hold recommendation until support and follow-up discipline are strengthened"
    else:
        recommended_action = (
            "revise the recommendation package before downstream handoff"
        )

    notes = [
        f"software_findings={len(software_findings)}",
        f"scientific_findings={len(scientific_findings)}",
        f"analytical_value_signals={len(analytical_value_signals)}",
    ]

    return SkepticalReviewReport(
        program_id=path.program_id,
        release_ready=release_ready,
        software_findings=software_findings,
        scientific_findings=scientific_findings,
        analytical_value_signals=analytical_value_signals,
        recommended_action=recommended_action,
        notes=notes,
    )


__all__ = [
    "AnalyticalValueSignal",
    "ReviewChallenge",
    "ReviewChallengeDomain",
    "ReviewChallengeSeverity",
    "SkepticalReviewReport",
    "build_skeptical_review_report",
]
