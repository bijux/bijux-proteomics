# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.literature import (
    DEFAULT_LITERATURE_GROUPS,
    LiteratureFocusArea,
)


def test_literature_groups_cover_required_focus_areas() -> None:
    focus_areas = {group.focus_area for group in DEFAULT_LITERATURE_GROUPS}

    assert focus_areas == {
        LiteratureFocusArea.ENZYME,
        LiteratureFocusArea.MULTIPLEX,
        LiteratureFocusArea.QC,
        LiteratureFocusArea.FDR,
        LiteratureFocusArea.QUANTIFICATION,
        LiteratureFocusArea.PTM,
        LiteratureFocusArea.DIA,
        LiteratureFocusArea.TARGETED,
    }


def test_literature_groups_carry_citations_and_context_links() -> None:
    for group in DEFAULT_LITERATURE_GROUPS:
        assert group.version_trace
        assert group.retrieval_trace
        assert group.citation_ids
        assert group.benchmark_ids
        assert group.curation_note
