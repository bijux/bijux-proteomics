# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.collaboration import (
    CitationRegistryEntry,
    build_citation_registry_document,
)


def test_build_citation_registry_document_sorts_by_kind_then_id() -> None:
    document = build_citation_registry_document(
        (
            CitationRegistryEntry(
                citation_id="z2",
                citation_kind="tool",
                label="Tool B",
                source_url="https://example.com/tool-b",
                evidence_pointer_ids=("ev-2",),
            ),
            CitationRegistryEntry(
                citation_id="a1",
                citation_kind="algorithm",
                label="Algo A",
                source_url="https://example.com/algo-a",
                evidence_pointer_ids=("ev-1",),
            ),
        )
    )

    assert document.entries[0].citation_kind == "algorithm"
