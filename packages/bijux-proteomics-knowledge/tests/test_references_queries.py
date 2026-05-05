# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.benchmarks import KnowledgeWorkflowFamily
from bijux_proteomics_knowledge.references.citations import CitationSourceKind
from bijux_proteomics_knowledge.references.corpora import KnowledgeCorpusSourceKind
from bijux_proteomics_knowledge.references.ontologies import KnowledgeOntologyDomain
from bijux_proteomics_knowledge.references.registry_queries import (
    get_citation,
    get_corpus_manifest,
    get_ontology_mapping,
    get_scientific_rule,
    list_citations,
    list_corpus_manifests,
    list_ontology_mappings,
    list_scientific_rules,
)
from bijux_proteomics_knowledge.references.workflow_queries import (
    get_benchmark_manifest,
    list_benchmark_manifests,
)
from bijux_proteomics_knowledge.references.rules import KnowledgeRuleDomain


def test_reference_queries_return_known_registry_entries() -> None:
    assert get_citation("citation:uniprot_2025") is not None
    assert get_ontology_mapping("ptm:phosphorylation") is not None
    assert (
        get_benchmark_manifest("benchmark:dia_library_extraction_consistency")
        is not None
    )
    assert get_corpus_manifest("corpus:quant_fixture_suite") is not None
    assert get_scientific_rule("rule:target_decoy_scope") is not None


def test_reference_queries_support_domain_filters() -> None:
    assert all(
        citation.source_kind is CitationSourceKind.METHOD
        for citation in list_citations(source_kind=CitationSourceKind.METHOD)
    )
    assert all(
        mapping.domain is KnowledgeOntologyDomain.PTM
        for mapping in list_ontology_mappings(domain=KnowledgeOntologyDomain.PTM)
    )
    assert all(
        manifest.workflow_family is KnowledgeWorkflowFamily.DIA
        for manifest in list_benchmark_manifests(
            workflow_family=KnowledgeWorkflowFamily.DIA
        )
    )
    assert all(
        corpus.source_kind is KnowledgeCorpusSourceKind.BUNDLED_FIXTURE
        for corpus in list_corpus_manifests(
            source_kind=KnowledgeCorpusSourceKind.BUNDLED_FIXTURE
        )
    )
    assert all(
        rule.domain is KnowledgeRuleDomain.FDR_CAVEAT
        for rule in list_scientific_rules(domain=KnowledgeRuleDomain.FDR_CAVEAT)
    )


def test_reference_queries_return_none_for_unknown_entries() -> None:
    assert get_citation("citation:missing") is None
    assert get_ontology_mapping("ptm:missing") is None
    assert get_benchmark_manifest("benchmark:missing") is None
    assert get_corpus_manifest("corpus:missing") is None
    assert get_scientific_rule("rule:missing") is None
