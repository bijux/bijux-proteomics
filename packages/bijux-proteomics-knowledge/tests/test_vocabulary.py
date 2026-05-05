# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.vocabulary import (
    ControlledVocabularyDomain,
    normalize_controlled_term,
)


def test_controlled_vocabulary_normalizes_known_aliases() -> None:
    enzyme = normalize_controlled_term(ControlledVocabularyDomain.ENZYME, "lys-c")
    assay = normalize_controlled_term(
        ControlledVocabularyDomain.ASSAY_TYPE, "engagement"
    )

    assert enzyme is not None
    assert enzyme.term_id == "enzyme:lysc"
    assert assay is not None
    assert assay.term_id == "assay:target_engagement"


def test_controlled_vocabulary_returns_none_for_unknown_term() -> None:
    assert (
        normalize_controlled_term(
            ControlledVocabularyDomain.INSTRUMENT, "homebrew-quadrupole"
        )
        is None
    )
