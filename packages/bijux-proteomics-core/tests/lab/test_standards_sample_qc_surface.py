# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantEntityKind,
    QuantMatrix,
    QuantMeasureKind,
)
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.lab import (
    build_internal_standard_sample_qc,
    track_internal_standards,
)
from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    estimate_sample_weights,
)


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="sample_a",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="sample_a.mzml",
            batch=None,
        ),
        ExperimentalDesignEntry(
            sample_id="sample_b",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="sample_b.mzml",
            batch=None,
        ),
        ExperimentalDesignEntry(
            sample_id="sample_c",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="sample_c.mzml",
            batch=None,
        ),
        ExperimentalDesignEntry(
            sample_id="sample_d",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="sample_d.mzml",
            batch=None,
        ),
    )


def _lfq_table() -> LabelFreeQuantTable:
    records = (
        Ms1FeatureRecord(
            feature_id="std-weight-001",
            sample_id="sample_a",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="std-weight-002",
            sample_id="sample_b",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=101.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="std-weight-003",
            sample_id="sample_c",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=380.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="std-weight-004",
            sample_id="sample_d",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=395.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="std-weight-005",
            sample_id="sample_a",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=150.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="std-weight-006",
            sample_id="sample_b",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=151.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="std-weight-007",
            sample_id="sample_c",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=605.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="std-weight-008",
            sample_id="sample_d",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=608.0,
            protein_refs=("P002",),
        ),
    )
    return build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )


def _standards_matrix() -> QuantMatrix:
    return QuantMatrix(
        matrix_id="internal_standard_weight_matrix",
        entity_kind=QuantEntityKind.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        entity_ids=("STD_A", "STD_B"),
        sample_ids=("sample_a", "sample_b", "sample_c", "sample_d"),
        values=(
            (1000.0, 980.0, 620.0, None),
            (500.0, 510.0, 505.0, None),
        ),
        missing_value_states=(
            (
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.NOT_OBSERVED,
            ),
            (
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.NOT_OBSERVED,
            ),
        ),
        support_counts=((1, 1, 1, 0), (1, 1, 1, 0)),
    )


def test_internal_standard_sample_qc_lowers_sample_weights() -> None:
    tracking_rows = track_internal_standards(_standards_matrix(), ("STD_A", "STD_B"))
    sample_qc_rows = build_internal_standard_sample_qc(tracking_rows)

    report = estimate_sample_weights(_lfq_table(), _design(), sample_qc_rows)
    weights = {entry.sample_id: entry for entry in report.entries}

    assert weights["sample_a"].reliability_weight == 1.0
    assert weights["sample_c"].reliability_weight == 0.5
    assert "caution_sample_qc" in weights["sample_c"].low_weight_reasons
    assert "sample_qc:internal_standard_drift" in weights["sample_c"].low_weight_reasons
    assert weights["sample_d"].reliability_weight == 0.0
    assert "failed_sample_qc" in weights["sample_d"].low_weight_reasons
