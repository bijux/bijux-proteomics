# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import numpy as np

from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantEntityKind,
    QuantMeasureKind,
    SampleMetadata,
)
from bijux_proteomics.quantification.core_matrix import (
    build_numeric_quant_matrix,
    iter_quant_matrix_cells,
    quant_matrix_to_dense_array,
    rebuild_quant_matrix_from_dense_array,
)


def test_numeric_quant_matrix_builds_dense_rows_missingness_and_metadata() -> None:
    matrix = build_numeric_quant_matrix(
        matrix_id="protein-intensity",
        entity_kind=QuantEntityKind.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        entity_ids=("P1", "P2"),
        sample_ids=("S1", "S2"),
        value_lookup={
            ("P1", "S1"): 10.0,
            ("P1", "S2"): None,
            ("P2", "S1"): 5.0,
            ("P2", "S2"): 7.0,
        },
        missing_state_lookup={
            ("P1", "S1"): MissingValueState.OBSERVED,
            ("P1", "S2"): MissingValueState.NOT_OBSERVED,
            ("P2", "S1"): MissingValueState.ZERO,
            ("P2", "S2"): MissingValueState.OBSERVED,
        },
        support_count_lookup={
            ("P1", "S1"): 2,
            ("P2", "S1"): 1,
            ("P2", "S2"): 3,
        },
        row_metadata_lookup={
            "P1": {"protein_refs": "P1"},
            "P2": {"protein_refs": "P2"},
        },
        sample_metadata=(
            SampleMetadata(sample_id="S1", run_id="run-1", condition="control"),
            SampleMetadata(sample_id="S2", run_id="run-2", condition="treated"),
        ),
        transformation_history=("aggregation:sum",),
        metadata={"note": "matrix note"},
    )

    assert matrix.entity_ids == ("P1", "P2")
    assert matrix.sample_ids == ("S1", "S2")
    assert matrix.values[0] == (10.0, None)
    assert matrix.missing_value_states[1][0] is MissingValueState.ZERO
    assert matrix.support_counts == ((2, 0), (1, 3))
    assert matrix.row_metadata[0]["protein_refs"] == "P1"
    assert matrix.sample_metadata[1].condition == "treated"
    assert matrix.transformation_history == ("aggregation:sum",)


def test_numeric_quant_matrix_dense_roundtrip_preserves_grid_and_history() -> None:
    matrix = build_numeric_quant_matrix(
        matrix_id="peptide-intensity",
        entity_kind=QuantEntityKind.PEPTIDE,
        measure_kind=QuantMeasureKind.INTENSITY,
        entity_ids=("PEP1",),
        sample_ids=("S1", "S2"),
        value_lookup={("PEP1", "S1"): 2.0, ("PEP1", "S2"): None},
        missing_state_lookup={
            ("PEP1", "S1"): MissingValueState.OBSERVED,
            ("PEP1", "S2"): MissingValueState.FILTERED,
        },
        transformation_history=("aggregation:median",),
    )

    dense = quant_matrix_to_dense_array(matrix)
    assert dense.shape == (1, 2)
    assert dense[0, 0] == 2.0
    assert np.isnan(dense[0, 1])

    rebuilt = rebuild_quant_matrix_from_dense_array(
        matrix,
        np.array([[3.0, np.nan]], dtype=float),
        transformation_step="normalization:median",
        metadata_updates={"note": "normalized"},
    )

    assert rebuilt.values == ((3.0, None),)
    assert rebuilt.missing_value_states == matrix.missing_value_states
    assert rebuilt.transformation_history == (
        "aggregation:median",
        "normalization:median",
    )
    assert rebuilt.metadata["note"] == "normalized"


def test_iter_quant_matrix_cells_emits_stable_entity_sample_order() -> None:
    matrix = build_numeric_quant_matrix(
        matrix_id="protein-ratio",
        entity_kind=QuantEntityKind.PROTEIN,
        measure_kind=QuantMeasureKind.RATIO,
        entity_ids=("P1", "P2"),
        sample_ids=("A", "B"),
        value_lookup={
            ("P1", "A"): 1.0,
            ("P2", "B"): 4.0,
        },
        missing_state_lookup={
            ("P1", "A"): MissingValueState.OBSERVED,
            ("P1", "B"): MissingValueState.NOT_OBSERVED,
            ("P2", "A"): MissingValueState.NOT_OBSERVED,
            ("P2", "B"): MissingValueState.OBSERVED,
        },
    )

    assert iter_quant_matrix_cells(matrix) == (
        ("P1", "A", 1.0, MissingValueState.OBSERVED),
        ("P1", "B", None, MissingValueState.NOT_OBSERVED),
        ("P2", "A", None, MissingValueState.NOT_OBSERVED),
        ("P2", "B", 4.0, MissingValueState.OBSERVED),
    )
