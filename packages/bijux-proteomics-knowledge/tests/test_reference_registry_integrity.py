# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from bijux_proteomics_knowledge.references.benchmarks import (
    BenchmarkManifest,
    DEFAULT_BENCHMARK_MANIFESTS,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.citations import (
    CitationSourceKind,
    DEFAULT_CITATION_REGISTRY,
)
from bijux_proteomics_knowledge.references.corpora import (
    CorpusManifest,
    DEFAULT_CORPUS_MANIFESTS,
    KnowledgeCorpusSourceKind,
)
from bijux_proteomics_knowledge.references.rules import (
    DEFAULT_SCIENTIFIC_RULE_REFERENCES,
    KnowledgeRuleDomain,
    ScientificRuleReference,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_scientific_rules_require_references_and_benchmark_rationale() -> None:
    with pytest.raises(ValidationError):
        ScientificRuleReference(
            rule_id="rule:missing_references",
            domain=KnowledgeRuleDomain.FDR_CAVEAT,
            title="Missing references",
            rule_statement="This should fail because the registry must keep references explicit.",
            citation_ids=(),
            benchmark_ids=("benchmark:dda_search_reproducibility",),
            benchmark_rationale="Explicit benchmark rationale still exists here.",
        )
    with pytest.raises(ValidationError):
        ScientificRuleReference(
            rule_id="rule:missing_benchmark_context",
            domain=KnowledgeRuleDomain.FDR_CAVEAT,
            title="Missing benchmark context",
            rule_statement="This should fail because benchmark rationale is required.",
            citation_ids=("citation:target_decoy_2007",),
            benchmark_ids=(),
            benchmark_rationale="",
        )


def test_scientific_rule_registry_links_only_known_references() -> None:
    citation_ids = {citation.citation_id for citation in DEFAULT_CITATION_REGISTRY}
    benchmark_ids = {manifest.benchmark_id for manifest in DEFAULT_BENCHMARK_MANIFESTS}

    for rule in DEFAULT_SCIENTIFIC_RULE_REFERENCES:
        assert set(rule.citation_ids).issubset(citation_ids)
        assert set(rule.benchmark_ids).issubset(benchmark_ids)
        assert rule.benchmark_rationale


def test_benchmark_manifests_require_reproduction_metadata() -> None:
    with pytest.raises(ValidationError):
        BenchmarkManifest(
            benchmark_id="benchmark:missing_reproduction_metadata",
            workflow_family=KnowledgeWorkflowFamily.DIA,
            title="Missing reproduction metadata",
            scientific_focus="This should fail because reproduction inputs are incomplete.",
            dataset_id="dataset:missing_reproduction_metadata",
            dataset_locator="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_report.tsv",
            acquisition_mode="data-independent acquisition",
            success_metric="Not enough structure for a reproducible claim.",
            result_claim="Incomplete manifests should not validate.",
            primary_citation_ids=("citation:swath_2012",),
            corpus_ids=("corpus:search_adapter_fixture_suite",),
            benchmark_rationale="A rationale exists, but reproduction requirements are missing.",
            instrument_profiles=("Orbitrap",),
            reproduction_requirements=(),
            comparison_notes=("This benchmark still needs comparison notes.",),
            exclusion_notes=("This benchmark still needs explicit exclusions.",),
            weakness_notes=("This benchmark still needs explicit weaknesses.",),
            failure_mode_notes=("This benchmark still needs explicit failure modes.",),
        )


def test_benchmark_registry_carries_reproducible_claim_context() -> None:
    corpus_ids = {corpus.corpus_id for corpus in DEFAULT_CORPUS_MANIFESTS}
    citation_ids = {citation.citation_id for citation in DEFAULT_CITATION_REGISTRY}

    for manifest in DEFAULT_BENCHMARK_MANIFESTS:
        assert set(manifest.corpus_ids).issubset(corpus_ids)
        assert set(manifest.primary_citation_ids).issubset(citation_ids)
        assert len(manifest.reproduction_requirements) >= 3
        assert manifest.success_metric
        assert manifest.result_claim
        assert manifest.exclusion_notes
        assert manifest.weakness_notes
        assert manifest.failure_mode_notes


def test_corpus_manifests_distinguish_bundled_fixtures_from_external_references() -> (
    None
):
    bundled = {
        corpus.corpus_id
        for corpus in DEFAULT_CORPUS_MANIFESTS
        if corpus.source_kind is KnowledgeCorpusSourceKind.BUNDLED_FIXTURE
    }
    external = {
        corpus.corpus_id
        for corpus in DEFAULT_CORPUS_MANIFESTS
        if corpus.source_kind is KnowledgeCorpusSourceKind.EXTERNAL_REFERENCE
    }

    assert bundled
    assert external
    assert bundled.isdisjoint(external)

    for corpus in DEFAULT_CORPUS_MANIFESTS:
        if corpus.source_kind is KnowledgeCorpusSourceKind.BUNDLED_FIXTURE:
            assert corpus.repo_relative_path is not None
            assert corpus.reference_locator is None
            assert corpus.reference_accession is None
            assert (REPO_ROOT / corpus.repo_relative_path).exists()
        else:
            assert corpus.repo_relative_path is None
            assert corpus.reference_locator is not None
            assert corpus.reference_accession is not None
            assert corpus.citation_ids


def test_invalid_corpus_source_shapes_fail_validation() -> None:
    with pytest.raises(ValidationError):
        CorpusManifest(
            corpus_id="corpus:invalid_bundled_fixture",
            display_name="Invalid bundled fixture",
            source_kind=KnowledgeCorpusSourceKind.BUNDLED_FIXTURE,
            format_family="tsv",
            scientific_scope="This should fail because bundled fixtures cannot point outward.",
            repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/quant",
            reference_locator="https://example.org/not_allowed",
        )
    with pytest.raises(ValidationError):
        CorpusManifest(
            corpus_id="corpus:invalid_external_reference",
            display_name="Invalid external reference",
            source_kind=KnowledgeCorpusSourceKind.EXTERNAL_REFERENCE,
            format_family="journal_article",
            scientific_scope="This should fail because external references need citations.",
            reference_locator="https://example.org/reference",
        )


def test_citation_registry_retains_scientific_source_variety() -> None:
    source_kinds = {citation.source_kind for citation in DEFAULT_CITATION_REGISTRY}

    assert {
        CitationSourceKind.DATABASE,
        CitationSourceKind.ONTOLOGY,
        CitationSourceKind.METHOD,
        CitationSourceKind.REVIEW,
    }.issubset(source_kinds)
