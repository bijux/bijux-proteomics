# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import math

import numpy as np

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
)
from bijux_proteomics.quantification.contracts.matrix_models import (
    LabelFreeQuantTable,
)
from bijux_proteomics.quantification.matrix import (
    build_dense_label_free_quant_table_view,
)
from bijux_proteomics.quantification.statistics.differential_abundance import (
    _collect_condition_values,
    _collect_condition_values_vectorized,
)


def _differential_table() -> tuple[
    LabelFreeQuantTable, tuple[ExperimentalDesignEntry, ...], dict[str, float]
]:
    records = (
        Ms1FeatureRecord(
            feature_id="dv-001",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=128.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="dv-002",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=132.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="dv-003",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=0.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.ZERO,
        ),
        Ms1FeatureRecord(
            feature_id="dv-004",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=None,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.FILTERED,
        ),
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.mzml",
        ),
    )
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )
    weights = {
        "case-1": 1.0,
        "case-2": 0.8,
        "ctrl-1": 0.5,
        "ctrl-2": 0.2,
    }
    return table, design, weights


def test_vectorized_differential_value_collection_matches_pure_reference() -> None:
    table, _design, weights = _differential_table()
    dense_view = build_dense_label_free_quant_table_view(table)
    sample_weight_vector = np.array(
        [weights.get(sample_id, 1.0) for sample_id in dense_view.sample_ids],
        dtype=float,
    )

    pure_values, pure_weights, pure_counts = _collect_condition_values(
        {(value.entity_id, value.sample_id): value for value in table.values},
        "PEPA",
        ("ctrl-1", "ctrl-2"),
        sample_weights=weights,
    )
    vectorized_values, vectorized_weights, vectorized_counts = (
        _collect_condition_values_vectorized(
            dense_view.log2_abundance_matrix[dense_view.entity_index["PEPA"]],
            dense_view.missing_kind_codes[dense_view.entity_index["PEPA"]],
            np.array(
                [
                    dense_view.sample_index["ctrl-1"],
                    dense_view.sample_index["ctrl-2"],
                ],
                dtype=int,
            ),
            sample_weight_vector=sample_weight_vector,
        )
    )

    assert np.allclose(pure_values, vectorized_values, equal_nan=True)
    assert np.allclose(pure_weights, vectorized_weights, equal_nan=True)
    assert pure_counts == vectorized_counts
    assert math.isclose(vectorized_values[0], 0.0, abs_tol=1e-12)
