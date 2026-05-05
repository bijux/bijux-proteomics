# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Read-only query helpers over citation, ontology, and registry surfaces."""

from __future__ import annotations

from bijux_proteomics_knowledge.references.citations import (
    CitationRecord,
    CitationSourceKind,
    DEFAULT_CITATION_REGISTRY,
)
from bijux_proteomics_knowledge.references.contexts import (
    DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES,
    KnowledgeContextDomain,
    ScientificContextEntry,
)
from bijux_proteomics_knowledge.references.corpora import (
    CorpusManifest,
    DEFAULT_CORPUS_MANIFESTS,
    KnowledgeCorpusSourceKind,
)
from bijux_proteomics_knowledge.references.literature import (
    DEFAULT_LITERATURE_GROUPS,
    LiteratureFocusArea,
    LiteratureGroup,
)
from bijux_proteomics_knowledge.references.ontologies import (
    DEFAULT_ONTOLOGY_MAPPINGS,
    KnowledgeOntologyDomain,
    KnowledgeOntologyMapping,
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
    return tuple(
        mapping for mapping in DEFAULT_ONTOLOGY_MAPPINGS if mapping.domain is domain
    )


def get_ontology_mapping(term_id: str) -> KnowledgeOntologyMapping | None:
    """Return one ontology mapping by stable term identifier."""

    return next(
        (
            mapping
            for mapping in DEFAULT_ONTOLOGY_MAPPINGS
            if mapping.term_id == term_id
        ),
        None,
    )


def list_scientific_context(
    *, domain: KnowledgeContextDomain | None = None
) -> tuple[ScientificContextEntry, ...]:
    """Return curated scientific context entries, optionally filtered by domain."""

    if domain is None:
        return DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES
    return tuple(
        entry for entry in DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES if entry.domain is domain
    )


def get_scientific_context(context_id: str) -> ScientificContextEntry | None:
    """Return one scientific context entry by stable identifier."""

    return next(
        (
            entry
            for entry in DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES
            if entry.context_id == context_id
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
        corpus
        for corpus in DEFAULT_CORPUS_MANIFESTS
        if corpus.source_kind is source_kind
    )


def get_corpus_manifest(corpus_id: str) -> CorpusManifest | None:
    """Return one corpus manifest by stable identifier."""

    return next(
        (
            corpus
            for corpus in DEFAULT_CORPUS_MANIFESTS
            if corpus.corpus_id == corpus_id
        ),
        None,
    )


def list_known_problems(
    *, problem_kind: KnowledgeProblemKind | None = None
) -> tuple[KnownProblemRegistryEntry, ...]:
    """Return curated known-problem entries, optionally filtered by problem kind."""

    if problem_kind is None:
        return DEFAULT_KNOWN_PROBLEM_REGISTRY
    return tuple(
        entry
        for entry in DEFAULT_KNOWN_PROBLEM_REGISTRY
        if entry.problem_kind is problem_kind
    )


def get_known_problem(problem_id: str) -> KnownProblemRegistryEntry | None:
    """Return one known-problem entry by stable identifier."""

    return next(
        (
            entry
            for entry in DEFAULT_KNOWN_PROBLEM_REGISTRY
            if entry.problem_id == problem_id
        ),
        None,
    )


def list_literature_groups(
    *, focus_area: LiteratureFocusArea | None = None
) -> tuple[LiteratureGroup, ...]:
    """Return curated literature groups, optionally filtered by focus area."""

    if focus_area is None:
        return DEFAULT_LITERATURE_GROUPS
    return tuple(
        group for group in DEFAULT_LITERATURE_GROUPS if group.focus_area is focus_area
    )


def get_literature_group(group_id: str) -> LiteratureGroup | None:
    """Return one literature group by stable identifier."""

    return next(
        (group for group in DEFAULT_LITERATURE_GROUPS if group.group_id == group_id),
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
        (
            rule
            for rule in DEFAULT_SCIENTIFIC_RULE_REFERENCES
            if rule.rule_id == rule_id
        ),
        None,
    )


__all__ = [
    "get_citation",
    "get_corpus_manifest",
    "get_known_problem",
    "get_literature_group",
    "get_ontology_mapping",
    "get_scientific_context",
    "get_scientific_rule",
    "list_citations",
    "list_corpus_manifests",
    "list_known_problems",
    "list_literature_groups",
    "list_ontology_mappings",
    "list_scientific_context",
    "list_scientific_rules",
]
