# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.grounding.citations import (
    DEFAULT_CITATION_REGISTRY,
    CitationSourceKind,
)


def test_citation_registry_covers_core_reference_families() -> None:
    citation_ids = {citation.citation_id for citation in DEFAULT_CITATION_REGISTRY}
    source_kinds = {citation.source_kind for citation in DEFAULT_CITATION_REGISTRY}

    assert {
        "citation:uniprot_2025",
        "citation:psi_mod_2008",
        "citation:psi_ms_cv_2012",
        "citation:target_decoy_2007",
        "citation:ascore_2006",
        "citation:tmtpro_2020",
        "citation:protein_inference_2012",
        "citation:swath_2012",
    }.issubset(citation_ids)
    assert source_kinds == {
        CitationSourceKind.DATABASE,
        CitationSourceKind.ONTOLOGY,
        CitationSourceKind.METHOD,
        CitationSourceKind.REVIEW,
    }


def test_citation_registry_records_version_and_license_notes() -> None:
    for citation in DEFAULT_CITATION_REGISTRY:
        assert citation.publisher
        assert citation.source_locator_kind
        assert citation.access_route
        assert citation.retrieval_trace
        assert citation.evidence_role
        assert citation.license_note
        assert citation.summary
        assert citation.publication_year >= 2006
        assert citation.source_version
