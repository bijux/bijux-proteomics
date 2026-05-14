# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Blinded recommendation challenge reports for flagship workflow families."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.benchmarks.flagship_challenge_corpora import (
    HoldoutOutcomeState,
    PerturbationReactionState,
    build_blinded_holdout_reports,
    build_perturbation_reports,
)
from bijux_proteomics.benchmarks.workflow_generalization import (
    WorkflowGeneralizationFindingState,
    build_workflow_generalization_reports,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    BenchmarkDisposition,
)
from bijux_proteomics_intelligence.judgment.benchmark_packets import (
    BenchmarkRecommendationPacket,
    build_flagship_benchmark_recommendation_packet_family,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)

__all__ = [
    "BlindedRecommendationChallengeFinding",
    "BlindedRecommendationChallengeReport",
    "BlindedRecommendationRevealState",
    "build_workflow_blinded_recommendation_challenge",
    "list_workflow_blinded_recommendation_challenges",
]


class BlindedRecommendationRevealState(StrEnum):
    """Revealed outcome for one previously blinded recommendation choice."""

    HIT = "hit"
    MISS = "miss"
    OVERCONFIDENT = "overconfident"
    UNDERCONFIDENT = "underconfident"


class BlindedRecommendationChallengeFinding(JsonModel):
    """One blinded recommendation finding after hidden evidence is revealed."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    chosen_disposition: BenchmarkDisposition
    chosen_action_summary: str = Field(..., min_length=1)
    hidden_truth_summary: str = Field(..., min_length=1)
    revealed_outcome: BlindedRecommendationRevealState
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class BlindedRecommendationChallengeReport(JsonModel):
    """Published blinded recommendation challenge for one workflow family."""

    model_config = ConfigDict(extra="forbid")

    challenge_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    benchmark_package_id: str | None = None
    artifact_path: str = Field(..., min_length=1)
    hit_count: int = Field(..., ge=0)
    miss_count: int = Field(..., ge=0)
    overconfidence_count: int = Field(..., ge=0)
    underconfidence_count: int = Field(..., ge=0)
    findings: tuple[BlindedRecommendationChallengeFinding, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


def _packet_by_family() -> dict[KnowledgeWorkflowFamily, BenchmarkRecommendationPacket]:
    return {
        packet.workflow_family: packet
        for packet in build_flagship_benchmark_recommendation_packet_family().packets
        if packet.workflow_family
        in {
            KnowledgeWorkflowFamily.DDA,
            KnowledgeWorkflowFamily.DIA,
            KnowledgeWorkflowFamily.LFQ,
            KnowledgeWorkflowFamily.PTM,
            KnowledgeWorkflowFamily.TARGETED,
        }
    }


_ACTION_SUMMARIES: dict[KnowledgeWorkflowFamily, dict[str, str]] = {
    KnowledgeWorkflowFamily.DDA: {
        "target-decoy-semantics": (
            "Keep DDA follow-up eligible, but only through the bounded adapter-normalized evidence lane."
        ),
        "protein-rollup-stability": (
            "Do not promote DDA protein-level confidence beyond a downgraded paired-package story."
        ),
    },
    KnowledgeWorkflowFamily.DIA: {
        "library-conditioned-precursor-review": (
            "Keep DIA recommendation bounded to library-conditioned precursor review rather than broad vendor-parity language."
        ),
        "protein-absence-overreach": (
            "Do not turn one cleaner DIA package into a stronger protein-absence promotion claim."
        ),
    },
    KnowledgeWorkflowFamily.LFQ: {
        "missingness-visibility": (
            "Recommend LFQ follow-up only while missingness and QC visibility remain explicit in the review."
        ),
        "effect-direction-stability": (
            "Do not promote LFQ effect direction as more stable than the companion cohort evidence supports."
        ),
    },
    KnowledgeWorkflowFamily.PTM: {
        "localization-visibility": (
            "Keep PTM follow-up bounded to localization-aware review rather than broader mechanistic promotion."
        ),
        "targetability-promotion": (
            "Do not turn one tractable PTM packet into a stronger targetability recommendation than the ambiguity-stress package can defend."
        ),
    },
    KnowledgeWorkflowFamily.TARGETED: {
        "calibration-and-transition-visibility": (
            "Keep targeted follow-up visible as a bounded QC and transition review lane before hidden carryover evidence is revealed."
        ),
        "promotion-confidence": (
            "Do not translate one cleaner targeted package into stronger promotion confidence than the carryover-stress package justifies."
        ),
        "interference-carryover-follow-up": (
            "Refuse targeted promotion once hidden interference and carryover pressure collapse the follow-up lane."
        ),
    },
}


def _artifact_path(workflow_family: KnowledgeWorkflowFamily) -> str:
    return (
        "artifacts/intelligence/benchmark-decisions/"
        f"{workflow_family.value}_blinded_recommendation_challenge.json"
    )


def _map_holdout_outcome(
    outcome: HoldoutOutcomeState,
) -> BlindedRecommendationRevealState:
    if outcome is HoldoutOutcomeState.HIT:
        return BlindedRecommendationRevealState.HIT
    if outcome is HoldoutOutcomeState.OVERCONFIDENT:
        return BlindedRecommendationRevealState.OVERCONFIDENT
    if outcome is HoldoutOutcomeState.UNDERCONFIDENT:
        return BlindedRecommendationRevealState.UNDERCONFIDENT
    return BlindedRecommendationRevealState.MISS


def _note_for_outcome(outcome: BlindedRecommendationRevealState) -> str:
    if outcome is BlindedRecommendationRevealState.HIT:
        return "The pre-reveal recommendation stayed inside the claim boundary that the hidden evidence later confirmed."
    if outcome is BlindedRecommendationRevealState.OVERCONFIDENT:
        return "The hidden reveal showed that current recommendation language still carries more confidence than the paired-package evidence earns."
    if outcome is BlindedRecommendationRevealState.UNDERCONFIDENT:
        return "The hidden reveal showed that the current recommendation remained weaker than the evidence would have supported."
    return "The hidden reveal showed that this recommendation should have been refused rather than carried forward as a bounded follow-up."


def _holdout_family_findings(
    workflow_family: KnowledgeWorkflowFamily,
    packet: BenchmarkRecommendationPacket,
) -> tuple[BlindedRecommendationChallengeFinding, ...]:
    holdout = next(
        report
        for report in build_blinded_holdout_reports()
        if report.workflow_family == workflow_family.value
    )
    return tuple(
        BlindedRecommendationChallengeFinding(
            finding_id=(
                f"blinded_recommendation:{workflow_family.value}:{finding.claim_id}"
            ),
            workflow_family=workflow_family,
            chosen_disposition=packet.disposition,
            chosen_action_summary=_ACTION_SUMMARIES[workflow_family][finding.claim_id],
            hidden_truth_summary=finding.hidden_truth_summary,
            revealed_outcome=_map_holdout_outcome(finding.revealed_outcome),
            evidence_refs=finding.frozen_surface_paths,
            note=_note_for_outcome(_map_holdout_outcome(finding.revealed_outcome)),
        )
        for finding in holdout.findings
    )


def _targeted_family_findings(
    packet: BenchmarkRecommendationPacket,
) -> tuple[BlindedRecommendationChallengeFinding, ...]:
    generalization = next(
        report
        for report in build_workflow_generalization_reports()
        if report.workflow_family == KnowledgeWorkflowFamily.TARGETED.value
    )
    perturbation = next(
        report
        for report in build_perturbation_reports()
        if report.workflow_family == KnowledgeWorkflowFamily.TARGETED.value
    )
    findings: list[BlindedRecommendationChallengeFinding] = []
    for finding in generalization.findings:
        if finding.state is WorkflowGeneralizationFindingState.SURVIVES:
            outcome = BlindedRecommendationRevealState.HIT
        elif finding.state is WorkflowGeneralizationFindingState.WEAKENS:
            outcome = BlindedRecommendationRevealState.OVERCONFIDENT
        else:
            outcome = BlindedRecommendationRevealState.MISS
        findings.append(
            BlindedRecommendationChallengeFinding(
                finding_id=(f"blinded_recommendation:targeted:{finding.claim_id}"),
                workflow_family=KnowledgeWorkflowFamily.TARGETED,
                chosen_disposition=packet.disposition,
                chosen_action_summary=_ACTION_SUMMARIES[
                    KnowledgeWorkflowFamily.TARGETED
                ][finding.claim_id],
                hidden_truth_summary=finding.summary,
                revealed_outcome=outcome,
                evidence_refs=finding.evidence_paths,
                note=_note_for_outcome(outcome),
            )
        )
    if perturbation.review_reaction is PerturbationReactionState.COLLAPSES:
        outcome = BlindedRecommendationRevealState.MISS
    elif perturbation.review_reaction is PerturbationReactionState.WEAKENS:
        outcome = BlindedRecommendationRevealState.OVERCONFIDENT
    else:
        outcome = BlindedRecommendationRevealState.HIT
    findings.append(
        BlindedRecommendationChallengeFinding(
            finding_id="blinded_recommendation:targeted:interference-carryover-follow-up",
            workflow_family=KnowledgeWorkflowFamily.TARGETED,
            chosen_disposition=packet.disposition,
            chosen_action_summary=_ACTION_SUMMARIES[KnowledgeWorkflowFamily.TARGETED][
                "interference-carryover-follow-up"
            ],
            hidden_truth_summary=perturbation.note,
            revealed_outcome=outcome,
            evidence_refs=perturbation.evidence_paths,
            note=_note_for_outcome(outcome),
        )
    )
    return tuple(findings)


def build_workflow_blinded_recommendation_challenge(
    workflow_family: KnowledgeWorkflowFamily,
) -> BlindedRecommendationChallengeReport:
    """Build the blinded recommendation challenge for one flagship family."""

    if workflow_family not in _packet_by_family():
        raise ValueError(
            "blinded recommendation challenges currently cover "
            "dda, dia, lfq, ptm, and targeted"
        )
    packet = _packet_by_family()[workflow_family]
    if workflow_family is KnowledgeWorkflowFamily.TARGETED:
        findings = _targeted_family_findings(packet)
    else:
        findings = _holdout_family_findings(workflow_family, packet)
    return BlindedRecommendationChallengeReport(
        challenge_id=f"blinded-recommendation-challenge:{workflow_family.value}",
        workflow_family=workflow_family,
        benchmark_id=packet.benchmark_id,
        benchmark_package_id=packet.benchmark_package_id,
        artifact_path=_artifact_path(workflow_family),
        hit_count=sum(
            finding.revealed_outcome is BlindedRecommendationRevealState.HIT
            for finding in findings
        ),
        miss_count=sum(
            finding.revealed_outcome is BlindedRecommendationRevealState.MISS
            for finding in findings
        ),
        overconfidence_count=sum(
            finding.revealed_outcome is BlindedRecommendationRevealState.OVERCONFIDENT
            for finding in findings
        ),
        underconfidence_count=sum(
            finding.revealed_outcome is BlindedRecommendationRevealState.UNDERCONFIDENT
            for finding in findings
        ),
        findings=findings,
        note=(
            "This report freezes the current intelligence recommendation posture first "
            "and then records whether hidden companion-package or perturbation evidence "
            "shows a hit, miss, overconfidence, or underconfidence outcome."
        ),
    )


def list_workflow_blinded_recommendation_challenges() -> tuple[
    BlindedRecommendationChallengeReport, ...
]:
    """Return blinded recommendation challenges across shipped flagship families."""

    return tuple(
        build_workflow_blinded_recommendation_challenge(workflow_family)
        for workflow_family in (
            KnowledgeWorkflowFamily.DDA,
            KnowledgeWorkflowFamily.DIA,
            KnowledgeWorkflowFamily.LFQ,
            KnowledgeWorkflowFamily.PTM,
            KnowledgeWorkflowFamily.TARGETED,
        )
    )
