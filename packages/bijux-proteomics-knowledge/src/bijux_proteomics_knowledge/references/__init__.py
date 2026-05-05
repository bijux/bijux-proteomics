# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated scientific reference surfaces owned by the knowledge package."""

from __future__ import annotations

from bijux_proteomics_knowledge.references.citations import (
    CitationRecord,
    CitationSourceKind,
    DEFAULT_CITATION_REGISTRY,
)
from bijux_proteomics_knowledge.references.benchmarks import (
    BenchmarkManifest,
    DEFAULT_BENCHMARK_MANIFESTS,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.briefings import (
    WorkflowReferenceBriefing,
    build_workflow_reference_briefing,
    list_workflow_reference_briefings,
)
from bijux_proteomics_knowledge.references.corpora import (
    CorpusManifest,
    DEFAULT_CORPUS_MANIFESTS,
    KnowledgeCorpusSourceKind,
)
from bijux_proteomics_knowledge.references.contexts import (
    DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES,
    KnowledgeContextDomain,
    ScientificContextEntry,
)
from bijux_proteomics_knowledge.references.literature import (
    DEFAULT_LITERATURE_GROUPS,
    LiteratureFocusArea,
    LiteratureGroup,
)
from bijux_proteomics_knowledge.references.narratives import (
    DEFAULT_WORKFLOW_NARRATIVES,
    WorkflowNarrative,
    WorkflowNarrativeKind,
)
from bijux_proteomics_knowledge.references.ontologies import (
    DEFAULT_ONTOLOGY_MAPPINGS,
    KnowledgeOntologyDomain,
    KnowledgeOntologyMapping,
    resolve_ontology_mapping,
)
from bijux_proteomics_knowledge.references.problems import (
    DEFAULT_KNOWN_PROBLEM_REGISTRY,
    KnowledgeProblemKind,
    KnownProblemRegistryEntry,
)
from bijux_proteomics_knowledge.references.rules import (
    DEFAULT_SCIENTIFIC_RULE_REFERENCES,
    KnowledgeRuleDomain,
    ScientificRuleReference,
)
from bijux_proteomics_knowledge.references.queries import (
    get_benchmark_manifest,
    get_citation,
    get_corpus_manifest,
    get_known_problem,
    get_literature_group,
    get_ontology_mapping,
    get_scientific_context,
    get_scientific_rule,
    get_workflow_narrative,
    list_benchmark_manifests,
    list_citations,
    list_corpus_manifests,
    list_known_problems,
    list_literature_groups,
    list_ontology_mappings,
    list_scientific_context,
    list_scientific_rules,
    list_workflow_narratives,
)

__all__ = [
    "BenchmarkManifest",
    "CitationRecord",
    "CitationSourceKind",
    "CorpusManifest",
    "DEFAULT_BENCHMARK_MANIFESTS",
    "DEFAULT_CITATION_REGISTRY",
    "DEFAULT_CORPUS_MANIFESTS",
    "DEFAULT_KNOWN_PROBLEM_REGISTRY",
    "DEFAULT_LITERATURE_GROUPS",
    "DEFAULT_ONTOLOGY_MAPPINGS",
    "DEFAULT_WORKFLOW_NARRATIVES",
    "DEFAULT_SCIENTIFIC_RULE_REFERENCES",
    "DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES",
    "KnowledgeContextDomain",
    "KnowledgeCorpusSourceKind",
    "KnowledgeOntologyDomain",
    "KnowledgeOntologyMapping",
    "KnowledgeProblemKind",
    "KnowledgeRuleDomain",
    "KnowledgeWorkflowFamily",
    "KnownProblemRegistryEntry",
    "LiteratureFocusArea",
    "LiteratureGroup",
    "ScientificContextEntry",
    "ScientificRuleReference",
    "WorkflowReferenceBriefing",
    "WorkflowNarrative",
    "WorkflowNarrativeKind",
    "build_workflow_reference_briefing",
    "get_benchmark_manifest",
    "get_citation",
    "get_corpus_manifest",
    "get_known_problem",
    "get_literature_group",
    "get_ontology_mapping",
    "get_scientific_context",
    "get_scientific_rule",
    "get_workflow_narrative",
    "list_known_problems",
    "list_literature_groups",
    "list_benchmark_manifests",
    "list_citations",
    "list_corpus_manifests",
    "list_ontology_mappings",
    "list_scientific_context",
    "list_scientific_rules",
    "list_workflow_narratives",
    "list_workflow_reference_briefings",
    "resolve_ontology_mapping",
]
