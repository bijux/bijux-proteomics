# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scenario evaluators for progression decisions."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.programs import ProgramSpec
from bijux_proteomics_knowledge import DecisionReadiness
from bijux_proteomics_intelligence.briefs import CandidateRanking
from bijux_proteomics_intelligence.candidates import CandidateRiskProfile
from bijux_proteomics_intelligence.serialization import JsonModel


class ScenarioAction(StrEnum):
    """High-level actions recommended by scenario evaluators."""

    ADVANCE = "advance"
    HOLD = "hold"
    REDESIGN = "redesign"
    SCALE_UP = "scale_up"


class HypothesisStatus(StrEnum):
    """Status of the active scientific hypothesis for decision guidance."""

    SUPPORTED = "supported"
    WEAKENED = "weakened"
    UNRESOLVED = "unresolved"


class ScenarioEvaluation(JsonModel):
    """Recommendation for a specific progression scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario: str = Field(..., min_length=1, description="Scenario under evaluation.")
    action: ScenarioAction = Field(..., description="Recommended action.")
    reasons: list[str] = Field(
        default_factory=list,
        description="Short reasons for the recommendation.",
    )
    hypothesis_status: HypothesisStatus = Field(
        default=HypothesisStatus.UNRESOLVED,
        description="How the recommendation maps to current hypothesis confidence.",
    )
    key_discriminating_experiment: str | None = Field(
        default=None,
        description="Most informative next experiment for reducing uncertainty.",
    )


class ProgressionPolicy(JsonModel):
    """Policy that governs progression decisions."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable policy identifier.")
    require_ranked_candidate: bool = Field(
        default=True,
        description="Whether progression requires at least one ranked candidate.",
    )


class SynthesisPolicy(JsonModel):
    """Policy that governs synthesis decisions."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable policy identifier.")
    maximum_residual_risk: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Maximum acceptable residual risk for synthesis.",
    )


class ScaleUpPolicy(JsonModel):
    """Policy that governs scale-up decisions."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable policy identifier.")
    minimum_decisive_records: int = Field(
        default=2,
        ge=1,
        description="Minimum decisive evidence count required for scale-up.",
    )
    maximum_residual_risk: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Maximum acceptable residual risk for scale-up.",
    )


class RedesignPolicy(JsonModel):
    """Policy that governs redesign decisions."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable policy identifier.")
    redesign_on_any_rejection: bool = Field(
        default=True,
        description="Whether any rejection should trigger redesign consideration.",
    )


class EvaluatorPolicyBundle(JsonModel):
    """Bundle of scenario policies applied together."""

    model_config = ConfigDict(extra="forbid")

    progression: ProgressionPolicy = Field(
        default_factory=lambda: ProgressionPolicy(policy_id="progression-default"),
        description="Progression scenario policy.",
    )
    synthesis: SynthesisPolicy = Field(
        default_factory=lambda: SynthesisPolicy(policy_id="synthesis-default"),
        description="Synthesis scenario policy.",
    )
    scale_up: ScaleUpPolicy = Field(
        default_factory=lambda: ScaleUpPolicy(policy_id="scale-up-default"),
        description="Scale-up scenario policy.",
    )
    redesign: RedesignPolicy = Field(
        default_factory=lambda: RedesignPolicy(policy_id="redesign-default"),
        description="Redesign scenario policy.",
    )


class ScenarioSetEvaluation(JsonModel):
    """Grouped scenario evaluations for one program state."""

    model_config = ConfigDict(extra="forbid")

    progression: ScenarioEvaluation = Field(..., description="Progression evaluation.")
    synthesis: ScenarioEvaluation = Field(..., description="Synthesis evaluation.")
    scale_up: ScenarioEvaluation = Field(..., description="Scale-up evaluation.")
    redesign: ScenarioEvaluation = Field(..., description="Redesign evaluation.")


def _top_candidate(
    ranking: CandidateRanking,
    risks: list[CandidateRiskProfile],
) -> tuple[str | None, float | None]:
    if not ranking.ranked_candidates:
        return None, None
    candidate_id = ranking.ranked_candidates[0].candidate_id
    risk_map = {risk.candidate_id: risk.residual_risk for risk in risks}
    return candidate_id, risk_map.get(candidate_id)


def evaluate_for_progression(
    program: ProgramSpec,
    ranking: CandidateRanking,
    readiness: DecisionReadiness,
    policy: ProgressionPolicy | None = None,
) -> ScenarioEvaluation:
    """Decide whether the program should progress to the next gated step."""
    policy = policy or ProgressionPolicy(policy_id="progression-default")
    reasons: list[str] = []
    if not readiness.ready:
        reasons.extend(readiness.blockers)
        return ScenarioEvaluation(
            scenario="progression",
            action=ScenarioAction.HOLD,
            reasons=reasons,
            hypothesis_status=HypothesisStatus.WEAKENED,
            key_discriminating_experiment="run orthogonal assay panel to resolve readiness blockers",
        )
    if policy.require_ranked_candidate and not ranking.ranked_candidates:
        return ScenarioEvaluation(
            scenario="progression",
            action=ScenarioAction.REDESIGN,
            reasons=["no ranked candidates remain after screening"],
            hypothesis_status=HypothesisStatus.WEAKENED,
            key_discriminating_experiment="expand candidate generation with mechanism-preserving variants",
        )
    if ranking.ranked_candidates:
        reasons.append(
            f"top candidate {ranking.ranked_candidates[0].candidate_id} is available"
        )
    else:
        reasons.append("evidence is decision-ready even though ranking has not been generated yet")
    reasons.append(f"{len(program.review_gates)} review gates are modeled in the program")
    return ScenarioEvaluation(
        scenario="progression",
        action=ScenarioAction.ADVANCE,
        reasons=reasons,
        hypothesis_status=HypothesisStatus.SUPPORTED,
        key_discriminating_experiment=None,
    )


def evaluate_for_synthesis(
    ranking: CandidateRanking,
    readiness: DecisionReadiness,
    risks: list[CandidateRiskProfile],
    policy: SynthesisPolicy | None = None,
) -> ScenarioEvaluation:
    """Decide whether the program is ready to synthesize a top candidate."""
    policy = policy or SynthesisPolicy(policy_id="synthesis-default")
    candidate_id, residual_risk = _top_candidate(ranking, risks)
    if candidate_id is None:
        return ScenarioEvaluation(
            scenario="synthesis",
            action=ScenarioAction.REDESIGN,
            reasons=["no candidates are available for synthesis"],
            hypothesis_status=HypothesisStatus.WEAKENED,
            key_discriminating_experiment="generate candidates with improved multi-objective profiles",
        )
    if not readiness.ready:
        return ScenarioEvaluation(
            scenario="synthesis",
            action=ScenarioAction.HOLD,
            reasons=readiness.blockers,
            hypothesis_status=HypothesisStatus.UNRESOLVED,
            key_discriminating_experiment="collect missing decisive evidence before synthesis",
        )
    if residual_risk is not None and residual_risk > policy.maximum_residual_risk:
        return ScenarioEvaluation(
            scenario="synthesis",
            action=ScenarioAction.REDESIGN,
            reasons=[f"top candidate {candidate_id} has residual risk {residual_risk:.2f}"],
            hypothesis_status=HypothesisStatus.WEAKENED,
            key_discriminating_experiment="run risk-focused assays on top liabilities",
        )
    return ScenarioEvaluation(
        scenario="synthesis",
        action=ScenarioAction.ADVANCE,
        reasons=[f"top candidate {candidate_id} is supported and within risk budget"],
        hypothesis_status=HypothesisStatus.SUPPORTED,
        key_discriminating_experiment=None,
    )


def evaluate_for_scale_up(
    ranking: CandidateRanking,
    readiness: DecisionReadiness,
    risks: list[CandidateRiskProfile],
    policy: ScaleUpPolicy | None = None,
) -> ScenarioEvaluation:
    """Decide whether the current top candidate is ready for scale-up."""
    policy = policy or ScaleUpPolicy(policy_id="scale-up-default")
    candidate_id, residual_risk = _top_candidate(ranking, risks)
    if candidate_id is None:
        return ScenarioEvaluation(
            scenario="scale_up",
            action=ScenarioAction.REDESIGN,
            reasons=["scale-up requires at least one prioritized candidate"],
            hypothesis_status=HypothesisStatus.WEAKENED,
        )
    if (
        not readiness.ready
        or readiness.coverage.decisive_records < policy.minimum_decisive_records
    ):
        return ScenarioEvaluation(
            scenario="scale_up",
            action=ScenarioAction.HOLD,
            reasons=[
                "scale-up needs decision-ready evidence with at least "
                f"{policy.minimum_decisive_records} decisive records"
            ],
            hypothesis_status=HypothesisStatus.UNRESOLVED,
        )
    if residual_risk is not None and residual_risk <= policy.maximum_residual_risk:
        return ScenarioEvaluation(
            scenario="scale_up",
            action=ScenarioAction.SCALE_UP,
            reasons=[f"top candidate {candidate_id} has low residual risk"],
            hypothesis_status=HypothesisStatus.SUPPORTED,
        )
    return ScenarioEvaluation(
        scenario="scale_up",
        action=ScenarioAction.HOLD,
        reasons=[f"top candidate {candidate_id} still carries too much residual risk for scale-up"],
        hypothesis_status=HypothesisStatus.UNRESOLVED,
    )


def evaluate_for_redesign(
    ranking: CandidateRanking,
    readiness: DecisionReadiness,
    policy: RedesignPolicy | None = None,
) -> ScenarioEvaluation:
    """Decide whether the system should move back into redesign."""
    policy = policy or RedesignPolicy(policy_id="redesign-default")
    if (
        not ranking.ranked_candidates
        or (policy.redesign_on_any_rejection and ranking.rejected_candidates)
    ):
        return ScenarioEvaluation(
            scenario="redesign",
            action=ScenarioAction.REDESIGN,
            reasons=["ranking outcomes indicate the current design set is weak"],
            hypothesis_status=HypothesisStatus.WEAKENED,
        )
    if not readiness.ready:
        return ScenarioEvaluation(
            scenario="redesign",
            action=ScenarioAction.HOLD,
            reasons=readiness.blockers,
            hypothesis_status=HypothesisStatus.UNRESOLVED,
        )
    return ScenarioEvaluation(
        scenario="redesign",
        action=ScenarioAction.ADVANCE,
        reasons=["current candidates and evidence do not require immediate redesign"],
        hypothesis_status=HypothesisStatus.SUPPORTED,
    )


def evaluate_all_scenarios(
    program: ProgramSpec,
    ranking: CandidateRanking,
    readiness: DecisionReadiness,
    risks: list[CandidateRiskProfile],
    *,
    policies: EvaluatorPolicyBundle | None = None,
) -> ScenarioSetEvaluation:
    """Evaluate all scenario endpoints under a shared policy bundle."""
    policies = policies or EvaluatorPolicyBundle()
    return ScenarioSetEvaluation(
        progression=evaluate_for_progression(
            program,
            ranking,
            readiness,
            policy=policies.progression,
        ),
        synthesis=evaluate_for_synthesis(
            ranking,
            readiness,
            risks,
            policy=policies.synthesis,
        ),
        scale_up=evaluate_for_scale_up(
            ranking,
            readiness,
            risks,
            policy=policies.scale_up,
        ),
        redesign=evaluate_for_redesign(
            ranking,
            readiness,
            policy=policies.redesign,
        ),
    )
