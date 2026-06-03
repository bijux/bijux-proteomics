# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import math

import numpy as np

from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    normalize_label_free_table,
)
from bijux_proteomics.quantification.matrix.core_matrix import (
    quant_matrix_to_dense_array,
)
from bijux_proteomics.quantification.normalization.normalization import (
    _normalize_intensity_matrix_pure,
    _normalize_intensity_matrix_vectorized,
)


def _normalization_records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="vec-nrm-001",
            sample_id="S1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="vec-nrm-002",
            sample_id="S2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=140.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="vec-nrm-003",
            sample_id="S3",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=0.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.ZERO,
        ),
        Ms1FeatureRecord(
            feature_id="vec-nrm-004",
            sample_id="S1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=60.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="vec-nrm-005",
            sample_id="S2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=None,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="vec-nrm-006",
            sample_id="S3",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=80.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="vec-nrm-007",
            sample_id="S1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=30.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="vec-nrm-008",
            sample_id="S2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=45.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="vec-nrm-009",
            sample_id="S3",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=None,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.CENSORED,
        ),
    )


def _build_table():
    return build_label_free_intensity_table(
        _normalization_records(),
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )


def test_vectorized_normalization_matches_pure_reference_paths() -> None:
    table = _build_table()
    matrix = quant_matrix_to_dense_array(table.to_quant_matrix())
    sample_ids = table.sample_ids

    for method in (
        NormalizationMethod.TIC,
        NormalizationMethod.MEDIAN,
        NormalizationMethod.QUANTILE,
        NormalizationMethod.LOG2_MEDIAN_CENTERING,
        NormalizationMethod.VSN_LIKE,
    ):
        pure_matrix, pure_factors = _normalize_intensity_matrix_pure(
            matrix,
            sample_ids,
            method=method,
        )
        vectorized_matrix, vectorized_factors = _normalize_intensity_matrix_vectorized(
            matrix,
            sample_ids,
            method=method,
        )

        assert np.allclose(
            pure_matrix,
            vectorized_matrix,
            equal_nan=True,
        )
        assert pure_factors.keys() == vectorized_factors.keys()
        for sample_id in sample_ids:
            assert math.isclose(
                pure_factors[sample_id],
                vectorized_factors[sample_id],
                rel_tol=1e-12,
                abs_tol=1e-12,
            )


def test_public_normalization_uses_vectorized_reference_results() -> None:
    table = _build_table()
    matrix = quant_matrix_to_dense_array(table.to_quant_matrix())

    expected_matrix, expected_factors = _normalize_intensity_matrix_vectorized(
        matrix,
        table.sample_ids,
        method=NormalizationMethod.MEDIAN,
    )
    normalized = normalize_label_free_table(table, method=NormalizationMethod.MEDIAN)

    assert np.allclose(
        quant_matrix_to_dense_array(normalized.to_quant_matrix()),
        expected_matrix,
        equal_nan=True,
    )
    assert normalized.normalization_factors == expected_factors
