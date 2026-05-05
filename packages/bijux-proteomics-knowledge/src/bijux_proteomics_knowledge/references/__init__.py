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
from bijux_proteomics_knowledge.references.corpora import (
    CorpusManifest,
    DEFAULT_CORPUS_MANIFESTS,
    KnowledgeCorpusSourceKind,
)
from bijux_proteomics_knowledge.references.ontologies import (
    DEFAULT_ONTOLOGY_MAPPINGS,
    KnowledgeOntologyDomain,
    KnowledgeOntologyMapping,
    resolve_ontology_mapping,
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
    get_ontology_mapping,
    get_scientific_rule,
    list_benchmark_manifests,
    list_citations,
    list_corpus_manifests,
    list_ontology_mappings,
    list_scientific_rules,
)

__all__ = [
    "BenchmarkManifest",
    "CitationRecord",
    "CitationSourceKind",
    "CorpusManifest",
    "DEFAULT_BENCHMARK_MANIFESTS",
    "DEFAULT_CITATION_REGISTRY",
    "DEFAULT_CORPUS_MANIFESTS",
    "DEFAULT_ONTOLOGY_MAPPINGS",
    "DEFAULT_SCIENTIFIC_RULE_REFERENCES",
    "KnowledgeCorpusSourceKind",
    "KnowledgeOntologyDomain",
    "KnowledgeOntologyMapping",
    "KnowledgeRuleDomain",
    "KnowledgeWorkflowFamily",
    "ScientificRuleReference",
    "get_benchmark_manifest",
    "get_citation",
    "get_corpus_manifest",
    "get_ontology_mapping",
    "get_scientific_rule",
    "list_benchmark_manifests",
    "list_citations",
    "list_corpus_manifests",
    "list_ontology_mappings",
    "list_scientific_rules",
    "resolve_ontology_mapping",
]
