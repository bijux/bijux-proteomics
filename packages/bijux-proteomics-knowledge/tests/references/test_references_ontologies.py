# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.grounding.ontologies import (
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
    reviewed_entry = resolve_ontology_mapping(
        KnowledgeOntologyDomain.UNIPROT, "Swiss-Prot"
    )
    assert reviewed_entry is not None
    assert reviewed_entry.term_id == "uniprot:reviewed_entry"

    phospho = resolve_ontology_mapping(KnowledgeOntologyDomain.PTM, "phospho")
    assert phospho is not None
    assert phospho.term_id == "ptm:phosphorylation"

    orbitrap = resolve_ontology_mapping(
        KnowledgeOntologyDomain.INSTRUMENT, "fusion lumos"
    )
    assert orbitrap is not None
    assert orbitrap.term_id == "instrument:orbitrap"

    dia = resolve_ontology_mapping(KnowledgeOntologyDomain.ACQUISITION_MODE, "swath-ms")
    assert dia is not None
    assert dia.term_id == "acquisition_mode:dia"


def test_ontology_mappings_return_none_for_unknown_terms() -> None:
    assert (
        resolve_ontology_mapping(KnowledgeOntologyDomain.ACQUISITION_MODE, "nanopore")
        is None
    )


def test_ontology_mappings_carry_traceable_curation_metadata() -> None:
    for mapping in DEFAULT_ONTOLOGY_MAPPINGS:
        assert mapping.version_trace
        assert mapping.retrieval_trace
        assert mapping.source_name
