# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_heatmap_preparation_report,
    build_label_free_intensity_table,
    export_heatmap_column_metadata_tsv,
    export_heatmap_matrix_tsv,
    export_heatmap_row_metadata_tsv,
    export_heatmap_summary_tsv,
    normalize_label_free_table,
)


def _records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="hex-001",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="hex-002",
            sample_id="s2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=140.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="hex-003",
            sample_id="s1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=220.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="hex-004",
            sample_id="s2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=260.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="s1",
            condition="case",
            replicate=1,
            fraction=1,
            batch="b1",
            spectra_file="s1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="s2",
            condition="ctrl",
            replicate=1,
            fraction=1,
            batch="b2",
            spectra_file="s2.mzml",
        ),
    )


def test_heatmap_preparation_exports_matrix_and_metadata_ledgers(tmp_path) -> None:
    raw = build_label_free_intensity_table(
        _records(),
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    report = build_heatmap_preparation_report(
        normalize_label_free_table(raw, method=NormalizationMethod.MEDIAN),
        design_entries=_design(),
    )

    summary_path = tmp_path / "heatmap.summary.tsv"
    matrix_path = tmp_path / "heatmap.matrix.tsv"
    row_path = tmp_path / "heatmap.rows.tsv"
    column_path = tmp_path / "heatmap.columns.tsv"
    export_heatmap_summary_tsv(report, summary_path)
    export_heatmap_matrix_tsv(report, matrix_path)
    export_heatmap_row_metadata_tsv(report, row_path)
    export_heatmap_column_metadata_tsv(report, column_path)

    assert "entity_level\tmeasure_kind\taggregation_method" in summary_path.read_text()
    assert "entity_id\ts1\ts2" in matrix_path.read_text()
    assert (
        "protein_refs\tmember_peptides\tobserved_sample_count\tmissing_sample_count\tfilled_missing_sample_count\tobserved_fraction\tmissing_value_policy"
        in row_path.read_text()
    )
    assert (
        "column_index\tsample_id\tcondition\treplicate\tfraction\tbatch\tinstrument\tsearch_engine\tmissing_value_policy\tnormalization_factor"
        in column_path.read_text()
    )
