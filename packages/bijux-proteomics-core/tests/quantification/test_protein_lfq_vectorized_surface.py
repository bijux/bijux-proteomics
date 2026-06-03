# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.quantification import MissingValueKind
from bijux_proteomics.quantification.matrix.peptide_intensity_matrix import (
    PeptideIntensityMatrixRow,
    PeptideIntensityMatrixValue,
)
from bijux_proteomics.quantification.rollup.protein_lfq import (
    _build_pairwise_ratio_rows_pure,
    _build_pairwise_ratio_rows_vectorized,
    _observed_log2_intensities_by_sample_pure,
    _observed_log2_intensities_by_sample_vectorized,
)


def _peptide_rows() -> list[tuple[PeptideIntensityMatrixRow, bool]]:
    return [
        (
            PeptideIntensityMatrixRow(
                entity_id="PEP_A",
                peptide_sequence="PEP_A",
                protein_refs=("P1",),
                values=(
                    PeptideIntensityMatrixValue(
                        sample_id="S1",
                        abundance=100.0,
                        missing_value_kind=MissingValueKind.OBSERVED,
                        source_record_count=1,
                    ),
                    PeptideIntensityMatrixValue(
                        sample_id="S2",
                        abundance=200.0,
                        missing_value_kind=MissingValueKind.OBSERVED,
                        source_record_count=1,
                    ),
                    PeptideIntensityMatrixValue(
                        sample_id="S3",
                        abundance=None,
                        missing_value_kind=MissingValueKind.NOT_OBSERVED,
                        source_record_count=0,
                    ),
                ),
            ),
            True,
        ),
        (
            PeptideIntensityMatrixRow(
                entity_id="PEP_B",
                peptide_sequence="PEP_B",
                protein_refs=("P1",),
                values=(
                    PeptideIntensityMatrixValue(
                        sample_id="S1",
                        abundance=120.0,
                        missing_value_kind=MissingValueKind.OBSERVED,
                        source_record_count=1,
                    ),
                    PeptideIntensityMatrixValue(
                        sample_id="S2",
                        abundance=240.0,
                        missing_value_kind=MissingValueKind.OBSERVED,
                        source_record_count=1,
                    ),
                    PeptideIntensityMatrixValue(
                        sample_id="S3",
                        abundance=60.0,
                        missing_value_kind=MissingValueKind.OBSERVED,
                        source_record_count=1,
                    ),
                ),
            ),
            True,
        ),
    ]


def test_vectorized_pairwise_ratios_match_pure_reference() -> None:
    peptide_rows = _peptide_rows()
    sample_ids = ("S1", "S2", "S3")

    pure = _build_pairwise_ratio_rows_pure(
        peptide_rows,
        sample_ids=sample_ids,
        minimum_shared_peptides=1,
    )
    vectorized = _build_pairwise_ratio_rows_vectorized(
        peptide_rows,
        sample_ids=sample_ids,
        minimum_shared_peptides=1,
    )

    assert [entry.model_dump() for entry in pure] == [
        entry.model_dump() for entry in vectorized
    ]


def test_vectorized_observed_logs_match_pure_reference() -> None:
    peptide_rows = _peptide_rows()
    sample_ids = ("S1", "S2", "S3")

    pure = _observed_log2_intensities_by_sample_pure(
        peptide_rows,
        sample_ids=sample_ids,
    )
    vectorized = _observed_log2_intensities_by_sample_vectorized(
        peptide_rows,
        sample_ids=sample_ids,
    )

    assert pure == vectorized
