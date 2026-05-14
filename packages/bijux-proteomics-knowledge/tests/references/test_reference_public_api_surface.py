# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references import (
    BenchmarkManifest,
    KnowledgeOntologyDomain,
    KnowledgeOntologyMapping,
    KnowledgeWorkflowFamily,
    WorkflowReferenceBriefing,
    build_workflow_reference_briefing,
    get_benchmark_manifest,
    resolve_ontology_mapping,
)


def test_knowledge_references_root_exposes_curated_reference_anchors() -> None:
    briefing = build_workflow_reference_briefing(KnowledgeWorkflowFamily.DIA)
    manifest = get_benchmark_manifest("benchmark:dia_library_extraction_consistency")
    mapping = resolve_ontology_mapping(KnowledgeOntologyDomain.PTM, "phospho")

    assert isinstance(briefing, WorkflowReferenceBriefing)
    assert isinstance(manifest, BenchmarkManifest)
    assert isinstance(mapping, KnowledgeOntologyMapping)
