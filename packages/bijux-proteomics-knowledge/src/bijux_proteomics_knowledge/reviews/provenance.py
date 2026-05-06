# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Provenance and reference-disagreement surfaces for review-critical claims."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel

from bijux_proteomics_knowledge.memory.models.claims import EvidenceClaim
from bijux_proteomics_knowledge.memory.models.evidence import EvidenceBundle
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.briefings import (
    WorkflowReferenceBriefing,
    build_workflow_reference_briefing,
)


class ReferenceDisagreementSeverity(StrEnum):
    """Severity of benchmark-versus-literature disagreement pressure."""

    MODERATE = "moderate"
    HIGH = "high"


class CriticalClaimProvenanceLine(JsonModel):
    """One recommendation-critical claim with full reference and evidence lineage."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=1)
    decision_impact: str = Field(..., min_length=1)
    evidence_state: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    contradicting_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    benchmark_id: str = Field(..., min_length=1)
    benchmark_claim: str = Field(..., min_length=1)
    citation_ids: tuple[str, ...] = Field(default_factory=tuple)
    corpus_ids: tuple[str, ...] = Field(default_factory=tuple)
    literature_group_ids: tuple[str, ...] = Field(default_factory=tuple)
    missing_links: tuple[str, ...] = Field(default_factory=tuple)


class ReferenceDisagreementEntry(JsonModel):
    """One first-class disagreement between benchmark support and literature caution."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    literature_group_id: str = Field(..., min_length=1)
    benchmark_position: str = Field(..., min_length=1)
    literature_position: str = Field(..., min_length=1)
    limitation_anchor: str = Field(..., min_length=1)
    severity: ReferenceDisagreementSeverity
    downgrade_reason: str = Field(..., min_length=1)


class ReferenceDisagreementReport(JsonModel):
    """Workflow-level disagreement report spanning benchmark and literature inputs."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    entries: tuple[ReferenceDisagreementEntry, ...] = Field(default_factory=tuple)


def _briefing(workflow_family: KnowledgeWorkflowFamily) -> WorkflowReferenceBriefing:
    return build_workflow_reference_briefing(workflow_family)


def build_critical_claim_provenance_lines(
    bundle: EvidenceBundle,
    claims: list[EvidenceClaim],
    *,
    decision_tag: str,
    workflow_family: KnowledgeWorkflowFamily,
) -> tuple[CriticalClaimProvenanceLine, ...]:
    """Trace recommendation-critical claims to benchmark, citation, corpus, and evidence."""

    briefing = _briefing(workflow_family)
    available_evidence_ids = {record.evidence_id for record in bundle.records}
    lines: list[CriticalClaimProvenanceLine] = []
    for claim in claims:
        claim_evidence_ids = tuple(
            evidence_id
            for evidence_id in claim.evidence_ids
            if evidence_id in available_evidence_ids
        )
        contradicting_ids = tuple(
            evidence_id
            for evidence_id in claim.contradicting_evidence_ids
            if evidence_id in available_evidence_ids
        )
        if not claim_evidence_ids and not contradicting_ids:
            continue
        relevant_ids = {*claim_evidence_ids, *contradicting_ids}
        related_records = [
            record
            for record in bundle.records
            if record.evidence_id in relevant_ids
            and decision_tag in record.decision_tags
        ]
        if not related_records:
            continue
        missing_links: list[str] = []
        if len(claim_evidence_ids) < len(claim.evidence_ids):
            missing_links.append(
                "claim references evidence outside the attached bundle"
            )
        if not briefing.literature_groups:
            missing_links.append("workflow briefing has no linked literature groups")
        lines.append(
            CriticalClaimProvenanceLine(
                claim_id=claim.claim_id,
                statement=claim.statement,
                decision_impact=claim.decision_impact,
                evidence_state=claim.evidence_state.value,
                confidence=round(claim.confidence, 4),
                evidence_ids=claim_evidence_ids,
                contradicting_evidence_ids=contradicting_ids,
                benchmark_id=briefing.benchmark_manifest.benchmark_id,
                benchmark_claim=briefing.evidence_claim.narrative_text,
                citation_ids=briefing.benchmark_manifest.primary_citation_ids,
                corpus_ids=briefing.benchmark_manifest.corpus_ids,
                literature_group_ids=tuple(
                    group.group_id for group in briefing.literature_groups
                ),
                missing_links=tuple(missing_links),
            )
        )
    return tuple(sorted(lines, key=lambda line: line.claim_id))


def build_reference_disagreement_report(
    workflow_family: KnowledgeWorkflowFamily,
) -> ReferenceDisagreementReport:
    """Build first-class disagreement artifacts from benchmark claims and literature caution."""

    briefing = _briefing(workflow_family)
    entries = tuple(
        ReferenceDisagreementEntry(
            benchmark_id=briefing.benchmark_manifest.benchmark_id,
            literature_group_id=group.group_id,
            benchmark_position=briefing.evidence_claim.narrative_text,
            literature_position=group.curation_note,
            limitation_anchor=briefing.limitation.narrative_text,
            severity=(
                ReferenceDisagreementSeverity.HIGH
                if briefing.benchmark_manifest.cross_check_status.value
                == "internal_only"
                else ReferenceDisagreementSeverity.MODERATE
            ),
            downgrade_reason=briefing.scope_limit_notes[0],
        )
        for group in briefing.literature_groups
    )
    return ReferenceDisagreementReport(
        workflow_family=workflow_family,
        entries=entries,
    )


__all__ = [
    "CriticalClaimProvenanceLine",
    "ReferenceDisagreementEntry",
    "ReferenceDisagreementReport",
    "ReferenceDisagreementSeverity",
    "build_critical_claim_provenance_lines",
    "build_reference_disagreement_report",
]
