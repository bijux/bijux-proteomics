# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
)
from bijux_proteomics.quantification.review import (
    build_replicate_and_batch_qc_report,
)


def _table_and_design() -> tuple[
    LabelFreeQuantTable, tuple[ExperimentalDesignEntry, ...]
]:
    records = (
        Ms1FeatureRecord(
            feature_id="q-001",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=1000.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="q-002",
            sample_id="s2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="q-003",
            sample_id="s3",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=950.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="q-004",
            sample_id="s4",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=90.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="q-005",
            sample_id="s1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=800.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="q-006",
            sample_id="s2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=120.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="q-007",
            sample_id="s3",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=760.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="q-008",
            sample_id="s4",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=130.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="s1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="s1.mzml",
            batch="b1",
            instrument="inst-a",
        ),
        ExperimentalDesignEntry(
            sample_id="s2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="s2.mzml",
            batch="b1",
            instrument="inst-a",
        ),
        ExperimentalDesignEntry(
            sample_id="s3",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="s3.mzml",
            batch="b2",
            instrument="inst-b",
        ),
        ExperimentalDesignEntry(
            sample_id="s4",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="s4.mzml",
            batch="b2",
            instrument="inst-b",
        ),
    )
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )
    return table, design


def test_replicate_and_batch_qc_report_surfaces_outlier_sample_context() -> None:
    table, design = _table_and_design()
    report = build_replicate_and_batch_qc_report(
        table,
        design_entries=design,
        within_condition_warning_threshold=0.95,
        batch_shift_threshold=0.2,
    )

    assert report.batch_effect_report.batches
    assert report.replicate_correlation_report.entries
    assert report.replicate_cv_report.entries
    assert report.sample_pca_report is not None
    assert report.condition_clustering_report is not None
    assert report.replicate_correlation_count >= 1
    assert report.flagged_batch_count >= 0
    assert report.batch_effect_report.batch_variance_proxy >= 0.0
    assert report.batch_effect_report.batch_associated_component_count >= 0
    assert len(report.outlier_samples) >= 1
    assert report.outlier_samples[0].spectra_file.endswith(".mzml")
    assert all(
        entry.outlier_reasons
        for entry in report.sample_pca_report.entries
        if entry.outlier
    )
