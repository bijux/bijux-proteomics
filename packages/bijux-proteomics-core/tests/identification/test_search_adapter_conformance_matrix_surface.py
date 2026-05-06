# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    build_search_adapter_corpus_conformance_matrix,
)


def _matrix_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "search_adapter_corpora"
    )


def test_search_adapter_corpus_conformance_matrix_summarizes_all_built_in_adapters() -> (
    None
):
    matrix = build_search_adapter_corpus_conformance_matrix(_matrix_root())

    assert matrix.passes is True
    by_kind = {entry.adapter_kind: entry for entry in matrix.entries}
    assert set(by_kind) == {
        SearchAdapterKind.COMET,
        SearchAdapterKind.MSFRAGGER,
        SearchAdapterKind.SAGE,
        SearchAdapterKind.MAXQUANT_EVIDENCE,
        SearchAdapterKind.DIANN,
        SearchAdapterKind.SPECTRONAUT,
    }
    for entry in matrix.entries:
        assert entry.corpus_passes is True
        assert entry.corpus_entry_count == 2
        assert entry.total_accepted_rows == 6
        assert entry.total_rejected_rows == 0
        assert entry.unsupported_column_count == 0
        assert entry.lost_column_count == 0
