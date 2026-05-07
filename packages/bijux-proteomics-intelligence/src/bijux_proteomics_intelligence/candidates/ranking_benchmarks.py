"""Benchmark corpora for ranking decision quality and policy improvement."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.criteria import MeasurementDirection, SuccessCriterion
from bijux_proteomics.domain.program_spec import ProgramSpec, create_program_spec
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.candidates.ranking import (
    CandidateAssessment,
    CandidateRanking,
    prioritize_candidates,
)
from bijux_proteomics_intelligence.judgment.policies import RankingFactor, RankingPolicy

__all__ = [
    "RankingBenchmarkCorpus",
    "RankingBenchmarkPolicyImprovementReport",
    "RankingBenchmarkReport",
    "RankingBenchmarkScenario",
    "RankingBenchmarkScenarioResult",
    "build_flagship_ranking_policy",
    "build_legacy_ranking_policy",
    "build_reviewable_ranking_benchmark_corpus",
    "compare_ranking_policies_against_benchmark_corpus",
    "run_ranking_benchmark_corpus",
]


@dataclass(frozen=True)
class RankingBenchmarkScenario:
    """One controlled ranking scenario with an explicit expected decision."""

    scenario_id: str
    summary: str
    decision_quality_claim: str
    program: ProgramSpec
    candidates: tuple[CandidateAssessment, ...]
    expected_top_candidate_id: str
    required_rejected_candidate_ids: tuple[str, ...] = ()
    prohibited_top_candidate_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class RankingBenchmarkCorpus:
    """One governed corpus for ranking decision quality."""

    corpus_id: str
    artifact_path: str
    scenarios: tuple[RankingBenchmarkScenario, ...]
    note: str


class RankingBenchmarkScenarioResult(JsonModel):
    """Outcome of running one ranking benchmark scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    expected_top_candidate_id: str = Field(..., min_length=1)
    observed_top_candidate_id: str | None = Field(default=None)
    rejected_candidate_ids: tuple[str, ...] = Field(default_factory=tuple)
    solved: bool
    notes: tuple[str, ...] = Field(default_factory=tuple)


class RankingBenchmarkReport(JsonModel):
    """Decision-quality report for one policy across the benchmark corpus."""

    model_config = ConfigDict(extra="forbid")

    corpus_id: str = Field(..., min_length=1)
    policy_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    scenario_count: int = Field(..., ge=0)
    solved_scenario_count: int = Field(..., ge=0)
    decision_quality_score: float = Field(..., ge=0.0, le=1.0)
    results: tuple[RankingBenchmarkScenarioResult, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class RankingBenchmarkPolicyImprovementReport(JsonModel):
    """Improvement report between two policies on the same corpus."""

    model_config = ConfigDict(extra="forbid")

    corpus_id: str = Field(..., min_length=1)
    baseline_policy_id: str = Field(..., min_length=1)
    candidate_policy_id: str = Field(..., min_length=1)
    improved_scenario_ids: tuple[str, ...] = Field(default_factory=tuple)
    regressed_scenario_ids: tuple[str, ...] = Field(default_factory=tuple)
    decision_improved: bool
    note: str = Field(..., min_length=1)


def build_legacy_ranking_policy() -> RankingPolicy:
    """Build a weaker legacy-style policy that overweights surface appeal."""

    return RankingPolicy(
        policy_id="legacy-surface-heavy",
        minimum_evidence_support=0.1,
        require_manufacturability_floor=False,
        diversity_bonus_weight=0.22,
        factor_weights={
            RankingFactor.CRITERIA: 0.4,
            RankingFactor.EVIDENCE: 0.05,
            RankingFactor.MANUFACTURABILITY: 0.25,
            RankingFactor.LIABILITY: 0.15,
            RankingFactor.UNCERTAINTY: 0.15,
        },
    )


def build_flagship_ranking_policy() -> RankingPolicy:
    """Build the flagship policy used for the reviewable decision corpus."""

    return RankingPolicy(
        policy_id="flagship-reviewable-ranking",
        minimum_evidence_support=0.35,
        require_manufacturability_floor=True,
        manufacturability_floor=0.45,
        diversity_bonus_weight=0.05,
        factor_weights={
            RankingFactor.CRITERIA: 0.35,
            RankingFactor.EVIDENCE: 0.3,
            RankingFactor.MANUFACTURABILITY: 0.15,
            RankingFactor.LIABILITY: 0.1,
            RankingFactor.UNCERTAINTY: 0.1,
        },
    )


def _base_program(
    *,
    program_id: str,
    name: str,
    objective: str,
    mechanism: str,
) -> ProgramSpec:
    return create_program_spec(
        program_id=program_id,
        name=name,
        objective=objective,
        target_id=f"{program_id}-target",
        target_name=f"{name} target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism=mechanism,
    )


def build_reviewable_ranking_benchmark_corpus() -> RankingBenchmarkCorpus:
    """Build the governed benchmark corpus for ranking decision quality."""

    novelty_trap_program = _base_program(
        program_id="reviewable-ranking-novelty-trap",
        name="novelty trap guard",
        objective="prevent polished weak evidence from outranking grounded support",
        mechanism="prefer grounded evidence over novelty-heavy presentation",
    )
    novelty_trap_program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="binding_score",
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.8,
        )
    )

    manufacturability_program = _base_program(
        program_id="reviewable-ranking-manufacturability-gate",
        name="manufacturability gate",
        objective="block fragile candidates before lab promotion",
        mechanism="require candidate readiness, not only attractive scorecards",
    )
    manufacturability_program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="binding_score",
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.8,
        )
    )

    contradiction_program = _base_program(
        program_id="reviewable-ranking-contradiction-guard",
        name="contradiction guard",
        objective="prefer reproducible evidence over contradictory high novelty",
        mechanism="reward contradiction control and uncertainty control honestly",
    )
    contradiction_program.success_criteria.append(
        SuccessCriterion(
            criterion_id="effect",
            metric="pathway_effect",
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.7,
        )
    )

    return RankingBenchmarkCorpus(
        corpus_id="reviewable-ranking-corpus",
        artifact_path="artifacts/intelligence/ranking-benchmarks/reviewable-ranking-corpus.json",
        scenarios=(
            RankingBenchmarkScenario(
                scenario_id="grounded-evidence-over-novelty",
                summary="grounded evidence must beat novelty-heavy surface appeal",
                decision_quality_claim="a ranking policy should not let polished weak evidence outrank grounded support",
                program=novelty_trap_program,
                candidates=(
                    CandidateAssessment(
                        candidate_id="candidate-grounded",
                        sequence="ACDEFGHIKLMNPQRSTVWY",
                        metric_scores={"binding_score": 0.84},
                        manufacturability_score=0.68,
                        uncertainty=0.08,
                        evidence_support=0.92,
                        reproducibility_score=0.95,
                        effect_size_score=0.74,
                        novelty_score=0.22,
                        assay_feasibility_score=0.71,
                    ),
                    CandidateAssessment(
                        candidate_id="candidate-flashy",
                        sequence="ACDEFGHIKLMNPQRSTVWA",
                        metric_scores={"binding_score": 0.91},
                        manufacturability_score=0.9,
                        uncertainty=0.28,
                        evidence_support=0.21,
                        reproducibility_score=0.24,
                        effect_size_score=0.62,
                        novelty_score=0.96,
                        assay_feasibility_score=0.93,
                    ),
                ),
                expected_top_candidate_id="candidate-grounded",
                prohibited_top_candidate_ids=("candidate-flashy",),
            ),
            RankingBenchmarkScenario(
                scenario_id="manufacturability-floor-before-lab",
                summary="lab-bound ranking must reject strong-looking but unmakeable candidates",
                decision_quality_claim="a lab-facing ranking must reject candidates below the manufacturability floor",
                program=manufacturability_program,
                candidates=(
                    CandidateAssessment(
                        candidate_id="candidate-fragile",
                        sequence="ACDEFGHIKLMNPQRSTVWF",
                        metric_scores={"binding_score": 0.93},
                        manufacturability_score=0.19,
                        uncertainty=0.09,
                        evidence_support=0.78,
                        reproducibility_score=0.8,
                        effect_size_score=0.75,
                        novelty_score=0.78,
                        assay_feasibility_score=0.28,
                    ),
                    CandidateAssessment(
                        candidate_id="candidate-ready",
                        sequence="ACDEFGHIKLMNPQRSTVWC",
                        metric_scores={"binding_score": 0.86},
                        manufacturability_score=0.74,
                        uncertainty=0.11,
                        evidence_support=0.84,
                        reproducibility_score=0.83,
                        effect_size_score=0.71,
                        novelty_score=0.31,
                        assay_feasibility_score=0.76,
                    ),
                ),
                expected_top_candidate_id="candidate-ready",
                required_rejected_candidate_ids=("candidate-fragile",),
            ),
            RankingBenchmarkScenario(
                scenario_id="reproducibility-over-contradictory-appeal",
                summary="reproducible evidence must beat contradictory novelty pressure",
                decision_quality_claim="a reviewable ranking should prefer contradiction-controlled evidence over attractive but contradictory stories",
                program=contradiction_program,
                candidates=(
                    CandidateAssessment(
                        candidate_id="candidate-reproducible",
                        sequence="ACDEFGHIKLMNPQRSTVWD",
                        metric_scores={"pathway_effect": 0.78},
                        manufacturability_score=0.58,
                        uncertainty=0.06,
                        evidence_support=0.88,
                        reproducibility_score=0.91,
                        effect_size_score=0.69,
                        novelty_score=0.35,
                        assay_feasibility_score=0.67,
                    ),
                    CandidateAssessment(
                        candidate_id="candidate-contradictory",
                        sequence="ACDEFGHIKLMNPQRSTVWE",
                        metric_scores={"pathway_effect": 0.88},
                        manufacturability_score=0.81,
                        uncertainty=0.37,
                        evidence_support=0.39,
                        reproducibility_score=0.29,
                        effect_size_score=0.76,
                        novelty_score=0.92,
                        assay_feasibility_score=0.86,
                    ),
                ),
                expected_top_candidate_id="candidate-reproducible",
                prohibited_top_candidate_ids=("candidate-contradictory",),
            ),
        ),
        note=(
            "This corpus proves ranking behavior against concrete reviewable traps. "
            "It is for decision quality, not throughput theater."
        ),
    )


def _evaluate_scenario(
    scenario: RankingBenchmarkScenario,
    policy: RankingPolicy,
) -> tuple[CandidateRanking, RankingBenchmarkScenarioResult]:
    ranking = prioritize_candidates(
        scenario.program,
        list(scenario.candidates),
        policy=policy,
    )
    observed_top_candidate_id = (
        ranking.ranked_candidates[0].candidate_id if ranking.ranked_candidates else None
    )
    rejected_candidate_ids = tuple(ranking.rejected_candidates)
    notes: list[str] = []
    solved = True
    if observed_top_candidate_id != scenario.expected_top_candidate_id:
        notes.append(
            "expected top candidate "
            f"{scenario.expected_top_candidate_id} but observed {observed_top_candidate_id}"
        )
        solved = False
    missing_rejections = tuple(
        candidate_id
        for candidate_id in scenario.required_rejected_candidate_ids
        if candidate_id not in rejected_candidate_ids
    )
    if missing_rejections:
        notes.append(
            "missing required rejections: " + ", ".join(sorted(missing_rejections))
        )
        solved = False
    blocked_top = tuple(
        candidate_id
        for candidate_id in scenario.prohibited_top_candidate_ids
        if observed_top_candidate_id == candidate_id
    )
    if blocked_top:
        notes.append(
            "policy promoted prohibited top candidate: " + ", ".join(blocked_top)
        )
        solved = False
    if not notes:
        notes.append("policy satisfied the decision-quality expectation")
    return ranking, RankingBenchmarkScenarioResult(
        scenario_id=scenario.scenario_id,
        expected_top_candidate_id=scenario.expected_top_candidate_id,
        observed_top_candidate_id=observed_top_candidate_id,
        rejected_candidate_ids=rejected_candidate_ids,
        solved=solved,
        notes=tuple(notes),
    )


def run_ranking_benchmark_corpus(
    policy: RankingPolicy,
    *,
    corpus: RankingBenchmarkCorpus | None = None,
) -> RankingBenchmarkReport:
    """Run the ranking benchmark corpus for one policy."""

    corpus = corpus or build_reviewable_ranking_benchmark_corpus()
    results = tuple(_evaluate_scenario(scenario, policy)[1] for scenario in corpus.scenarios)
    solved_count = sum(result.solved for result in results)
    score = round(solved_count / len(results), 4) if results else 0.0
    return RankingBenchmarkReport(
        corpus_id=corpus.corpus_id,
        policy_id=policy.policy_id,
        artifact_path=f"artifacts/intelligence/ranking-benchmarks/{policy.policy_id}.json",
        scenario_count=len(results),
        solved_scenario_count=solved_count,
        decision_quality_score=score,
        results=results,
        note=(
            "Ranking quality is measured by solved decision traps, not by whether candidates were merely reshuffled."
        ),
    )


def compare_ranking_policies_against_benchmark_corpus(
    baseline_policy: RankingPolicy,
    candidate_policy: RankingPolicy,
    *,
    corpus: RankingBenchmarkCorpus | None = None,
) -> RankingBenchmarkPolicyImprovementReport:
    """Compare two policies against the same decision-quality corpus."""

    corpus = corpus or build_reviewable_ranking_benchmark_corpus()
    baseline = run_ranking_benchmark_corpus(baseline_policy, corpus=corpus)
    candidate = run_ranking_benchmark_corpus(candidate_policy, corpus=corpus)
    baseline_by_scenario = {result.scenario_id: result for result in baseline.results}
    candidate_by_scenario = {result.scenario_id: result for result in candidate.results}
    improved = tuple(
        scenario_id
        for scenario_id, candidate_result in candidate_by_scenario.items()
        if candidate_result.solved and not baseline_by_scenario[scenario_id].solved
    )
    regressed = tuple(
        scenario_id
        for scenario_id, baseline_result in baseline_by_scenario.items()
        if baseline_result.solved and not candidate_by_scenario[scenario_id].solved
    )
    decision_improved = (
        candidate.solved_scenario_count > baseline.solved_scenario_count and not regressed
    )
    return RankingBenchmarkPolicyImprovementReport(
        corpus_id=corpus.corpus_id,
        baseline_policy_id=baseline_policy.policy_id,
        candidate_policy_id=candidate_policy.policy_id,
        improved_scenario_ids=improved,
        regressed_scenario_ids=regressed,
        decision_improved=decision_improved,
        note=(
            "A policy counts as improved only when it solves more decision traps without introducing new regressions."
        ),
    )
