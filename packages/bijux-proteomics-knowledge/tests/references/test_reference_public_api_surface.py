# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references import (
    BenchmarkManifest,
    BenchmarkRegistryEntry,
    KnowledgeOntologyDomain,
    KnowledgeOntologyMapping,
    KnowledgeWorkflowFamily,
    WorkflowBenchmarkPackage,
    WorkflowComparatorMatrixReport,
    WorkflowReferenceBriefing,
    build_workflow_comparator_matrix,
    build_workflow_reference_briefing,
    get_benchmark_manifest,
    get_benchmark_package,
    get_benchmark_registry_entry,
    resolve_ontology_mapping,
)


def test_knowledge_references_root_exposes_curated_reference_anchors() -> None:
    briefing = build_workflow_reference_briefing(KnowledgeWorkflowFamily.DIA)
    manifest = get_benchmark_manifest("benchmark:dia_library_extraction_consistency")
    package = get_benchmark_package("benchmark:dia_library_extraction_consistency")
    registry_entry = get_benchmark_registry_entry(
        "benchmark:dia_library_extraction_consistency"
    )
    comparator_matrix = build_workflow_comparator_matrix(
        workflow_family=KnowledgeWorkflowFamily.DIA
    )
    mapping = resolve_ontology_mapping(KnowledgeOntologyDomain.PTM, "phospho")

    assert isinstance(briefing, WorkflowReferenceBriefing)
    assert isinstance(manifest, BenchmarkManifest)
    assert isinstance(package, WorkflowBenchmarkPackage)
    assert isinstance(registry_entry, BenchmarkRegistryEntry)
    assert isinstance(comparator_matrix, WorkflowComparatorMatrixReport)
    assert isinstance(mapping, KnowledgeOntologyMapping)
