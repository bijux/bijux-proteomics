# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import math

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    build_sample_distance_report,
    build_sample_pca_variance_report,
)


def _sample_exploration_inputs() -> tuple[tuple[Ms1FeatureRecord, ...], tuple[ExperimentalDesignEntry, ...]]:
    records = (
        Ms1FeatureRecord(
            feature_id="explore-001",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="explore-002",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=102.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="explore-003",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=18.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="explore-004",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=20.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="explore-005",
            sample_id="case-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=90.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="explore-006",
            sample_id="case-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=89.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="explore-007",
            sample_id="ctrl-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=12.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="explore-008",
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
    return records, design


def test_sample_pca_variance_report_tracks_component_contribution() -> None:
    records, design = _sample_exploration_inputs()
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )

    report = build_sample_pca_variance_report(table, design)

    assert report.entity_level is QuantEntityLevel.PEPTIDE
    assert report.entries
    assert report.entries[0].component_label == "PC1"
    assert report.entries[0].explained_variance_ratio > report.entries[1].explained_variance_ratio
    assert math.isclose(
        report.entries[-1].cumulative_explained_variance_ratio,
        1.0,
        rel_tol=0.0,
        abs_tol=1e-9,
    )


def test_sample_distance_report_orders_closest_pairs_first() -> None:
    records, design = _sample_exploration_inputs()
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )

    report = build_sample_distance_report(table, design)

    assert report.sample_count == 4
    assert len(report.entries) == 6
    assert report.entries[0].sample_id_a == "case-1"
    assert report.entries[0].sample_id_b == "case-2"
    assert report.entries[0].same_condition is True
    assert report.entries[0].same_batch is True
    assert report.entries[-1].same_condition is False
    assert report.entries[-1].euclidean_distance > report.entries[0].euclidean_distance
