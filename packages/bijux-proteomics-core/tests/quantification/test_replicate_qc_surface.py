# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_condition_clustering_report,
    build_label_free_intensity_table,
    build_replicate_cv_report,
    build_sample_pca_report,
)


def test_replicate_cv_report_flags_unstable_condition_spread() -> None:
    records = (
        Ms1FeatureRecord(
            feature_id="rcv-001",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rcv-002",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=300.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rcv-003",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=200.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rcv-004",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=210.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rcv-005",
            sample_id="case-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=120.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rcv-006",
            sample_id="case-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=360.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rcv-007",
            sample_id="ctrl-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=220.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="rcv-008",
            sample_id="ctrl-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=225.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
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

    report = build_replicate_cv_report(
        table,
        design,
        high_cv_threshold=0.2,
    )
    by_condition = {entry.condition: entry for entry in report.entries}

    assert report.entity_level is QuantEntityLevel.PEPTIDE
    assert by_condition["case"].flagged is True
    assert by_condition["case"].high_cv_entity_count == 2
    assert by_condition["ctrl"].flagged is False
    assert by_condition["ctrl"].high_cv_entity_count == 0


def test_sample_pca_report_surfaces_study_space_outlier() -> None:
    records = (
        Ms1FeatureRecord(
            feature_id="pca-001",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pca-002",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=105.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pca-003",
            sample_id="case-3",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=800.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pca-004",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=40.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pca-005",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=42.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pca-006",
            sample_id="case-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=120.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pca-007",
            sample_id="case-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=118.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pca-008",
            sample_id="case-3",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=920.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pca-009",
            sample_id="ctrl-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=55.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pca-010",
            sample_id="ctrl-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=54.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="case-3",
            condition="case",
            replicate=3,
            fraction=1,
            spectra_file="case-3.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
            batch="b2",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.mzml",
            batch="b2",
        ),
    )
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )

    report = build_sample_pca_report(table, design)
    by_sample = {entry.sample_id: entry for entry in report.entries}

    assert report.explained_variance_ratio_pc1 > 0.5
    assert by_sample["case-3"].outlier is True
    assert any(
        reason.startswith("distance_from_")
        for reason in by_sample["case-3"].outlier_reasons
    )
    assert by_sample["case-1"].outlier is False


def test_condition_clustering_report_recognizes_condition_separation() -> None:
    records = (
        Ms1FeatureRecord(
            feature_id="clu-001",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="clu-002",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=102.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="clu-003",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=18.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="clu-004",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=20.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="clu-005",
            sample_id="case-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=90.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="clu-006",
            sample_id="case-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=89.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="clu-007",
            sample_id="ctrl-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=12.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="clu-008",
            sample_id="ctrl-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=11.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
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

    report = build_condition_clustering_report(table, design)

    assert report.condition_count == 2
    assert report.clustered_by_condition is True
    assert report.nearest_same_condition_fraction == 1.0
    assert report.mean_within_condition_distance is not None
    assert report.mean_between_condition_distance is not None
    assert (
        report.mean_within_condition_distance < report.mean_between_condition_distance
    )
