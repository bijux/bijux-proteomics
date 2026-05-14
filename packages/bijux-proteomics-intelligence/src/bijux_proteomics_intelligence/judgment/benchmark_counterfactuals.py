# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Counterfactual recommendation reports for flagship workflow families."""

from __future__ import annotations

from pydantic import ConfigDict, Field

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
from bijux_proteomics_knowledge.references.workflows.claim_grounding import (
    ScientificClaimSeverity,
    build_workflow_unsupported_claim_ledger,
)
from bijux_proteomics_knowledge.references.workflows.contradiction_triage import (
    ContradictionConsequenceLevel,
    build_workflow_contradiction_triage_report,
)
from bijux_proteomics_knowledge.references.workflows.literature_audits import (
    build_workflow_literature_freshness_audit,
)
from bijux_proteomics_knowledge.references.workflows.reference_support import (
    get_benchmark_manifest_for_family,
)

__all__ = [
    "CounterfactualRecommendationEntry",
    "CounterfactualRecommendationReport",
    "build_counterfactual_recommendation_report",
]


class CounterfactualRecommendationEntry(JsonModel):
    """One family-level recommendation under withheld evidence counterfactuals."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    current_lab_burden: str = Field(..., min_length=1)
    baseline_disposition: BenchmarkDisposition
    without_comparator_disposition: BenchmarkDisposition
    without_literature_disposition: BenchmarkDisposition
    doubled_lab_burden_disposition: BenchmarkDisposition
    comparator_note: str = Field(..., min_length=1)
    literature_note: str = Field(..., min_length=1)
    lab_burden_note: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)


class CounterfactualRecommendationReport(JsonModel):
    """Published counterfactual report across flagship workflow families."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[CounterfactualRecommendationEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


def _packets() -> tuple[BenchmarkRecommendationPacket, ...]:
    return tuple(
        packet
        for packet in build_flagship_benchmark_recommendation_packet_family().packets
        if packet.workflow_family
        in {
            KnowledgeWorkflowFamily.DDA,
            KnowledgeWorkflowFamily.DIA,
            KnowledgeWorkflowFamily.LFQ,
            KnowledgeWorkflowFamily.PTM,
            KnowledgeWorkflowFamily.TARGETED,
        }
    )


def _lab_burden(packet: BenchmarkRecommendationPacket) -> str:
    burden_entry = next(
        item
        for item in packet.operational_implications
        if item.startswith("lab_burden=")
    )
    return burden_entry.split("=", 1)[1]


def _without_comparator(
    packet: BenchmarkRecommendationPacket,
) -> tuple[BenchmarkDisposition, str]:
    if packet.disposition is BenchmarkDisposition.DO_NOT_RECOMMEND:
        return (
            packet.disposition,
            "Comparator evidence is already too thin for recommendation, so removing it changes nothing.",
        )
    return (
        BenchmarkDisposition.DO_NOT_RECOMMEND,
        "Removing comparator evidence collapses the current bounded recommendation because the shipped family still relies on comparator pressure to keep its claim scope honest.",
    )


def _without_literature(
    workflow_family: KnowledgeWorkflowFamily,
    packet: BenchmarkRecommendationPacket,
) -> tuple[BenchmarkDisposition, str]:
    if packet.disposition is BenchmarkDisposition.DO_NOT_RECOMMEND:
        return (
            packet.disposition,
            "Literature support is already too thin to justify recommendation, so removing it changes nothing.",
        )
    freshness = build_workflow_literature_freshness_audit(workflow_family)
    triage = build_workflow_contradiction_triage_report(workflow_family)
    unsupported = build_workflow_unsupported_claim_ledger(workflow_family)
    outdated = any(entry.family_summary_outdated for entry in freshness.entries)
    release_blocking = any(
        entry.consequence_level is ContradictionConsequenceLevel.RELEASE_BLOCKING
        for entry in triage.entries
    )
    severe_unsupported = any(
        entry.scientific_severity
        in {ScientificClaimSeverity.MEDIUM, ScientificClaimSeverity.HIGH}
        for entry in unsupported.entries
    )
    if outdated or release_blocking or severe_unsupported:
        return (
            BenchmarkDisposition.DO_NOT_RECOMMEND,
            "Removing literature evidence collapses the recommendation because the current family still depends on literature freshness and contradiction handling to keep review-grade support scientifically bounded.",
        )
    return (
        packet.disposition,
        "Literature removal would not change the current family disposition under the presently shipped evidence posture.",
    )


def _with_doubled_lab_burden(
    packet: BenchmarkRecommendationPacket,
) -> tuple[BenchmarkDisposition, str]:
    if packet.disposition is BenchmarkDisposition.DO_NOT_RECOMMEND:
        return (
            packet.disposition,
            "Doubling lab burden leaves the family on hold because it is already not worth the spend.",
        )
    current_burden = _lab_burden(packet)
    return (
        (
            BenchmarkDisposition.DO_NOT_RECOMMEND,
            "Doubling lab burden turns the current bounded recommendation into an unjustified spend because the family still sits at review-grade rather than decision-grade evidence.",
        )
        if current_burden in {"medium", "high"}
        else (
            packet.disposition,
            "Lab burden remains low enough that doubling it would not change the current family disposition.",
        )
    )


def build_counterfactual_recommendation_report() -> CounterfactualRecommendationReport:
    """Show how flagship recommendations change under withheld evidence axes."""

    entries: list[CounterfactualRecommendationEntry] = []
    for packet in _packets():
        manifest = get_benchmark_manifest_for_family(packet.workflow_family)
        comparator_disposition, comparator_note = _without_comparator(packet)
        literature_disposition, literature_note = _without_literature(
            packet.workflow_family,
            packet,
        )
        burden_disposition, burden_note = _with_doubled_lab_burden(packet)
        entries.append(
            CounterfactualRecommendationEntry(
                workflow_family=packet.workflow_family,
                benchmark_id=manifest.benchmark_id,
                current_lab_burden=_lab_burden(packet),
                baseline_disposition=packet.disposition,
                without_comparator_disposition=comparator_disposition,
                without_literature_disposition=literature_disposition,
                doubled_lab_burden_disposition=burden_disposition,
                comparator_note=comparator_note,
                literature_note=literature_note,
                lab_burden_note=burden_note,
                evidence_refs=(
                    packet.artifact_path,
                    *packet.comparator_pressure,
                    *packet.operational_implications,
                ),
            )
        )
    return CounterfactualRecommendationReport(
        report_id="flagship-counterfactual-recommendations",
        artifact_path="artifacts/intelligence/benchmark-decisions/counterfactual_recommendations.json",
        entries=tuple(entries),
        note=(
            "This report shows how the current flagship recommendation posture changes "
            "if comparator evidence is removed, literature evidence is removed, or lab "
            "burden doubles."
        ),
    )
