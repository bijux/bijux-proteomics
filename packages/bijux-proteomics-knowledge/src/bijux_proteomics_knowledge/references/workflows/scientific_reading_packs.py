# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Outsider-readable scientific reading packs for workflow benchmark families."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.contradiction_dossiers import (
    WorkflowContradictionDossier,
    build_workflow_contradiction_dossier,
)
from bijux_proteomics_knowledge.references.workflows.contradiction_triage import (
    WorkflowContradictionTriageReport,
    build_workflow_contradiction_triage_report,
)
from bijux_proteomics_knowledge.references.workflows.evidence_sufficiency import (
    WorkflowEvidenceSufficiencyRubric,
    build_workflow_evidence_sufficiency_rubric,
)
from bijux_proteomics_knowledge.references.workflows.knowledge_deficits import (
    WorkflowKnowledgeDeficitReport,
    build_workflow_knowledge_deficit_report,
)
from bijux_proteomics_knowledge.references.workflows.claim_grounding import (
    WorkflowClaimCitationTable,
    WorkflowUnsupportedClaimLedger,
    build_workflow_claim_citation_table,
    build_workflow_unsupported_claim_ledger,
)
from bijux_proteomics_knowledge.references.workflows.literature_audits import (
    WorkflowBibliographyExport,
    WorkflowLiteratureFreshnessAudit,
    build_workflow_bibliography_export,
    build_workflow_literature_freshness_audit,
)
from bijux_proteomics_knowledge.references.workflows.literature_matrices import (
    WorkflowLiteratureMatrix,
    build_workflow_literature_matrix,
)
from bijux_proteomics_knowledge.references.workflows.reference_support import (
    get_benchmark_manifest_for_family,
    get_citation_record,
    get_workflow_reference_briefing_for_family,
)


class WorkflowScientificReadingPack(JsonModel):
    """One outsider-readable scientific reading pack for a workflow family."""

    model_config = ConfigDict(extra="forbid")

    pack_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    benchmark_title: str = Field(..., min_length=1)
    benchmark_claim_scope: tuple[str, ...] = Field(default_factory=tuple)
    claim_citation_table: WorkflowClaimCitationTable
    literature_matrix: WorkflowLiteratureMatrix
    literature_freshness_audit: WorkflowLiteratureFreshnessAudit
    bibliography_export: WorkflowBibliographyExport
    contradiction_dossier: WorkflowContradictionDossier
    contradiction_triage: WorkflowContradictionTriageReport
    evidence_sufficiency_rubric: WorkflowEvidenceSufficiencyRubric
    deficit_report: WorkflowKnowledgeDeficitReport
    unsupported_claim_ledger: WorkflowUnsupportedClaimLedger
    reading_sequence: tuple[str, ...] = Field(default_factory=tuple)
    citation_digest: tuple[str, ...] = Field(default_factory=tuple)
    outsider_questions: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def _citation_digest(workflow_family: KnowledgeWorkflowFamily) -> tuple[str, ...]:
    briefing = get_workflow_reference_briefing_for_family(workflow_family)
    citation_ids = {
        citation_id
        for group in briefing.literature_groups
        for citation_id in group.citation_ids
    }
    return tuple(
        f"{record.citation_id}: {record.title} ({record.publication_year})"
        for record in (
            get_citation_record(citation_id) for citation_id in sorted(citation_ids)
        )
    )


def build_workflow_scientific_reading_pack(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowScientificReadingPack:
    """Build the outsider-readable scientific reading pack for one family."""

    manifest = get_benchmark_manifest_for_family(workflow_family)
    claim_citation_table = build_workflow_claim_citation_table(workflow_family)
    literature_matrix = build_workflow_literature_matrix(workflow_family)
    literature_freshness_audit = build_workflow_literature_freshness_audit(
        workflow_family
    )
    bibliography_export = build_workflow_bibliography_export(workflow_family)
    contradiction_dossier = build_workflow_contradiction_dossier(workflow_family)
    contradiction_triage = build_workflow_contradiction_triage_report(workflow_family)
    sufficiency_rubric = build_workflow_evidence_sufficiency_rubric(workflow_family)
    deficit_report = build_workflow_knowledge_deficit_report(workflow_family)
    unsupported_claim_ledger = build_workflow_unsupported_claim_ledger(workflow_family)
    reading_sequence = (
        f"start with {manifest.benchmark_id} to see the benchmark package and its current claim scope",
        f"read {claim_citation_table.entries[0].entry_id} to see how the public trust language is grounded",
        f"read {literature_matrix.entries[0].entry_id} first to understand the strongest literature-backed theme",
        f"check {literature_freshness_audit.entries[0].entry_id} before treating the literature base as current by default",
        f"inspect {contradiction_dossier.scenarios[0].scenario_id} before trusting any stronger workflow claim",
        f"rank the main disagreement via {contradiction_triage.entries[0].entry_id} before widening any language",
        "use the evidence sufficiency rubric to see which trust tier is currently earned and which tiers are still blocked",
        "finish with the deficit report and unsupported-claim ledger to see what public data, comparator, literature, runtime, and narrative proof still need to be added",
    )
    outsider_questions = tuple(
        scenario.recommended_hold_reason
        for scenario in contradiction_dossier.scenarios
    )
    return WorkflowScientificReadingPack(
        pack_id=f"scientific_reading_pack:{workflow_family.value}",
        workflow_family=workflow_family,
        benchmark_id=manifest.benchmark_id,
        benchmark_title=manifest.title,
        benchmark_claim_scope=manifest.supported_repo_claims,
        claim_citation_table=claim_citation_table,
        literature_matrix=literature_matrix,
        literature_freshness_audit=literature_freshness_audit,
        bibliography_export=bibliography_export,
        contradiction_dossier=contradiction_dossier,
        contradiction_triage=contradiction_triage,
        evidence_sufficiency_rubric=sufficiency_rubric,
        deficit_report=deficit_report,
        unsupported_claim_ledger=unsupported_claim_ledger,
        reading_sequence=reading_sequence,
        citation_digest=_citation_digest(workflow_family),
        outsider_questions=outsider_questions,
        note=(
            f"This reading pack is the public scientific base for {workflow_family.value} and should be readable without code-level generosity."
        ),
    )


def list_workflow_scientific_reading_packs() -> tuple[WorkflowScientificReadingPack, ...]:
    """Return outsider-readable scientific reading packs across families."""

    return tuple(
        build_workflow_scientific_reading_pack(workflow_family)
        for workflow_family in KnowledgeWorkflowFamily
    )


__all__ = [
    "WorkflowScientificReadingPack",
    "build_workflow_scientific_reading_pack",
    "list_workflow_scientific_reading_packs",
]
