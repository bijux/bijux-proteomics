# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import identification


def _matrix_root() -> Path:
    return (
        Path(__file__).resolve().parents[1] / "fixtures" / "search_adapter_corpora"
    )


def test_identification_package_exports_search_adapter_split_surface() -> None:
    matrix = identification.build_search_adapter_corpus_conformance_matrix(
        _matrix_root()
    )

    assert hasattr(identification, "SearchAdapterKind")
    assert hasattr(identification, "search_adapter_registry")
    assert hasattr(identification, "normalize_search_results_with_adapter")
    assert hasattr(identification, "build_search_adapter_corpus_conformance_matrix")
    assert identification.SearchAdapterKind.COMET.value == "comet"
    assert matrix.passes is True
