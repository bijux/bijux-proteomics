# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references import (
    DEFAULT_ONTOLOGY_MAPPINGS,
    KnowledgeOntologyDomain,
    resolve_ontology_mapping,
)


def test_ontology_mappings_cover_needed_proteomics_domains() -> None:
    domains = {mapping.domain for mapping in DEFAULT_ONTOLOGY_MAPPINGS}

    assert domains == {
        KnowledgeOntologyDomain.UNIPROT,
        KnowledgeOntologyDomain.PTM,
        KnowledgeOntologyDomain.INSTRUMENT,
        KnowledgeOntologyDomain.ACQUISITION_MODE,
    }


def test_ontology_mappings_normalize_aliases_for_curated_terms() -> None:
    assert (
        resolve_ontology_mapping(KnowledgeOntologyDomain.UNIPROT, "Swiss-Prot").term_id
        == "uniprot:reviewed_entry"
    )
    assert (
        resolve_ontology_mapping(KnowledgeOntologyDomain.PTM, "phospho").term_id
        == "ptm:phosphorylation"
    )
    assert (
        resolve_ontology_mapping(
            KnowledgeOntologyDomain.INSTRUMENT, "fusion lumos"
        ).term_id
        == "instrument:orbitrap"
    )
    assert (
        resolve_ontology_mapping(
            KnowledgeOntologyDomain.ACQUISITION_MODE, "swath-ms"
        ).term_id
        == "acquisition_mode:dia"
    )


def test_ontology_mappings_return_none_for_unknown_terms() -> None:
    assert (
        resolve_ontology_mapping(KnowledgeOntologyDomain.ACQUISITION_MODE, "nanopore")
        is None
    )
