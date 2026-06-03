# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    HeatmapMissingValuePolicy,
    HeatmapPreparationPolicy,
    MissingValueKind,
    Ms1FeatureRecord,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_heatmap_preparation_report,
    build_label_free_intensity_table,
    normalize_label_free_table,
)


def _records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="hm-001",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="hm-002",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=120.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="hm-003",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=90.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="hm-004",
            sample_id="case-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=300.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="hm-005",
            sample_id="case-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=360.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="hm-006",
            sample_id="ctrl-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=270.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="hm-007",
            sample_id="case-1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=500.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="hm-008",
            sample_id="case-2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=520.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            batch="b1",
            spectra_file="case-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            batch="b1",
            spectra_file="case-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="ctrl",
            replicate=1,
            fraction=1,
            batch="b2",
            spectra_file="ctrl-1.mzml",
        ),
    )


def _table():
    raw = build_label_free_intensity_table(
        _records(),
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    return normalize_label_free_table(raw, method=NormalizationMethod.MEDIAN)


def test_heatmap_preparation_report_builds_z_scored_matrix_and_metadata() -> None:
    report = build_heatmap_preparation_report(
        _table(),
        design_entries=_design(),
    )

    assert report.summary.output_entity_count == 3
    assert report.summary.sample_count == 3
    assert report.summary.z_scored is True
    assert report.column_metadata[0].sample_metadata.condition == "case"
    assert (
        report.column_metadata[0].missing_value_policy
        is HeatmapMissingValuePolicy.FILL_ROW_MEDIAN
    )
    assert report.row_metadata[0].entity_id == "P1"
    assert (
        report.row_metadata[0].missing_value_policy
        is HeatmapMissingValuePolicy.FILL_ROW_MEDIAN
    )
    assert len(report.rows[0].values) == 3
    assert abs(sum(report.rows[0].values)) < 1e-9


def test_heatmap_preparation_report_filters_by_protein_and_entity_limit() -> None:
    report = build_heatmap_preparation_report(
        _table(),
        policy=HeatmapPreparationPolicy(
            protein_refs=("P1", "P2"),
            max_entity_count=1,
            z_score_rows=False,
        ),
    )

    assert report.summary.filtered_protein_ref_count == 1
    assert report.summary.truncated_entity_count == 1
    assert report.summary.output_entity_count == 1
    assert report.rows[0].entity_id in {"P1", "P2"}


def test_heatmap_preparation_report_applies_missing_value_policy() -> None:
    median_report = build_heatmap_preparation_report(
        _table(),
        policy=HeatmapPreparationPolicy(
            z_score_rows=False,
            missing_value_policy=HeatmapMissingValuePolicy.FILL_ROW_MEDIAN,
        ),
    )
    drop_report = build_heatmap_preparation_report(
        _table(),
        policy=HeatmapPreparationPolicy(
            z_score_rows=False,
            missing_value_policy=HeatmapMissingValuePolicy.DROP_ROWS,
        ),
    )

    assert any(row.entity_id == "P3" for row in median_report.rows)
    p3_metadata = next(
        row for row in median_report.row_metadata if row.entity_id == "P3"
    )
    assert p3_metadata.missing_sample_count == 1
    assert p3_metadata.filled_missing_sample_count == 1
    assert p3_metadata.missing_value_policy is HeatmapMissingValuePolicy.FILL_ROW_MEDIAN
    assert all(row.entity_id != "P3" for row in drop_report.rows)
    assert drop_report.summary.filtered_missing_policy_count == 1


def test_heatmap_preparation_report_accepts_canonical_quant_matrix_input() -> None:
    report = build_heatmap_preparation_report(
        _table().to_quant_matrix(),
        design_entries=_design(),
    )

    assert report.summary.output_entity_count == 3
    assert report.column_metadata[0].sample_metadata.sample_id == "case-1"
