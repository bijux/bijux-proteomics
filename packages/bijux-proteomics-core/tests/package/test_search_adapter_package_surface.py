# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import identification
from bijux_proteomics.identification import search_adapters


def _matrix_root() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "search_adapter_corpora"


def test_identification_package_exports_search_adapter_split_surface() -> None:
    matrix = search_adapters.build_search_adapter_corpus_conformance_matrix(
        _matrix_root()
    )

    assert hasattr(identification, "SearchAdapterKind")
    assert hasattr(search_adapters, "search_adapter_registry")
    assert hasattr(search_adapters, "normalize_search_results_with_adapter")
    assert hasattr(search_adapters, "build_search_adapter_corpus_conformance_matrix")
    assert not hasattr(identification, "build_search_adapter_corpus_conformance_matrix")
    assert identification.SearchAdapterKind.COMET.value == "comet"
    assert matrix.passes is True
