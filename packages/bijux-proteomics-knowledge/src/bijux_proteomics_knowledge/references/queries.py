# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Read-only query helpers over curated scientific reference registries."""

from __future__ import annotations

from bijux_proteomics_knowledge.references.benchmarks import (
    BenchmarkManifest,
    DEFAULT_BENCHMARK_MANIFESTS,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.citations import (
    CitationRecord,
    CitationSourceKind,
    DEFAULT_CITATION_REGISTRY,
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
)
from bijux_proteomics_knowledge.references.rules import (
    DEFAULT_SCIENTIFIC_RULE_REFERENCES,
    KnowledgeRuleDomain,
    ScientificRuleReference,
)


def list_citations(
    *, source_kind: CitationSourceKind | None = None
) -> tuple[CitationRecord, ...]:
    """Return curated citations, optionally filtered by source kind."""
    if source_kind is None:
        return DEFAULT_CITATION_REGISTRY
    return tuple(
        citation
        for citation in DEFAULT_CITATION_REGISTRY
        if citation.source_kind is source_kind
    )


def get_citation(citation_id: str) -> CitationRecord | None:
    """Return one citation by stable identifier."""
    return next(
        (
            citation
            for citation in DEFAULT_CITATION_REGISTRY
            if citation.citation_id == citation_id
        ),
        None,
    )


def list_ontology_mappings(
    *, domain: KnowledgeOntologyDomain | None = None
) -> tuple[KnowledgeOntologyMapping, ...]:
    """Return curated ontology mappings, optionally filtered by domain."""
    if domain is None:
        return DEFAULT_ONTOLOGY_MAPPINGS
    return tuple(mapping for mapping in DEFAULT_ONTOLOGY_MAPPINGS if mapping.domain is domain)


def get_ontology_mapping(term_id: str) -> KnowledgeOntologyMapping | None:
    """Return one ontology mapping by stable term identifier."""
    return next(
        (mapping for mapping in DEFAULT_ONTOLOGY_MAPPINGS if mapping.term_id == term_id),
        None,
    )


def list_benchmark_manifests(
    *, workflow_family: KnowledgeWorkflowFamily | None = None
) -> tuple[BenchmarkManifest, ...]:
    """Return curated benchmark manifests, optionally filtered by workflow family."""
    if workflow_family is None:
        return DEFAULT_BENCHMARK_MANIFESTS
    return tuple(
        manifest
        for manifest in DEFAULT_BENCHMARK_MANIFESTS
        if manifest.workflow_family is workflow_family
    )


def get_benchmark_manifest(benchmark_id: str) -> BenchmarkManifest | None:
    """Return one benchmark manifest by stable identifier."""
    return next(
        (
            manifest
            for manifest in DEFAULT_BENCHMARK_MANIFESTS
            if manifest.benchmark_id == benchmark_id
        ),
        None,
    )


def list_corpus_manifests(
    *, source_kind: KnowledgeCorpusSourceKind | None = None
) -> tuple[CorpusManifest, ...]:
    """Return curated corpora, optionally filtered by source kind."""
    if source_kind is None:
        return DEFAULT_CORPUS_MANIFESTS
    return tuple(
        corpus for corpus in DEFAULT_CORPUS_MANIFESTS if corpus.source_kind is source_kind
    )


def get_corpus_manifest(corpus_id: str) -> CorpusManifest | None:
    """Return one corpus manifest by stable identifier."""
    return next(
        (corpus for corpus in DEFAULT_CORPUS_MANIFESTS if corpus.corpus_id == corpus_id),
        None,
    )


def list_scientific_rules(
    *, domain: KnowledgeRuleDomain | None = None
) -> tuple[ScientificRuleReference, ...]:
    """Return curated scientific rule mappings, optionally filtered by domain."""
    if domain is None:
        return DEFAULT_SCIENTIFIC_RULE_REFERENCES
    return tuple(
        rule for rule in DEFAULT_SCIENTIFIC_RULE_REFERENCES if rule.domain is domain
    )


def get_scientific_rule(rule_id: str) -> ScientificRuleReference | None:
    """Return one scientific rule mapping by stable identifier."""
    return next(
        (rule for rule in DEFAULT_SCIENTIFIC_RULE_REFERENCES if rule.rule_id == rule_id),
        None,
    )


__all__ = [
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
]
