# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Decision policies and evaluation for flagship benchmark-backed recommendation corpora."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_foundation.support.states import SupportState
from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    BenchmarkDecisionCorpus,
    BenchmarkDecisionOption,
    BenchmarkDecisionScenario,
    BenchmarkDisposition,
    LabBurdenTier,
)
from bijux_proteomics_intelligence.reviews.benchmarks import (
    ReviewerGroundingState,
    WorkflowBenchmarkReview,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    ComparatorClaimSupportState,
)

__all__ = [
    "BenchmarkDecisionCorpusReport",
    "BenchmarkDecisionOutcome",
    "BenchmarkDecisionPolicy",
    "build_benchmark_refusal_policy",
    "build_benchmark_surface_appeal_policy",
    "build_flagship_benchmark_decision_policy",
    "evaluate_benchmark_decision_scenario",
    "run_benchmark_decision_corpus",
]


class BenchmarkDecisionPolicy(JsonModel):
    """Scoring contract for selecting or refusing flagship benchmark paths."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1)
    evidence_weight: float = Field(..., ge=0.0)
    comparator_weight: float = Field(..., ge=0.0)
    grounding_weight: float = Field(..., ge=0.0)
    readiness_weight: float = Field(..., ge=0.0)
    surface_weight: float = Field(..., ge=0.0)
    lab_burden_weight: float = Field(..., ge=0.0)
    refusal_penalty: float = Field(..., ge=0.0)
    thin_grounding_penalty: float = Field(..., ge=0.0)
    review_only_penalty: float = Field(..., ge=0.0)
    recommend_threshold: float = Field(..., ge=0.0)
    downgrade_threshold: float = Field(..., ge=0.0)
    respect_comparator_refusal: bool = True
    respect_lab_burden: bool = True


class BenchmarkDecisionOutcome(JsonModel):
    """Outcome of one benchmark-backed decision scenario under one policy."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    policy_id: str = Field(..., min_length=1)
    disposition: BenchmarkDisposition
    selected_option_id: str | None = None
    selected_benchmark_id: str | None = None
    score_by_option_id: dict[str, float] = Field(default_factory=dict)
    blocker_set: tuple[str, ...] = Field(default_factory=tuple)
    downgrade_chain: tuple[str, ...] = Field(default_factory=tuple)
    reasoning: tuple[str, ...] = Field(default_factory=tuple)
    solved: bool


class BenchmarkDecisionCorpusReport(JsonModel):
    """Corpus run result for one benchmark-backed decision policy."""

    model_config = ConfigDict(extra="forbid")

    corpus_id: str = Field(..., min_length=1)
    policy_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    scenario_count: int = Field(..., ge=0)
    solved_scenario_count: int = Field(..., ge=0)
    results: tuple[BenchmarkDecisionOutcome, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def build_benchmark_surface_appeal_policy() -> BenchmarkDecisionPolicy:
    """Build a naive baseline that overweights attractive benchmark surfaces."""

    return BenchmarkDecisionPolicy(
        policy_id="surface-appeal-baseline",
        evidence_weight=0.1,
        comparator_weight=0.05,
        grounding_weight=0.05,
        readiness_weight=0.15,
        surface_weight=0.55,
        lab_burden_weight=0.1,
        refusal_penalty=0.12,
        thin_grounding_penalty=0.1,
        review_only_penalty=0.05,
        recommend_threshold=0.55,
        downgrade_threshold=0.4,
        respect_comparator_refusal=False,
        respect_lab_burden=False,
    )


def build_flagship_benchmark_decision_policy() -> BenchmarkDecisionPolicy:
    """Build the flagship policy for benchmark-backed recommendation quality."""

    return BenchmarkDecisionPolicy(
        policy_id="flagship-benchmark-decision",
        evidence_weight=0.26,
        comparator_weight=0.2,
        grounding_weight=0.18,
        readiness_weight=0.12,
        surface_weight=0.08,
        lab_burden_weight=0.16,
        refusal_penalty=0.34,
        thin_grounding_penalty=0.16,
        review_only_penalty=0.08,
        recommend_threshold=0.58,
        downgrade_threshold=0.42,
        respect_comparator_refusal=True,
        respect_lab_burden=True,
    )


def build_benchmark_refusal_policy() -> BenchmarkDecisionPolicy:
    """Build a harsh refusal-first policy for explicit do-not-recommend proof."""

    return BenchmarkDecisionPolicy(
        policy_id="refusal-first-benchmark-decision",
        evidence_weight=0.2,
        comparator_weight=0.24,
        grounding_weight=0.2,
        readiness_weight=0.1,
        surface_weight=0.04,
        lab_burden_weight=0.22,
        refusal_penalty=0.42,
        thin_grounding_penalty=0.22,
        review_only_penalty=0.1,
        recommend_threshold=0.6,
        downgrade_threshold=0.48,
        respect_comparator_refusal=True,
        respect_lab_burden=True,
    )


def _claim_support_score(review: WorkflowBenchmarkReview) -> float:
    total = len(review.claim_summaries)
    if total == 0:
        return 0.0
    claim_score = 0.0
    for claim in review.claim_summaries:
        if claim.support_state is SupportState.SUPPORTED:
            claim_score += 1.0
        elif claim.support_state is SupportState.ADVISORY:
            claim_score += 0.5
        elif claim.support_state is SupportState.AMBIGUOUS:
            claim_score += 0.3
    return claim_score / total


def _comparator_score(review: WorkflowBenchmarkReview) -> float:
    if review.public_claim_support_state is ComparatorClaimSupportState.SUPPORTED:
        return 1.0
    if review.public_claim_support_state is ComparatorClaimSupportState.ADVISORY:
        return 0.55
    return 0.0


def _grounding_score(review: WorkflowBenchmarkReview) -> float:
    if review.reviewer_grounding_state is ReviewerGroundingState.DECISION_GRADE:
        return 1.0
    if review.reviewer_grounding_state is ReviewerGroundingState.REVIEW_GRADE:
        return 0.68
    return 0.18


def _lab_burden_score(option: BenchmarkDecisionOption) -> float:
    if option.lab_burden is LabBurdenTier.LOW:
        return 1.0
    if option.lab_burden is LabBurdenTier.MEDIUM:
        return 0.62
    return 0.18


def _operational_burden_reason(option: BenchmarkDecisionOption) -> str:
    if option.lab_burden is LabBurdenTier.HIGH:
        return "operational burden remains too high for a justified recommendation"
    if option.lab_burden is LabBurdenTier.MEDIUM:
        return "operational burden still needs explicit control planning"
    return "operational burden is comparatively contained"


def _collect_review_blockers(review: WorkflowBenchmarkReview) -> tuple[str, ...]:
    blockers: list[str] = []
    if review.public_claim_support_state is ComparatorClaimSupportState.REFUSED:
        blockers.append("public comparator-backed claim support is refused")
    elif review.public_claim_support_state is ComparatorClaimSupportState.ADVISORY:
        blockers.append("external comparator claim support is still advisory")
    if review.reviewer_grounding_state is ReviewerGroundingState.THIN:
        blockers.append("biological grounding remains thin")
    elif review.reviewer_grounding_state is ReviewerGroundingState.REVIEW_GRADE:
        blockers.append(
            "claim support is not yet strong enough for an unqualified recommendation"
        )
    if not review.ready_for_release_review:
        blockers.append("benchmark review is not yet ready for release scrutiny")
    if review.improvement_targets:
        first_target = review.improvement_targets[0]
        if "vendor" in first_target or "library" in first_target:
            blockers.append("vendor and library comparison gaps remain open")
    return tuple(dict.fromkeys(blockers))


def _score_option(
    option: BenchmarkDecisionOption,
    policy: BenchmarkDecisionPolicy,
) -> tuple[float, tuple[str, ...]]:
    review = option.review
    score = (
        _claim_support_score(review) * policy.evidence_weight
        + _comparator_score(review) * policy.comparator_weight
        + _grounding_score(review) * policy.grounding_weight
        + (1.0 if review.ready_for_release_review else 0.0) * policy.readiness_weight
        + option.surface_attractiveness * policy.surface_weight
        + _lab_burden_score(option) * policy.lab_burden_weight
    )
    blockers = list(_collect_review_blockers(review))
    if (
        policy.respect_comparator_refusal
        and review.public_claim_support_state is ComparatorClaimSupportState.REFUSED
    ):
        score -= policy.refusal_penalty
    if review.reviewer_grounding_state is ReviewerGroundingState.THIN:
        score -= policy.thin_grounding_penalty
    elif review.reviewer_grounding_state is ReviewerGroundingState.REVIEW_GRADE:
        score -= policy.review_only_penalty
    if policy.respect_lab_burden and option.lab_burden is LabBurdenTier.HIGH:
        score -= policy.lab_burden_weight * 0.65
        blockers.append(_operational_burden_reason(option))
    return score, tuple(dict.fromkeys(blockers))


def evaluate_benchmark_decision_scenario(
    scenario: BenchmarkDecisionScenario,
    policy: BenchmarkDecisionPolicy,
) -> BenchmarkDecisionOutcome:
    """Evaluate one benchmark-backed scenario under one decision policy."""

    score_by_option_id: dict[str, float] = {}
    blockers_by_option_id: dict[str, tuple[str, ...]] = {}
    for option in scenario.options:
        score, blockers = _score_option(option, policy)
        score_by_option_id[option.option_id] = score
        blockers_by_option_id[option.option_id] = blockers

    selected_option = max(
        scenario.options,
        key=lambda item: score_by_option_id[item.option_id],
    )
    selected_score = score_by_option_id[selected_option.option_id]
    selected_blockers = blockers_by_option_id[selected_option.option_id]

    if selected_score < policy.downgrade_threshold:
        disposition = BenchmarkDisposition.DO_NOT_RECOMMEND
        selected_option_id = None
        selected_benchmark_id = None
        blocker_set = selected_blockers
        downgrade_chain: tuple[str, ...] = ()
    elif selected_score < policy.recommend_threshold or selected_blockers:
        disposition = BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE
        selected_option_id = selected_option.option_id
        selected_benchmark_id = selected_option.review.benchmark_id
        blocker_set = tuple(
            blocker
            for blocker in selected_blockers
            if blocker.startswith(
                (
                    "public comparator-backed",
                    "biological grounding",
                    "operational burden",
                )
            )
        )
        downgrade_chain = tuple(
            blocker for blocker in selected_blockers if blocker not in blocker_set
        )
    else:
        disposition = BenchmarkDisposition.RECOMMEND
        selected_option_id = selected_option.option_id
        selected_benchmark_id = selected_option.review.benchmark_id
        blocker_set = ()
        downgrade_chain = ()

    solved = (
        disposition is scenario.expected_disposition
        and selected_option_id == scenario.expected_selected_option_id
        and all(
            any(required in actual for actual in downgrade_chain)
            for required in scenario.required_downgrade_reasons
        )
        and all(
            any(required in actual for actual in blocker_set)
            for required in scenario.required_blockers
        )
    )

    return BenchmarkDecisionOutcome(
        scenario_id=scenario.scenario_id,
        policy_id=policy.policy_id,
        disposition=disposition,
        selected_option_id=selected_option_id,
        selected_benchmark_id=selected_benchmark_id,
        score_by_option_id=score_by_option_id,
        blocker_set=blocker_set,
        downgrade_chain=downgrade_chain,
        reasoning=(
            scenario.decision_quality_claim,
            scenario.naive_failure_mode,
        ),
        solved=solved,
    )


def run_benchmark_decision_corpus(
    corpus: BenchmarkDecisionCorpus,
    policy: BenchmarkDecisionPolicy,
) -> BenchmarkDecisionCorpusReport:
    """Run one benchmark-backed decision corpus under one policy."""

    results = tuple(
        evaluate_benchmark_decision_scenario(scenario, policy)
        for scenario in corpus.scenarios
    )
    return BenchmarkDecisionCorpusReport(
        corpus_id=corpus.corpus_id,
        policy_id=policy.policy_id,
        artifact_path=corpus.artifact_path,
        scenario_count=len(results),
        solved_scenario_count=sum(result.solved for result in results),
        results=results,
        note=corpus.note,
    )
