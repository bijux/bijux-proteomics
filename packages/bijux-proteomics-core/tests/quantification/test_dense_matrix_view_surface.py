# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import math

from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_dense_label_free_quant_table_view,
    build_label_free_intensity_table,
    missing_value_code_to_kind,
    missing_value_kind_to_code,
)


def test_dense_label_free_quant_table_view_preserves_abundance_and_missing_codes() -> (
    None
):
    table = build_label_free_intensity_table(
        (
            Ms1FeatureRecord(
                feature_id="dense-001",
                sample_id="S1",
                peptide="PEPAA",
                canonical_peptide="PEPAA",
                intensity=100.0,
                protein_refs=("P1",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="dense-002",
                sample_id="S2",
                peptide="PEPAA",
                canonical_peptide="PEPAA",
                intensity=None,
                protein_refs=("P1",),
                missing_value_kind=MissingValueKind.NOT_OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="dense-003",
                sample_id="S1",
                peptide="PEPBB",
                canonical_peptide="PEPBB",
                intensity=0.0,
                protein_refs=("P2",),
                missing_value_kind=MissingValueKind.ZERO,
            ),
            Ms1FeatureRecord(
                feature_id="dense-004",
                sample_id="S2",
                peptide="PEPBB",
                canonical_peptide="PEPBB",
                intensity=None,
                protein_refs=("P2",),
                missing_value_kind=MissingValueKind.FILTERED,
            ),
        ),
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )

    view = build_dense_label_free_quant_table_view(table)

    assert view.entity_ids == ("PEPAA", "PEPBB")
    assert view.sample_ids == ("S1", "S2")
    assert view.abundance_matrix.shape == (2, 2)
    assert view.abundance_matrix[0, 0] == 100.0
    assert math.isnan(view.abundance_matrix[0, 1])
    assert view.abundance_matrix[1, 0] == 0.0
    assert (
        missing_value_code_to_kind(view.missing_kind_codes[0, 0])
        is MissingValueKind.OBSERVED
    )
    assert (
        missing_value_code_to_kind(view.missing_kind_codes[0, 1])
        is MissingValueKind.NOT_OBSERVED
    )
    assert (
        missing_value_code_to_kind(view.missing_kind_codes[1, 0])
        is MissingValueKind.ZERO
    )
    assert (
        missing_value_code_to_kind(view.missing_kind_codes[1, 1])
        is MissingValueKind.FILTERED
    )
    assert view.log2_abundance_matrix[0, 0] > 0.0
    assert view.log2_abundance_matrix[1, 0] == 0.0


def test_missing_value_kind_dense_codes_round_trip() -> None:
    for kind in (
        MissingValueKind.OBSERVED,
        MissingValueKind.ZERO,
        MissingValueKind.NOT_OBSERVED,
        MissingValueKind.FILTERED,
        MissingValueKind.IMPUTED,
        MissingValueKind.CENSORED,
        MissingValueKind.EXCLUDED,
        MissingValueKind.NOT_APPLICABLE,
    ):
        assert missing_value_code_to_kind(missing_value_kind_to_code(kind)) is kind
