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
from bijux_proteomics_knowledge.references.workflows.evidence_sufficiency import (
    WorkflowEvidenceSufficiencyRubric,
    build_workflow_evidence_sufficiency_rubric,
)
from bijux_proteomics_knowledge.references.workflows.knowledge_deficits import (
    WorkflowKnowledgeDeficitReport,
    build_workflow_knowledge_deficit_report,
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
    literature_matrix: WorkflowLiteratureMatrix
    contradiction_dossier: WorkflowContradictionDossier
    evidence_sufficiency_rubric: WorkflowEvidenceSufficiencyRubric
    deficit_report: WorkflowKnowledgeDeficitReport
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
    literature_matrix = build_workflow_literature_matrix(workflow_family)
    contradiction_dossier = build_workflow_contradiction_dossier(workflow_family)
    sufficiency_rubric = build_workflow_evidence_sufficiency_rubric(workflow_family)
    deficit_report = build_workflow_knowledge_deficit_report(workflow_family)
    reading_sequence = (
        f"start with {manifest.benchmark_id} to see the benchmark package and its current claim scope",
        f"read {literature_matrix.entries[0].entry_id} first to understand the strongest literature-backed theme",
        f"inspect {contradiction_dossier.scenarios[0].scenario_id} before trusting any stronger workflow claim",
        "use the evidence sufficiency rubric to see which trust tier is currently earned and which tiers are still blocked",
        "finish with the deficit report to see what public data, comparator, literature, and runtime proof still need to be added",
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
        literature_matrix=literature_matrix,
        contradiction_dossier=contradiction_dossier,
        evidence_sufficiency_rubric=sufficiency_rubric,
        deficit_report=deficit_report,
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
