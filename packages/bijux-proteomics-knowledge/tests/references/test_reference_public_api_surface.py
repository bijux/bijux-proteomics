# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references import (
    BenchmarkComparatorFailureReport,
    BenchmarkManifest,
    BenchmarkRegistryEntry,
    KnowledgeDeficitSeverity,
    KnowledgeOntologyDomain,
    KnowledgeOntologyMapping,
    KnowledgeWorkflowFamily,
    WorkflowBenchmarkPackage,
    WorkflowComparatorMatrixReport,
    WorkflowContradictionDossier,
    WorkflowEvidenceSufficiencyRubric,
    WorkflowLiteratureMatrix,
    WorkflowReferenceBriefing,
    WorkflowScientificReadingPack,
    build_benchmark_comparator_failure_report,
    build_workflow_comparator_matrix,
    build_workflow_reference_briefing,
    get_benchmark_manifest,
    get_benchmark_package,
    get_benchmark_registry_entry,
    get_workflow_contradiction_dossier,
    get_workflow_evidence_sufficiency_rubric,
    get_workflow_knowledge_deficit_report,
    get_workflow_literature_matrix,
    get_workflow_scientific_reading_pack,
    resolve_ontology_mapping,
)


def test_knowledge_references_root_exposes_curated_reference_anchors() -> None:
    briefing = build_workflow_reference_briefing(KnowledgeWorkflowFamily.DIA)
    manifest = get_benchmark_manifest("benchmark:dia_library_extraction_consistency")
    package = get_benchmark_package("benchmark:dia_library_extraction_consistency")
    registry_entry = get_benchmark_registry_entry(
        "benchmark:dia_library_extraction_consistency"
    )
    comparator_failures = build_benchmark_comparator_failure_report(
        workflow_family=KnowledgeWorkflowFamily.DIA
    )
    comparator_matrix = build_workflow_comparator_matrix(
        workflow_family=KnowledgeWorkflowFamily.DIA
    )
    literature_matrix = get_workflow_literature_matrix(KnowledgeWorkflowFamily.DIA)
    contradiction_dossier = get_workflow_contradiction_dossier(
        KnowledgeWorkflowFamily.DIA
    )
    sufficiency_rubric = get_workflow_evidence_sufficiency_rubric(
        KnowledgeWorkflowFamily.DIA
    )
    deficit_report = get_workflow_knowledge_deficit_report(
        KnowledgeWorkflowFamily.DIA
    )
    reading_pack = get_workflow_scientific_reading_pack(KnowledgeWorkflowFamily.DIA)
    mapping = resolve_ontology_mapping(KnowledgeOntologyDomain.PTM, "phospho")

    assert isinstance(briefing, WorkflowReferenceBriefing)
    assert isinstance(manifest, BenchmarkManifest)
    assert isinstance(package, WorkflowBenchmarkPackage)
    assert isinstance(registry_entry, BenchmarkRegistryEntry)
    assert isinstance(comparator_failures, BenchmarkComparatorFailureReport)
    assert isinstance(comparator_matrix, WorkflowComparatorMatrixReport)
    assert isinstance(literature_matrix, WorkflowLiteratureMatrix)
    assert isinstance(contradiction_dossier, WorkflowContradictionDossier)
    assert isinstance(sufficiency_rubric, WorkflowEvidenceSufficiencyRubric)
    assert deficit_report.highest_severity in set(KnowledgeDeficitSeverity)
    assert isinstance(reading_pack, WorkflowScientificReadingPack)
    assert isinstance(mapping, KnowledgeOntologyMapping)
