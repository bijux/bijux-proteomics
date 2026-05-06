# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references import (
    BenchmarkRegistryEntry,
    BenchmarkManifest,
    KnowledgeOntologyDomain,
    KnowledgeOntologyMapping,
    KnowledgeWorkflowFamily,
    WorkflowReferenceBriefing,
    get_benchmark_registry_entry,
    build_workflow_reference_briefing,
    get_benchmark_manifest,
    resolve_ontology_mapping,
)


def test_knowledge_references_root_exposes_curated_reference_anchors() -> None:
    briefing = build_workflow_reference_briefing(KnowledgeWorkflowFamily.DIA)
    manifest = get_benchmark_manifest("benchmark:dia_library_extraction_consistency")
    registry_entry = get_benchmark_registry_entry(
        "benchmark:dia_library_extraction_consistency"
    )
    mapping = resolve_ontology_mapping(KnowledgeOntologyDomain.PTM, "phospho")

    assert isinstance(briefing, WorkflowReferenceBriefing)
    assert isinstance(manifest, BenchmarkManifest)
    assert isinstance(registry_entry, BenchmarkRegistryEntry)
    assert isinstance(mapping, KnowledgeOntologyMapping)
