# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated public entrypoints for grounded knowledge references."""

from __future__ import annotations

from bijux_proteomics_knowledge.references.grounding.contexts import (
    ScientificContextEntry,
)
from bijux_proteomics_knowledge.references.grounding.ontologies import (
    KnowledgeOntologyDomain,
    KnowledgeOntologyMapping,
    resolve_ontology_mapping,
)
from bijux_proteomics_knowledge.references.grounding.rules import (
    ScientificRuleReference,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkEvidenceTier,
    BenchmarkManifest,
    BenchmarkPackageArtifact,
    BenchmarkPackageArtifactKind,
    BenchmarkReproductionStep,
    KnowledgeWorkflowFamily,
    WorkflowBenchmarkPackage,
)
from bijux_proteomics_knowledge.references.workflows.briefings import (
    WorkflowReferenceBriefing,
    build_workflow_reference_briefing,
)
from bijux_proteomics_knowledge.references.workflows.comparators import (
    ProteomicsComparatorTool,
    WorkflowComparatorMatrixEntry,
    WorkflowComparatorMatrixReport,
    WorkflowComparatorPath,
    WorkflowComparatorToolStatus,
    build_workflow_comparator_matrix,
    get_workflow_comparator_path,
    list_workflow_comparator_paths,
)
from bijux_proteomics_knowledge.references.workflows.lookups import (
    get_benchmark_manifest,
    get_benchmark_package,
    get_benchmark_registry_entry,
    list_benchmark_registry_entries,
)
from bijux_proteomics_knowledge.references.workflows.registry import (
    BenchmarkAuthorityAssessment,
    BenchmarkAuthorityStatus,
    BenchmarkRegistryEntry,
    BenchmarkRegistryReport,
    assess_benchmark_authority,
    build_benchmark_registry,
)

__all__ = [
    "BenchmarkAuthorityAssessment",
    "BenchmarkAuthorityStatus",
    "BenchmarkEvidenceTier",
    "BenchmarkManifest",
    "BenchmarkPackageArtifact",
    "BenchmarkPackageArtifactKind",
    "BenchmarkReproductionStep",
    "BenchmarkRegistryEntry",
    "BenchmarkRegistryReport",
    "KnowledgeOntologyDomain",
    "KnowledgeOntologyMapping",
    "KnowledgeWorkflowFamily",
    "ProteomicsComparatorTool",
    "ScientificContextEntry",
    "ScientificRuleReference",
    "WorkflowBenchmarkPackage",
    "WorkflowComparatorMatrixEntry",
    "WorkflowComparatorMatrixReport",
    "WorkflowComparatorPath",
    "WorkflowComparatorToolStatus",
    "WorkflowReferenceBriefing",
    "assess_benchmark_authority",
    "build_benchmark_registry",
    "build_workflow_comparator_matrix",
    "build_workflow_reference_briefing",
    "get_benchmark_manifest",
    "get_benchmark_package",
    "get_benchmark_registry_entry",
    "get_workflow_comparator_path",
    "list_benchmark_registry_entries",
    "list_workflow_comparator_paths",
    "resolve_ontology_mapping",
]
