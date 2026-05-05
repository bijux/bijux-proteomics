# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references import (
    DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES,
    KnowledgeContextDomain,
)


def test_scientific_context_registry_covers_required_domains() -> None:
    domains = {entry.domain for entry in DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES}

    assert domains == {
        KnowledgeContextDomain.DIGESTION_CLEAVAGE,
        KnowledgeContextDomain.PTM_LOCALIZATION,
        KnowledgeContextDomain.DIA_SPECTRAL_LIBRARY,
        KnowledgeContextDomain.QUANTIFICATION_INTERPRETATION,
    }


def test_scientific_context_entries_carry_provenance_and_caveats() -> None:
    for entry in DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES:
        assert entry.citation_ids
        assert entry.benchmark_ids
        assert entry.scientific_assertion
        assert entry.interpretation_caveat
