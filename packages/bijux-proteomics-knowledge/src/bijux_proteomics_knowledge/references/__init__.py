# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated scientific reference surfaces owned by the knowledge package."""

from __future__ import annotations

from bijux_proteomics_knowledge.references.citations import (
    CitationRecord,
    CitationSourceKind,
    DEFAULT_CITATION_REGISTRY,
)
from bijux_proteomics_knowledge.references.ontologies import (
    KnowledgeOntologyDomain,
    KnowledgeOntologyMapping,
    DEFAULT_ONTOLOGY_MAPPINGS,
    resolve_ontology_mapping,
)

__all__ = [
    "CitationRecord",
    "CitationSourceKind",
    "DEFAULT_CITATION_REGISTRY",
    "DEFAULT_ONTOLOGY_MAPPINGS",
    "KnowledgeOntologyDomain",
    "KnowledgeOntologyMapping",
    "resolve_ontology_mapping",
]
