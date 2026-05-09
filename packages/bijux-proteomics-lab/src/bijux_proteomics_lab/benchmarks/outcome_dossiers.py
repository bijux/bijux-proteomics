# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Outcome-bearing flagship follow-up dossiers for benchmark-backed lab consequences."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.judgment.benchmark_policies import (
    BenchmarkDisposition,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)

__all__ = [
    "FlagshipAssayWorthLedger",
    "FlagshipAssayWorthLedgerEntry",
    "FlagshipFollowUpOutcomeBasis",
    "FlagshipFollowUpOutcomeDossier",
    "FlagshipFollowUpOutcomeDossierFamily",
    "FlagshipFollowUpOutcomeImpact",
    "FlagshipJustifiedButLowYieldReport",
    "FlagshipJustifiedButLowYieldReportEntry",
    "FlagshipRecommendationRevisionReport",
    "FlagshipRecommendationRevisionReportEntry",
    "FlagshipUnderestimatedButUsefulReport",
    "FlagshipUnderestimatedButUsefulReportEntry",
    "build_flagship_assay_worth_ledger",
    "build_flagship_follow_up_outcome_dossier",
    "build_flagship_follow_up_outcome_dossier_family",
    "build_flagship_justified_but_low_yield_report",
    "build_flagship_recommendation_revision_report",
    "build_flagship_underestimated_but_useful_report",
]


class FlagshipFollowUpOutcomeBasis(StrEnum):
    """Evidence basis for a shipped requested-versus-observed follow-up dossier."""

    BENCHMARK_SIMULATED = "benchmark_simulated"


class FlagshipFollowUpOutcomeImpact(StrEnum):
    """Decision impact visible after one shipped follow-up loop."""

    CALIBRATED = "calibrated"
    NARROWED = "narrowed"
    STRENGTHENED = "strengthened"
    WITHDREW = "withdrew"


class FlagshipFollowUpOutcomeDossier(JsonModel):
    """One shipped requested-versus-observed dossier for a flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    dossier_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    benchmark_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    outcome_basis: FlagshipFollowUpOutcomeBasis
    planning_packet_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    batch_id: str = Field(..., min_length=1)
    requested_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    observed_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    matched_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    missing_requested_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    unexpected_observed_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    blocked_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    weakened_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    promoted_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    initial_recommendation_disposition: BenchmarkDisposition
    revised_recommendation_disposition: BenchmarkDisposition
    recommendation_changed: bool
    belief_posture: str = Field(..., min_length=1)
    observed_information_gain_score: float = Field(..., ge=0.0, le=1.0)
    relative_cost_score: float = Field(..., ge=0.0, le=1.0)
    turnaround_days: int = Field(..., ge=0)
    final_decision_impact: FlagshipFollowUpOutcomeImpact
    worth_it: bool
    looked_justified_initially: bool
    looked_weak_initially: bool
    outcome_summary: str = Field(..., min_length=1)
    early_block_signals: tuple[str, ...] = Field(default_factory=tuple)
    missed_positive_signals: tuple[str, ...] = Field(default_factory=tuple)
    learning_points: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipFollowUpOutcomeDossierFamily(JsonModel):
    """Family surface spanning the shipped flagship outcome dossiers."""

    model_config = ConfigDict(extra="forbid")

    family_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    dossiers: tuple[FlagshipFollowUpOutcomeDossier, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipAssayWorthLedgerEntry(JsonModel):
    """Cross-family value ledger row for one shipped follow-up loop."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    dossier_id: str = Field(..., min_length=1)
    outcome_basis: FlagshipFollowUpOutcomeBasis
    worth_it: bool
    recommendation_changed: bool
    observed_information_gain_score: float = Field(..., ge=0.0, le=1.0)
    relative_cost_score: float = Field(..., ge=0.0, le=1.0)
    turnaround_days: int = Field(..., ge=0)
    final_decision_impact: FlagshipFollowUpOutcomeImpact
    final_decision_impact_score: float = Field(..., ge=0.0, le=1.0)
    overall_value_score: float = Field(..., ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class FlagshipAssayWorthLedger(JsonModel):
    """Cross-family ledger for whether shipped follow-up loops were worth it."""

    model_config = ConfigDict(extra="forbid")

    ledger_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipAssayWorthLedgerEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipRecommendationRevisionReportEntry(JsonModel):
    """One case where observed outcomes forced recommendation revision."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    dossier_id: str = Field(..., min_length=1)
    initial_recommendation_disposition: BenchmarkDisposition
    revised_recommendation_disposition: BenchmarkDisposition
    final_decision_impact: FlagshipFollowUpOutcomeImpact
    driver_signals: tuple[str, ...] = Field(default_factory=tuple)
    outcome_summary: str = Field(..., min_length=1)


class FlagshipRecommendationRevisionReport(JsonModel):
    """Cross-family report for recommendation changes after shipped outcomes."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipRecommendationRevisionReportEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class FlagshipJustifiedButLowYieldReportEntry(JsonModel):
    """One follow-up path that looked justified but did not repay the cost."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    dossier_id: str = Field(..., min_length=1)
    early_block_signals: tuple[str, ...] = Field(default_factory=tuple)
    outcome_summary: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class FlagshipJustifiedButLowYieldReport(JsonModel):
    """Cross-family report for low-yield follow-up loops that should have been stopped earlier."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipJustifiedButLowYieldReportEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class FlagshipUnderestimatedButUsefulReportEntry(JsonModel):
    """One follow-up path that looked weak but materially improved the decision."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    dossier_id: str = Field(..., min_length=1)
    missed_positive_signals: tuple[str, ...] = Field(default_factory=tuple)
    outcome_summary: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class FlagshipUnderestimatedButUsefulReport(JsonModel):
    """Cross-family report for useful follow-up loops that initial ranking undervalued."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipUnderestimatedButUsefulReportEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class _OutcomeBlueprint(JsonModel):
    """Durable per-family blueprint for one shipped benchmark follow-up loop."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    batch_id: str = Field(..., min_length=1)
    requested_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    observed_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    blocked_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    weakened_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    promoted_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    initial_recommendation_disposition: BenchmarkDisposition
    revised_recommendation_disposition: BenchmarkDisposition
    belief_posture: str = Field(..., min_length=1)
    observed_information_gain_score: float = Field(..., ge=0.0, le=1.0)
    relative_cost_score: float = Field(..., ge=0.0, le=1.0)
    turnaround_days: int = Field(..., ge=0)
    final_decision_impact: FlagshipFollowUpOutcomeImpact
    worth_it: bool
    looked_justified_initially: bool
    looked_weak_initially: bool
    outcome_summary: str = Field(..., min_length=1)
    early_block_signals: tuple[str, ...] = Field(default_factory=tuple)
    missed_positive_signals: tuple[str, ...] = Field(default_factory=tuple)
    learning_points: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


_DOSSIER_FAMILIES: tuple[KnowledgeWorkflowFamily, ...] = (
    KnowledgeWorkflowFamily.DDA,
    KnowledgeWorkflowFamily.DIA,
    KnowledgeWorkflowFamily.LFQ,
    KnowledgeWorkflowFamily.PTM,
    KnowledgeWorkflowFamily.TARGETED,
)

_OUTCOME_BLUEPRINTS: dict[KnowledgeWorkflowFamily, _OutcomeBlueprint] = {
    KnowledgeWorkflowFamily.DDA: _OutcomeBlueprint(
        benchmark_id="benchmark:dda_search_reproducibility",
        candidate_id="dda-cross-engine-follow-up",
        batch_id="dda-follow-up-batch",
        requested_assay_ids=(
            "dda-repeat-digest",
            "dda-pooled-reference",
            "dda-carryover-blank",
        ),
        observed_assay_ids=(
            "dda-repeat-digest",
            "dda-pooled-reference",
            "dda-carryover-blank",
        ),
        promoted_evidence_ids=("claim:dda_target_decoy_stability",),
        initial_recommendation_disposition=BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE,
        revised_recommendation_disposition=BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE,
        belief_posture="reinforcing",
        observed_information_gain_score=0.64,
        relative_cost_score=0.38,
        turnaround_days=4,
        final_decision_impact=FlagshipFollowUpOutcomeImpact.CALIBRATED,
        worth_it=True,
        looked_justified_initially=True,
        looked_weak_initially=False,
        outcome_summary=(
            "The repeat digest confirmed target-decoy and contaminant boundaries but did not justify stronger DDA authority than bounded outsider-auditable posture."
        ),
        learning_points=(
            "matched assays preserved the intended closure loop without widening public language",
            "the follow-up repaid cost because it stabilized the contaminant and pooled-reference boundary",
        ),
        note=(
            "This dossier keeps one benchmark-simulated DDA requested-versus-observed loop public so lab consequence is judged on observed closure pressure rather than on assay-planning prose alone."
        ),
    ),
    KnowledgeWorkflowFamily.DIA: _OutcomeBlueprint(
        benchmark_id="benchmark:dia_library_extraction_consistency",
        candidate_id="dia-library-pressure-follow-up",
        batch_id="dia-follow-up-batch",
        requested_assay_ids=("dia-library-bridge", "dia-matrix-shift-repeat"),
        observed_assay_ids=("dia-matrix-shift-repeat",),
        blocked_assay_ids=("dia-library-bridge",),
        weakened_assay_ids=("dia-matrix-shift-repeat",),
        initial_recommendation_disposition=BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE,
        revised_recommendation_disposition=BenchmarkDisposition.DO_NOT_RECOMMEND,
        belief_posture="blocked",
        observed_information_gain_score=0.29,
        relative_cost_score=0.66,
        turnaround_days=7,
        final_decision_impact=FlagshipFollowUpOutcomeImpact.WITHDREW,
        worth_it=False,
        looked_justified_initially=True,
        looked_weak_initially=False,
        outcome_summary=(
            "The matrix-shift repeat exposed library-conditioned fragility, so the follow-up consumed queue and still forced the recommendation back to refusal."
        ),
        early_block_signals=(
            "library dependence was already the dominant public cap on DIA authority",
            "the thinner package family still showed unstable transfer under matrix shift",
        ),
        learning_points=(
            "requested assay loss should block any attempt to treat DIA follow-up as laboratory closure",
            "strong import-backed review does not rescue a loop that fails its own library bridge",
        ),
        note=(
            "This dossier keeps one benchmark-simulated DIA closure loop honest by showing a path that looked justified, ran partly, and still was not worth the queue it consumed."
        ),
    ),
    KnowledgeWorkflowFamily.LFQ: _OutcomeBlueprint(
        benchmark_id="benchmark:lfq_cohort_repeatability",
        candidate_id="lfq-cohort-repeat-follow-up",
        batch_id="lfq-follow-up-batch",
        requested_assay_ids=("lfq-extra-replicate-block", "lfq-randomized-repeat"),
        observed_assay_ids=("lfq-extra-replicate-block",),
        blocked_assay_ids=("lfq-randomized-repeat",),
        weakened_assay_ids=("lfq-extra-replicate-block",),
        initial_recommendation_disposition=BenchmarkDisposition.DO_NOT_RECOMMEND,
        revised_recommendation_disposition=BenchmarkDisposition.DO_NOT_RECOMMEND,
        belief_posture="weakening",
        observed_information_gain_score=0.21,
        relative_cost_score=0.58,
        turnaround_days=12,
        final_decision_impact=FlagshipFollowUpOutcomeImpact.NARROWED,
        worth_it=False,
        looked_justified_initially=False,
        looked_weak_initially=True,
        outcome_summary=(
            "The extra LFQ repeat only confirmed that missingness and cohort-shape weakness still dominate, so the loop consumed time without improving biological clarity."
        ),
        early_block_signals=(
            "repeatability was never the missing piece; cohort design weakness was",
            "the public package already showed missingness pressure large enough to block escalation",
        ),
        learning_points=(
            "low-information repeats should stay refused when the biological conclusion is still design-limited",
        ),
        note=(
            "This dossier records a weak LFQ path that remained weak after execution, so refusal is grounded in visible requested-versus-observed closure instead of abstract caution."
        ),
    ),
    KnowledgeWorkflowFamily.PTM: _OutcomeBlueprint(
        benchmark_id="benchmark:ptm_localization_consistency",
        candidate_id="ptm-site-resolution-follow-up",
        batch_id="ptm-follow-up-batch",
        requested_assay_ids=("ptm-site-targetability", "ptm-orthogonal-validation"),
        observed_assay_ids=(
            "ptm-site-targetability",
            "ptm-orthogonal-validation",
        ),
        weakened_assay_ids=("ptm-site-targetability",),
        promoted_evidence_ids=("claim:ptm_site_resolution_boundary",),
        initial_recommendation_disposition=BenchmarkDisposition.DO_NOT_RECOMMEND,
        revised_recommendation_disposition=BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE,
        belief_posture="mixed",
        observed_information_gain_score=0.71,
        relative_cost_score=0.73,
        turnaround_days=9,
        final_decision_impact=FlagshipFollowUpOutcomeImpact.STRENGTHENED,
        worth_it=True,
        looked_justified_initially=False,
        looked_weak_initially=True,
        outcome_summary=(
            "The PTM follow-up clarified which site-level claims survive ambiguity pressure, so one previously refused path becomes worth a bounded recommendation with explicit caveats."
        ),
        missed_positive_signals=(
            "the benchmark already isolated one targetable site family even while broader occupancy remained blocked",
            "orthogonal validation pressure was narrower than the earlier blanket PTM refusal implied",
        ),
        learning_points=(
            "site-level ambiguity can still repay follow-up when the closure question is narrow and explicitly targetable",
            "useful PTM follow-up should strengthen a bounded claim rather than erase the wider ambiguity warning",
        ),
        note=(
            "This dossier records one benchmark-simulated PTM path where a weak-looking follow-up became decision-useful because the outcome narrowed ambiguity instead of pretending to solve all PTM burden."
        ),
    ),
    KnowledgeWorkflowFamily.TARGETED: _OutcomeBlueprint(
        benchmark_id="benchmark:targeted_transition_consistency",
        candidate_id="targeted-calibration-follow-up",
        batch_id="targeted-follow-up-batch",
        requested_assay_ids=("prm-assay", "orthogonal-assay"),
        observed_assay_ids=("prm-assay", "orthogonal-assay"),
        promoted_evidence_ids=(
            "claim:targeted_transition_consistency",
            "claim:targeted_interference_boundary",
        ),
        initial_recommendation_disposition=BenchmarkDisposition.DO_NOT_RECOMMEND,
        revised_recommendation_disposition=BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE,
        belief_posture="reinforcing",
        observed_information_gain_score=0.84,
        relative_cost_score=0.42,
        turnaround_days=3,
        final_decision_impact=FlagshipFollowUpOutcomeImpact.CALIBRATED,
        worth_it=True,
        looked_justified_initially=False,
        looked_weak_initially=True,
        outcome_summary=(
            "The targeted follow-up delivered useful calibration and interference clarification quickly enough to justify a bounded recommendation where the original benchmark packet stayed refused."
        ),
        missed_positive_signals=(
            "transition-level QC was already specific enough to support one narrow closure loop",
            "the carryover companion package exposed a calibration question that a small targeted repeat could answer efficiently",
        ),
        learning_points=(
            "fast calibration-facing loops can be worth it even when broader targeted authority remains bounded",
            "follow-up value here comes from interference clarification, not from pretending vendor-parity authority exists",
        ),
        note=(
            "This dossier makes the targeted closure loop inspectable as a shipped requested-versus-observed consequence surface instead of leaving usefulness hidden behind QC prose."
        ),
    ),
}


def _tuple_difference(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    right_set = set(right)
    return tuple(value for value in left if value not in right_set)


def build_flagship_follow_up_outcome_dossier(
    workflow_family: KnowledgeWorkflowFamily,
) -> FlagshipFollowUpOutcomeDossier:
    """Build one shipped requested-versus-observed outcome dossier."""

    blueprint = _OUTCOME_BLUEPRINTS[workflow_family]
    matched_assay_ids = tuple(
        assay_id
        for assay_id in blueprint.requested_assay_ids
        if assay_id in blueprint.observed_assay_ids
    )
    missing_requested_assay_ids = _tuple_difference(
        blueprint.requested_assay_ids,
        blueprint.observed_assay_ids,
    )
    unexpected_observed_assay_ids = _tuple_difference(
        blueprint.observed_assay_ids,
        blueprint.requested_assay_ids,
    )
    return FlagshipFollowUpOutcomeDossier(
        dossier_id=f"flagship_follow_up_outcome:{workflow_family.value}",
        artifact_path=(
            "artifacts/lab/flagship-follow-up-outcomes/"
            f"{workflow_family.value}.json"
        ),
        benchmark_id=blueprint.benchmark_id,
        workflow_family=workflow_family,
        outcome_basis=FlagshipFollowUpOutcomeBasis.BENCHMARK_SIMULATED,
        planning_packet_id=f"flagship_lab_packet:{workflow_family.value}",
        candidate_id=blueprint.candidate_id,
        batch_id=blueprint.batch_id,
        requested_assay_ids=blueprint.requested_assay_ids,
        observed_assay_ids=blueprint.observed_assay_ids,
        matched_assay_ids=matched_assay_ids,
        missing_requested_assay_ids=missing_requested_assay_ids,
        unexpected_observed_assay_ids=unexpected_observed_assay_ids,
        blocked_assay_ids=blueprint.blocked_assay_ids,
        weakened_assay_ids=blueprint.weakened_assay_ids,
        promoted_evidence_ids=blueprint.promoted_evidence_ids,
        initial_recommendation_disposition=(
            blueprint.initial_recommendation_disposition
        ),
        revised_recommendation_disposition=blueprint.revised_recommendation_disposition,
        recommendation_changed=(
            blueprint.initial_recommendation_disposition
            is not blueprint.revised_recommendation_disposition
        ),
        belief_posture=blueprint.belief_posture,
        observed_information_gain_score=blueprint.observed_information_gain_score,
        relative_cost_score=blueprint.relative_cost_score,
        turnaround_days=blueprint.turnaround_days,
        final_decision_impact=blueprint.final_decision_impact,
        worth_it=blueprint.worth_it,
        looked_justified_initially=blueprint.looked_justified_initially,
        looked_weak_initially=blueprint.looked_weak_initially,
        outcome_summary=blueprint.outcome_summary,
        early_block_signals=blueprint.early_block_signals,
        missed_positive_signals=blueprint.missed_positive_signals,
        learning_points=blueprint.learning_points,
        note=blueprint.note,
    )


def build_flagship_follow_up_outcome_dossier_family() -> (
    FlagshipFollowUpOutcomeDossierFamily
):
    """Build the five flagship requested-versus-observed dossiers."""

    return FlagshipFollowUpOutcomeDossierFamily(
        family_id="flagship-follow-up-outcome-dossiers",
        artifact_path="artifacts/lab/flagship-follow-up-outcomes/family.json",
        dossiers=tuple(
            build_flagship_follow_up_outcome_dossier(workflow_family)
            for workflow_family in _DOSSIER_FAMILIES
        ),
        note=(
            "These dossiers keep one shipped requested-versus-observed closure loop visible for each flagship family so lab consequence depends on observed outcomes, cost, and decision impact rather than on assay-planning posture alone."
        ),
    )


def _impact_score(impact: FlagshipFollowUpOutcomeImpact) -> float:
    return {
        FlagshipFollowUpOutcomeImpact.WITHDREW: 0.25,
        FlagshipFollowUpOutcomeImpact.NARROWED: 0.45,
        FlagshipFollowUpOutcomeImpact.CALIBRATED: 0.72,
        FlagshipFollowUpOutcomeImpact.STRENGTHENED: 0.84,
    }[impact]


def _overall_value_score(dossier: FlagshipFollowUpOutcomeDossier) -> float:
    turnaround_score = max(0.0, 1.0 - min(dossier.turnaround_days, 14) / 14.0)
    score = (
        dossier.observed_information_gain_score * 0.45
        + _impact_score(dossier.final_decision_impact) * 0.35
        + (1.0 - dossier.relative_cost_score) * 0.1
        + turnaround_score * 0.1
    )
    return round(score, 2)


@lru_cache(maxsize=1)
def _dossiers_by_family() -> dict[KnowledgeWorkflowFamily, FlagshipFollowUpOutcomeDossier]:
    family = build_flagship_follow_up_outcome_dossier_family()
    return {dossier.workflow_family: dossier for dossier in family.dossiers}


def build_flagship_assay_worth_ledger() -> FlagshipAssayWorthLedger:
    """Build the cross-family assay-worth-it ledger."""

    entries = tuple(
        sorted(
            (
                FlagshipAssayWorthLedgerEntry(
                    workflow_family=dossier.workflow_family,
                    benchmark_id=dossier.benchmark_id,
                    dossier_id=dossier.dossier_id,
                    outcome_basis=dossier.outcome_basis,
                    worth_it=dossier.worth_it,
                    recommendation_changed=dossier.recommendation_changed,
                    observed_information_gain_score=(
                        dossier.observed_information_gain_score
                    ),
                    relative_cost_score=dossier.relative_cost_score,
                    turnaround_days=dossier.turnaround_days,
                    final_decision_impact=dossier.final_decision_impact,
                    final_decision_impact_score=_impact_score(
                        dossier.final_decision_impact
                    ),
                    overall_value_score=_overall_value_score(dossier),
                    note=(
                        "This ledger row scores observed information gain, cost, turnaround, and final decision impact together so lab consequence can be argued with bounded evidence instead of intuition."
                    ),
                )
                for dossier in _dossiers_by_family().values()
            ),
            key=lambda entry: (-entry.overall_value_score, entry.workflow_family.value),
        )
    )
    return FlagshipAssayWorthLedger(
        ledger_id="flagship-assay-worth-ledger",
        artifact_path="artifacts/lab/flagship-follow-up-outcomes/assay_worth_ledger.json",
        entries=entries,
        note=(
            "This ledger ranks shipped benchmark follow-up loops by observed value rather than by whether the original recommendation prose sounded confident."
        ),
    )


def build_flagship_recommendation_revision_report() -> (
    FlagshipRecommendationRevisionReport
):
    """Build the report for workflows whose recommendation changed after outcomes."""

    entries = tuple(
        FlagshipRecommendationRevisionReportEntry(
            workflow_family=dossier.workflow_family,
            benchmark_id=dossier.benchmark_id,
            dossier_id=dossier.dossier_id,
            initial_recommendation_disposition=(
                dossier.initial_recommendation_disposition
            ),
            revised_recommendation_disposition=(
                dossier.revised_recommendation_disposition
            ),
            final_decision_impact=dossier.final_decision_impact,
            driver_signals=(
                dossier.early_block_signals or dossier.missed_positive_signals
            )[:3],
            outcome_summary=dossier.outcome_summary,
        )
        for dossier in _dossiers_by_family().values()
        if dossier.recommendation_changed
    )
    return FlagshipRecommendationRevisionReport(
        report_id="flagship-recommendation-revision-report",
        artifact_path=(
            "artifacts/lab/flagship-follow-up-outcomes/recommendation_revisions.json"
        ),
        entries=entries,
        note=(
            "This report names every flagship family where the shipped follow-up outcome forced the recommendation posture to strengthen, narrow, or withdraw."
        ),
    )


def build_flagship_justified_but_low_yield_report() -> (
    FlagshipJustifiedButLowYieldReport
):
    """Build the report for follow-up loops that should have been blocked earlier."""

    entries = tuple(
        FlagshipJustifiedButLowYieldReportEntry(
            workflow_family=dossier.workflow_family,
            benchmark_id=dossier.benchmark_id,
            dossier_id=dossier.dossier_id,
            early_block_signals=dossier.early_block_signals,
            outcome_summary=dossier.outcome_summary,
            note=(
                "The early block signals here are the exact warnings the repository should have weighted higher before spending assay budget."
            ),
        )
        for dossier in _dossiers_by_family().values()
        if dossier.looked_justified_initially and not dossier.worth_it
    )
    return FlagshipJustifiedButLowYieldReport(
        report_id="flagship-justified-but-low-yield-report",
        artifact_path=(
            "artifacts/lab/flagship-follow-up-outcomes/justified_but_low_yield.json"
        ),
        entries=entries,
        note=(
            "This report records follow-up loops that looked justified on the way in but should have been blocked before consuming time and budget."
        ),
    )


def build_flagship_underestimated_but_useful_report() -> (
    FlagshipUnderestimatedButUsefulReport
):
    """Build the report for follow-up loops whose usefulness the earlier ranking logic missed."""

    entries = tuple(
        FlagshipUnderestimatedButUsefulReportEntry(
            workflow_family=dossier.workflow_family,
            benchmark_id=dossier.benchmark_id,
            dossier_id=dossier.dossier_id,
            missed_positive_signals=dossier.missed_positive_signals,
            outcome_summary=dossier.outcome_summary,
            note=(
                "The missed positive signals here are the concrete reasons the earlier ranking logic undervalued a loop that later proved decision-useful."
            ),
        )
        for dossier in _dossiers_by_family().values()
        if dossier.looked_weak_initially and dossier.worth_it
    )
    return FlagshipUnderestimatedButUsefulReport(
        report_id="flagship-underestimated-but-useful-report",
        artifact_path=(
            "artifacts/lab/flagship-follow-up-outcomes/underestimated_but_useful.json"
        ),
        entries=entries,
        note=(
            "This report records follow-up loops that looked weak in the initial ranking but later proved worth running once the observed outcome was visible."
        ),
    )
