# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import (
    SearchResultColumnMapping,
    parse_psm_tsv,
    parse_psm_tsv_chunked,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def test_chunked_psm_parsing_matches_non_chunked_report() -> None:
    mapping = SearchResultColumnMapping(
        run_id="run_id",
        spectrum_id="spectrum_id",
        peptide="peptide",
        modified_peptide="modified_peptide",
        charge="charge",
        score="score",
        intensity="intensity",
        protein_refs="proteins",
    )
    eager = parse_psm_tsv(_fixture("peptide_matrix_psms.tsv"), mapping=mapping)
    chunked = parse_psm_tsv_chunked(
        _fixture("peptide_matrix_psms.tsv"),
        mapping=mapping,
        chunk_size_rows=2,
    )

    assert chunked.to_stable_json() == eager.to_stable_json()
