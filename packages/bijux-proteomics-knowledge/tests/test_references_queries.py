# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references import (
    CitationSourceKind,
    KnowledgeCorpusSourceKind,
    KnowledgeOntologyDomain,
    KnowledgeRuleDomain,
    KnowledgeWorkflowFamily,
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


def test_reference_queries_return_known_registry_entries() -> None:
    assert get_citation("citation:uniprot_2025") is not None
    assert get_ontology_mapping("ptm:phosphorylation") is not None
    assert get_benchmark_manifest("benchmark:dia_library_extraction_consistency") is not None
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
