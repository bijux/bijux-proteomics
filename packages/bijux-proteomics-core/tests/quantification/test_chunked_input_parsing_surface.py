# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.quantification import (
    parse_ms1_feature_table,
    parse_ms1_feature_table_chunked,
    parse_precursor_intensity_table,
    parse_precursor_intensity_table_chunked,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def test_chunked_ms1_feature_parsing_matches_non_chunked_report() -> None:
    eager = parse_ms1_feature_table(_fixture("peptide_matrix_features.tsv"))
    chunked = parse_ms1_feature_table_chunked(
        _fixture("peptide_matrix_features.tsv"),
        chunk_size_rows=2,
    )

    assert chunked.to_stable_json() == eager.to_stable_json()


def test_chunked_precursor_parsing_matches_non_chunked_report() -> None:
    eager = parse_precursor_intensity_table(_fixture("peptide_matrix_precursors.tsv"))
    chunked = parse_precursor_intensity_table_chunked(
        _fixture("peptide_matrix_precursors.tsv"),
        chunk_size_rows=2,
    )

    assert chunked.to_stable_json() == eager.to_stable_json()
