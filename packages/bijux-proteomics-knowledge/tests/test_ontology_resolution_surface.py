# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.ontologies import (
    KnowledgeOntologyDomain,
    resolve_ontology_mapping,
)


def test_ontology_resolution_normalizes_known_aliases() -> None:
    enzyme = resolve_ontology_mapping(KnowledgeOntologyDomain.INSTRUMENT, "tims_tof")
    acquisition = resolve_ontology_mapping(
        KnowledgeOntologyDomain.ACQUISITION_MODE,
        "swath",
    )

    assert enzyme is not None
    assert enzyme.term_id == "instrument:timstof"
    assert acquisition is not None
    assert acquisition.term_id == "acquisition_mode:dia"


def test_ontology_resolution_returns_none_for_unknown_term() -> None:
    assert (
        resolve_ontology_mapping(
            KnowledgeOntologyDomain.INSTRUMENT,
            "homebrew-quadrupole",
        )
        is None
    )
