# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Combined consequence-chain surfaces across knowledge, intelligence, and lab."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    BenchmarkDisposition,
)
from bijux_proteomics_intelligence.judgment.benchmark_counterfactuals import (
    CounterfactualRecommendationEntry,
    build_counterfactual_recommendation_report,
)
from bijux_proteomics_intelligence.judgment.benchmark_packets import (
    BenchmarkRecommendationPacket,
    build_flagship_benchmark_recommendation_packet_family,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.contradiction_triage import (
    WorkflowContradictionTriageReport,
    list_workflow_contradiction_triage_reports,
)
from bijux_proteomics_lab.benchmarks.follow_up import (
    FlagshipLabFollowUpPacket,
    FlagshipLabPacketPosture,
    build_flagship_lab_follow_up_packet_family,
)
from bijux_proteomics_lab.benchmarks.outcome_dossiers import (
    FlagshipFollowUpOutcomeDossier,
    FlagshipJustifiedButLowYieldReport,
    FlagshipRecommendationRevisionReportEntry,
    FlagshipUnderestimatedButUsefulReport,
    build_flagship_follow_up_outcome_dossier_family,
    build_flagship_justified_but_low_yield_report,
    build_flagship_recommendation_revision_report,
    build_flagship_underestimated_but_useful_report,
)

__all__ = [
    "LAB_CONSEQUENCE_OUTCOME_LEARNING_PATH",
    "LAB_CONSEQUENCE_REFUSAL_HANDBOOK_PATH",
    "RECOMMENDATION_CHANGE_PATH",
    "RecommendationStrength",
    "WORKFLOW_CONSEQUENCE_MAPS_PATH",
    "WorkflowConsequenceCoherenceIssue",
    "WorkflowConsequenceMap",
    "WorkflowOutcomeLearningLoop",
    "WorkflowRecommendationChange",
    "WorkflowRefusalGuidance",
    "build_workflow_consequence_maps",
    "build_workflow_outcome_learning_loops",
    "build_workflow_recommendation_changes",
    "build_workflow_refusal_guidance_family",
    "validate_workflow_consequence_coherence",
]


WORKFLOW_CONSEQUENCE_MAPS_PATH = (
    REPO_ROOT
    / "docs"
    / "01-bijux-proteomics"
    / "foundation"
    / "workflow-consequence-maps.md"
)
RECOMMENDATION_CHANGE_PATH = (
    REPO_ROOT
    / "docs"
    / "01-bijux-proteomics"
    / "foundation"
    / "what-changed-the-recommendation.md"
)
LAB_CONSEQUENCE_OUTCOME_LEARNING_PATH = (
    REPO_ROOT
    / "docs"
    / "07-bijux-proteomics-lab"
    / "foundation"
    / "outcome-learning-loops.md"
)
LAB_CONSEQUENCE_REFUSAL_HANDBOOK_PATH = (
    REPO_ROOT
    / "docs"
    / "07-bijux-proteomics-lab"
    / "foundation"
    / "workflow-refusal-handbook.md"
)


class RecommendationStrength(StrEnum):
    """Normalized public recommendation ceiling across owner packages."""

    DO_NOT_RECOMMEND = "do_not_recommend"
    RECOMMEND_WITH_DOWNGRADE = "recommend_with_downgrade"
    RECOMMEND = "recommend"


@dataclass(frozen=True)
class WorkflowConsequenceMap:
    """Combined per-family map from contradiction to recommendation to assay burden."""

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str
    knowledge_strength: RecommendationStrength
    intelligence_strength: RecommendationStrength
    lab_strength: RecommendationStrength
    weakest_allowed_strength: RecommendationStrength
    contradiction_summary: str
    contradiction_next_action: str
    recommendation_summary: str
    recommendation_blockers: tuple[str, ...]
    lab_summary: str
    control_demands: tuple[str, ...]
    burden_tradeoffs: tuple[str, ...]
    cost_of_being_wrong: tuple[str, ...]
    evidence_paths: tuple[str, ...]


@dataclass(frozen=True)
class WorkflowRecommendationChange:
    """One family summary of what changes or collapses the recommendation."""

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str
    current_strength: RecommendationStrength
    without_comparator: RecommendationStrength
    without_literature: RecommendationStrength
    with_doubled_lab_burden: RecommendationStrength
    observed_outcome_strength: RecommendationStrength | None
    primary_change_driver: str
    driver_signals: tuple[str, ...]
    evidence_paths: tuple[str, ...]


@dataclass(frozen=True)
class WorkflowOutcomeLearningLoop:
    """One family learning loop from planned follow-up to revised posture."""

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str
    requested_assay_ids: tuple[str, ...]
    observed_assay_ids: tuple[str, ...]
    matched_assay_ids: tuple[str, ...]
    blocked_assay_ids: tuple[str, ...]
    weakened_assay_ids: tuple[str, ...]
    initial_strength: RecommendationStrength
    revised_strength: RecommendationStrength
    worth_it: bool
    learning_points: tuple[str, ...]
    next_adjustments: tuple[str, ...]
    evidence_paths: tuple[str, ...]


@dataclass(frozen=True)
class WorkflowRefusalGuidance:
    """Per-family guidance for stop, rerun, narrow, or refuse actions."""

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str
    current_strength: RecommendationStrength
    stop_when: tuple[str, ...]
    rerun_when: tuple[str, ...]
    narrow_when: tuple[str, ...]
    refuse_when: tuple[str, ...]
    evidence_paths: tuple[str, ...]


@dataclass(frozen=True)
class WorkflowConsequenceCoherenceIssue:
    """One cross-package consequence mismatch or docs drift."""

    code: str
    detail: str


_WORKFLOW_FAMILIES: tuple[KnowledgeWorkflowFamily, ...] = (
    KnowledgeWorkflowFamily.DDA,
    KnowledgeWorkflowFamily.DIA,
    KnowledgeWorkflowFamily.LFQ,
    KnowledgeWorkflowFamily.MULTIPLEX,
    KnowledgeWorkflowFamily.PTM,
    KnowledgeWorkflowFamily.TARGETED,
)


def _rank(strength: RecommendationStrength) -> int:
    return {
        RecommendationStrength.DO_NOT_RECOMMEND: 0,
        RecommendationStrength.RECOMMEND_WITH_DOWNGRADE: 1,
        RecommendationStrength.RECOMMEND: 2,
    }[strength]


def _minimum(*strengths: RecommendationStrength) -> RecommendationStrength:
    return min(strengths, key=_rank)


def _format_strength(strength: RecommendationStrength) -> str:
    return {
        RecommendationStrength.DO_NOT_RECOMMEND: "do not recommend",
        RecommendationStrength.RECOMMEND_WITH_DOWNGRADE: "recommend only with downgrade",
        RecommendationStrength.RECOMMEND: "recommend",
    }[strength]


def _packet_strength(disposition: BenchmarkDisposition) -> RecommendationStrength:
    return RecommendationStrength(disposition.value)


def _lab_strength(
    packet: FlagshipLabFollowUpPacket | None,
) -> RecommendationStrength:
    if packet is None:
        return RecommendationStrength.DO_NOT_RECOMMEND
    if packet.posture is FlagshipLabPacketPosture.NOT_WORTH_ASSAY:
        return RecommendationStrength.DO_NOT_RECOMMEND
    if packet.posture is FlagshipLabPacketPosture.EXPLORATORY_ONLY:
        return RecommendationStrength.RECOMMEND_WITH_DOWNGRADE
    return RecommendationStrength.RECOMMEND


def _knowledge_strength(
    workflow_family: KnowledgeWorkflowFamily,
    triage: WorkflowContradictionTriageReport,
) -> RecommendationStrength:
    if workflow_family is KnowledgeWorkflowFamily.MULTIPLEX:
        return RecommendationStrength.DO_NOT_RECOMMEND
    if any(
        entry.consequence_level.value == "release_blocking" for entry in triage.entries
    ):
        return RecommendationStrength.RECOMMEND_WITH_DOWNGRADE
    return RecommendationStrength.RECOMMEND


def _counterfactual_by_family() -> dict[
    KnowledgeWorkflowFamily, CounterfactualRecommendationEntry
]:
    report = build_counterfactual_recommendation_report()
    return {entry.workflow_family: entry for entry in report.entries}


def _packet_by_family() -> dict[KnowledgeWorkflowFamily, BenchmarkRecommendationPacket]:
    family = build_flagship_benchmark_recommendation_packet_family()
    return {packet.workflow_family: packet for packet in family.packets}


def _triage_by_family() -> dict[
    KnowledgeWorkflowFamily, WorkflowContradictionTriageReport
]:
    return {
        report.workflow_family: report
        for report in list_workflow_contradiction_triage_reports()
    }


def _lab_packet_by_family() -> dict[KnowledgeWorkflowFamily, FlagshipLabFollowUpPacket]:
    family = build_flagship_lab_follow_up_packet_family()
    return {packet.workflow_family: packet for packet in family.packets}


def _outcome_by_family() -> dict[
    KnowledgeWorkflowFamily, FlagshipFollowUpOutcomeDossier
]:
    family = build_flagship_follow_up_outcome_dossier_family()
    return {dossier.workflow_family: dossier for dossier in family.dossiers}


def _revision_by_family() -> dict[
    KnowledgeWorkflowFamily, FlagshipRecommendationRevisionReportEntry
]:
    report = build_flagship_recommendation_revision_report()
    return {entry.workflow_family: entry for entry in report.entries}


def _low_yield_by_family(
    report: FlagshipJustifiedButLowYieldReport,
) -> dict[KnowledgeWorkflowFamily, tuple[str, ...]]:
    return {
        entry.workflow_family: entry.early_block_signals for entry in report.entries
    }


def _underestimated_by_family(
    report: FlagshipUnderestimatedButUsefulReport,
) -> dict[KnowledgeWorkflowFamily, tuple[str, ...]]:
    return {
        entry.workflow_family: entry.missed_positive_signals for entry in report.entries
    }


def build_workflow_consequence_maps() -> tuple[WorkflowConsequenceMap, ...]:
    """Return cross-package consequence maps across workflow families."""

    triage_by_family = _triage_by_family()
    packet_by_family = _packet_by_family()
    lab_by_family = _lab_packet_by_family()
    outcome_by_family = _outcome_by_family()
    maps: list[WorkflowConsequenceMap] = []
    for workflow_family in _WORKFLOW_FAMILIES:
        triage = triage_by_family[workflow_family]
        packet = packet_by_family[workflow_family]
        lab_packet = lab_by_family.get(workflow_family)
        knowledge_strength = _knowledge_strength(workflow_family, triage)
        intelligence_strength = _packet_strength(packet.disposition)
        lab_strength = _lab_strength(lab_packet)
        weakest = _minimum(knowledge_strength, intelligence_strength, lab_strength)
        contradiction = triage.entries[0]
        lab_summary = (
            "No dedicated lab follow-up packet is published for this family."
            if lab_packet is None
            else (
                f"Lab posture is `{lab_packet.posture.value}` with strategy: "
                f"{lab_packet.suggested_assay_strategy}"
            )
        )
        control_demands = () if lab_packet is None else lab_packet.required_controls
        burden_tradeoffs = (
            () if lab_packet is None else lab_packet.burden_profile.tradeoffs
        )
        cost_of_being_wrong = (
            () if lab_packet is None else lab_packet.expected_failure_modes
        )
        evidence_paths = [
            packet.artifact_path,
            *packet.comparator_pressure,
            triage.entries[0].entry_id,
        ]
        if lab_packet is not None:
            evidence_paths.extend(
                [
                    lab_packet.artifact_path,
                    *lab_packet.required_controls,
                ]
            )
        dossier = outcome_by_family.get(workflow_family)
        if dossier is not None:
            evidence_paths.append(dossier.artifact_path)
        maps.append(
            WorkflowConsequenceMap(
                workflow_family=workflow_family,
                benchmark_id=packet.benchmark_id,
                knowledge_strength=knowledge_strength,
                intelligence_strength=intelligence_strength,
                lab_strength=lab_strength,
                weakest_allowed_strength=weakest,
                contradiction_summary=contradiction.summary,
                contradiction_next_action=contradiction.next_action,
                recommendation_summary=(
                    f"Current recommendation posture is `{packet.disposition.value}`"
                ),
                recommendation_blockers=tuple(
                    dict.fromkeys((*packet.blocker_set, *packet.downgrade_chain))
                ),
                lab_summary=lab_summary,
                control_demands=control_demands,
                burden_tradeoffs=burden_tradeoffs,
                cost_of_being_wrong=cost_of_being_wrong,
                evidence_paths=tuple(dict.fromkeys(evidence_paths)),
            )
        )
    return tuple(maps)


def build_workflow_recommendation_changes() -> tuple[WorkflowRecommendationChange, ...]:
    """Return one per-family summary of what changes the recommendation."""

    counterfactual_by_family = _counterfactual_by_family()
    revision_by_family = _revision_by_family()
    low_yield_by_family = _low_yield_by_family(
        build_flagship_justified_but_low_yield_report()
    )
    underestimated_by_family = _underestimated_by_family(
        build_flagship_underestimated_but_useful_report()
    )
    changes: list[WorkflowRecommendationChange] = []
    for packet in _packet_by_family().values():
        counterfactual = counterfactual_by_family.get(packet.workflow_family)
        revision = revision_by_family.get(packet.workflow_family)
        driver_signals: tuple[str, ...] = ()
        primary_change_driver = (
            "current public recommendation still holds under shipped evidence"
        )
        observed_strength: RecommendationStrength | None = None
        if revision is not None:
            observed_strength = _packet_strength(
                revision.revised_recommendation_disposition
            )
            driver_signals = revision.driver_signals
            primary_change_driver = revision.outcome_summary
        elif packet.workflow_family in low_yield_by_family:
            driver_signals = low_yield_by_family[packet.workflow_family]
            primary_change_driver = "assay spend looked justified at first, but the observed outcome says the family should stop earlier next time"
        elif packet.workflow_family in underestimated_by_family:
            driver_signals = underestimated_by_family[packet.workflow_family]
            primary_change_driver = "the observed outcome proved the loop more useful than the initial ranking expected"
        elif counterfactual is None:
            primary_change_driver = "no public counterfactual report is shipped for this family because recommendation posture is already held below outsider-facing consequence closure"
        changes.append(
            WorkflowRecommendationChange(
                workflow_family=packet.workflow_family,
                benchmark_id=packet.benchmark_id,
                current_strength=_packet_strength(packet.disposition),
                without_comparator=(
                    _packet_strength(counterfactual.without_comparator_disposition)
                    if counterfactual is not None
                    else _packet_strength(packet.disposition)
                ),
                without_literature=(
                    _packet_strength(counterfactual.without_literature_disposition)
                    if counterfactual is not None
                    else _packet_strength(packet.disposition)
                ),
                with_doubled_lab_burden=(
                    _packet_strength(counterfactual.doubled_lab_burden_disposition)
                    if counterfactual is not None
                    else _packet_strength(packet.disposition)
                ),
                observed_outcome_strength=observed_strength,
                primary_change_driver=primary_change_driver,
                driver_signals=driver_signals,
                evidence_paths=tuple(
                    dict.fromkeys(
                        (
                            packet.artifact_path,
                            *(
                                (
                                    counterfactual.comparator_note,
                                    counterfactual.literature_note,
                                    counterfactual.lab_burden_note,
                                )
                                if counterfactual is not None
                                else ()
                            ),
                            *(driver_signals or ()),
                        )
                    )
                ),
            )
        )
    return tuple(
        sorted(
            changes, key=lambda entry: _WORKFLOW_FAMILIES.index(entry.workflow_family)
        )
    )


def build_workflow_outcome_learning_loops() -> tuple[WorkflowOutcomeLearningLoop, ...]:
    """Return per-family learning loops from shipped follow-up outcomes."""

    dossier_by_family = _outcome_by_family()
    loops: list[WorkflowOutcomeLearningLoop] = []
    for workflow_family in _WORKFLOW_FAMILIES:
        dossier = dossier_by_family.get(workflow_family)
        if dossier is None:
            packet = _packet_by_family()[workflow_family]
            loops.append(
                WorkflowOutcomeLearningLoop(
                    workflow_family=workflow_family,
                    benchmark_id=packet.benchmark_id,
                    requested_assay_ids=(),
                    observed_assay_ids=(),
                    matched_assay_ids=(),
                    blocked_assay_ids=(),
                    weakened_assay_ids=(),
                    initial_strength=_packet_strength(packet.disposition),
                    revised_strength=_packet_strength(packet.disposition),
                    worth_it=False,
                    learning_points=(
                        "no shipped requested-versus-observed outcome loop exists for this family yet",
                    ),
                    next_adjustments=(
                        "publish a dedicated downstream lab consequence and observed outcome loop before strengthening recommendation posture",
                    ),
                    evidence_paths=(packet.artifact_path,),
                )
            )
            continue
        next_adjustments = list(dossier.learning_points)
        if dossier.recommendation_changed:
            next_adjustments.append(
                "feed the revised follow-up result back into future recommendation posture instead of keeping the original recommendation sentence unchanged"
            )
        if dossier.blocked_assay_ids:
            next_adjustments.append(
                "treat blocked assays as explicit evidence for narrower or slower future follow-up"
            )
        if dossier.weakened_assay_ids:
            next_adjustments.append(
                "carry weakened assays forward as downgrade evidence rather than as partial confirmation"
            )
        loops.append(
            WorkflowOutcomeLearningLoop(
                workflow_family=dossier.workflow_family,
                benchmark_id=dossier.benchmark_id,
                requested_assay_ids=dossier.requested_assay_ids,
                observed_assay_ids=dossier.observed_assay_ids,
                matched_assay_ids=dossier.matched_assay_ids,
                blocked_assay_ids=dossier.blocked_assay_ids,
                weakened_assay_ids=dossier.weakened_assay_ids,
                initial_strength=_packet_strength(
                    dossier.initial_recommendation_disposition
                ),
                revised_strength=_packet_strength(
                    dossier.revised_recommendation_disposition
                ),
                worth_it=dossier.worth_it,
                learning_points=dossier.learning_points,
                next_adjustments=tuple(dict.fromkeys(next_adjustments)),
                evidence_paths=(
                    dossier.artifact_path,
                    *dossier.promoted_evidence_ids,
                ),
            )
        )
    return tuple(
        sorted(loops, key=lambda entry: _WORKFLOW_FAMILIES.index(entry.workflow_family))
    )


def build_workflow_refusal_guidance_family() -> tuple[WorkflowRefusalGuidance, ...]:
    """Return per-family stop, rerun, narrow, and refuse guidance."""

    triage_by_family = _triage_by_family()
    lab_by_family = _lab_packet_by_family()
    outcome_by_family = _outcome_by_family()
    guidance: list[WorkflowRefusalGuidance] = []
    for packet in _packet_by_family().values():
        triage = triage_by_family[packet.workflow_family]
        lab_packet = lab_by_family.get(packet.workflow_family)
        dossier = outcome_by_family.get(packet.workflow_family)
        stop_when: tuple[str, ...] = ()
        rerun_when = tuple(
            dict.fromkeys((*packet.blocker_set, *packet.downgrade_chain))
        )
        narrow_when: tuple[str, ...] = (
            triage.entries[0].summary,
            triage.entries[0].next_action,
        )
        refuse_when: tuple[str, ...] = ()
        if lab_packet is not None:
            stop_when = tuple(dict.fromkeys(lab_packet.stop_reasons[:3]))
            rerun_when = tuple(
                dict.fromkeys(
                    (
                        *rerun_when,
                        *lab_packet.comparator_pressure[:2],
                        *lab_packet.expected_failure_modes[:2],
                    )
                )
            )
            narrow_when = tuple(
                dict.fromkeys((*narrow_when, *lab_packet.exploratory_boundary[:2]))
            )
            refuse_when = tuple(
                dict.fromkeys(
                    (
                        *lab_packet.stop_reasons[:2],
                        *(
                            "decision-grade condition is not satisfied: "
                            f"{condition}"
                            for condition in lab_packet.decision_grade_boundary[:2]
                        ),
                    )
                )
            )
        if dossier is not None and not dossier.worth_it:
            refuse_when = tuple(
                dict.fromkeys(
                    (
                        *refuse_when,
                        *dossier.early_block_signals[:2],
                        dossier.outcome_summary,
                    )
                )
            )
        if packet.workflow_family is KnowledgeWorkflowFamily.MULTIPLEX:
            refuse_when = (
                "keep multiplex at internal support until the family earns its own outsider review and lab consequence closure",
                triage.entries[0].summary,
            )
        guidance.append(
            WorkflowRefusalGuidance(
                workflow_family=packet.workflow_family,
                benchmark_id=packet.benchmark_id,
                current_strength=_packet_strength(packet.disposition),
                stop_when=stop_when,
                rerun_when=rerun_when,
                narrow_when=narrow_when,
                refuse_when=refuse_when,
                evidence_paths=tuple(
                    dict.fromkeys(
                        (
                            packet.artifact_path,
                            triage.entries[0].entry_id,
                            *(
                                lab_packet.required_controls
                                if lab_packet is not None
                                else ()
                            ),
                            *(() if dossier is None else (dossier.artifact_path,)),
                        )
                    )
                ),
            )
        )
    return tuple(
        sorted(
            guidance, key=lambda entry: _WORKFLOW_FAMILIES.index(entry.workflow_family)
        )
    )


def _contains_all(text: str, required: tuple[str, ...]) -> bool:
    return all(item in text for item in required)


def _section(text: str, workflow_family: KnowledgeWorkflowFamily) -> str:
    marker = f"### `{workflow_family.value}`"
    _, _, tail = text.partition(marker)
    if not tail:
        return ""
    next_marker = "\n### `"
    end = tail.find(next_marker)
    return tail if end == -1 else tail[:end]


def validate_workflow_consequence_coherence(
    repo_root: Path = REPO_ROOT,
) -> tuple[WorkflowConsequenceCoherenceIssue, ...]:
    """Require shared consequence posture across knowledge, intelligence, and lab."""

    issues: list[WorkflowConsequenceCoherenceIssue] = []
    maps = build_workflow_consequence_maps()
    by_family = {entry.workflow_family: entry for entry in maps}

    for entry in maps:
        strengths = {
            entry.knowledge_strength,
            entry.intelligence_strength,
            entry.lab_strength,
        }
        if len(strengths) > 1:
            issues.append(
                WorkflowConsequenceCoherenceIssue(
                    code="cross-package-posture-disagreement",
                    detail=(
                        f"{entry.workflow_family.value} disagrees across knowledge, intelligence, and lab: "
                        f"{entry.knowledge_strength.value}, {entry.intelligence_strength.value}, {entry.lab_strength.value}"
                    ),
                )
            )
        if _rank(entry.intelligence_strength) > _rank(entry.weakest_allowed_strength):
            issues.append(
                WorkflowConsequenceCoherenceIssue(
                    code="recommendation-strength-exceeds-downstream-boundary",
                    detail=(
                        f"{entry.workflow_family.value} intelligence posture "
                        f"{entry.intelligence_strength.value} exceeds weakest downstream boundary "
                        f"{entry.weakest_allowed_strength.value}"
                    ),
                )
            )

    consequence_text = WORKFLOW_CONSEQUENCE_MAPS_PATH.read_text(encoding="utf-8")
    change_text = RECOMMENDATION_CHANGE_PATH.read_text(encoding="utf-8")
    learning_text = LAB_CONSEQUENCE_OUTCOME_LEARNING_PATH.read_text(encoding="utf-8")
    refusal_text = LAB_CONSEQUENCE_REFUSAL_HANDBOOK_PATH.read_text(encoding="utf-8")
    for workflow_family in (
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    ):
        label = f"### `{workflow_family.value}`"
        if label not in consequence_text:
            issues.append(
                WorkflowConsequenceCoherenceIssue(
                    code="missing-consequence-map-family-section",
                    detail=f"{workflow_family.value} is missing from workflow-consequence-maps.md",
                )
            )
        family_section = _section(consequence_text, workflow_family)
        if "decision-grade remains blocked" not in family_section:
            issues.append(
                WorkflowConsequenceCoherenceIssue(
                    code="decision-grade-narrowing-missing",
                    detail=(
                        f"{workflow_family.value} consequence map does not keep decision-grade language explicitly blocked"
                    ),
                )
            )
        if (
            label not in change_text
            or label not in learning_text
            or label not in refusal_text
        ):
            issues.append(
                WorkflowConsequenceCoherenceIssue(
                    code="missing-consequence-doc-route",
                    detail=(
                        f"{workflow_family.value} is missing from one of the shared consequence docs"
                    ),
                )
            )

    for workflow_family, entry in by_family.items():
        expected_line = f"- current strongest allowed posture: `{entry.weakest_allowed_strength.value}`"
        if expected_line not in consequence_text:
            issues.append(
                WorkflowConsequenceCoherenceIssue(
                    code="missing-weakest-posture-line",
                    detail=(
                        f"workflow-consequence-maps.md does not pin the weakest allowed posture for {workflow_family.value}"
                    ),
                )
            )
    return tuple(issues)
