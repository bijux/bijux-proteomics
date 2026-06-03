# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from typing import cast

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
from bijux_proteomics.quantification.power_estimation import (
    PowerEstimationPolicy,
    build_power_estimation_report,
    render_power_effect_size_grid_tsv,
    render_power_variance_tsv,
)


def _records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="pow-001",
            sample_id="c1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pow-002",
            sample_id="c2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pow-003",
            sample_id="t1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=145.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pow-004",
            sample_id="t2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=155.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pow-005",
            sample_id="c1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=300.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pow-006",
            sample_id="c2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=420.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pow-007",
            sample_id="t1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=330.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pow-008",
            sample_id="t2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=470.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pow-009",
            sample_id="c1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=70.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pow-010",
            sample_id="t1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=90.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="pow-011",
            sample_id="t2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=95.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="c1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="c2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="t1",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="t2",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="t2.mzml",
        ),
    )


def _table() -> LabelFreeQuantTable:
    return cast(
        LabelFreeQuantTable,
        build_label_free_intensity_table(
            _records(),
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
    )


def test_power_estimation_report_builds_variance_table_and_effect_grid() -> None:
    report = build_power_estimation_report(
        _table(),
        _design(),
        policy=PowerEstimationPolicy(candidate_replicates_per_condition=(2, 4, 6)),
    )

    assert report.summary.entity_level is QuantEntityLevel.PROTEIN
    assert report.summary.evaluated_entity_count >= 2
    assert report.summary.weaker_power_with_fewer_replicates is True
    assert len(report.variance_entries) >= 2
    assert len(report.effect_size_grid) == 3
    by_replicates = {
        entry.replicates_per_condition: entry for entry in report.effect_size_grid
    }
    assert (
        by_replicates[2].median_detectable_log2_fold_change
        > by_replicates[4].median_detectable_log2_fold_change
    )
    assert (
        by_replicates[4].median_detectable_log2_fold_change
        > by_replicates[6].median_detectable_log2_fold_change
    )
    assert "pooled_log2_variance" in render_power_variance_tsv(report)
    assert "median_detectable_log2_fold_change" in render_power_effect_size_grid_tsv(
        report
    )


def test_power_estimation_report_uses_global_variance_fallback_without_design() -> None:
    report = build_power_estimation_report(
        _table(),
        (),
        policy=PowerEstimationPolicy(candidate_replicates_per_condition=(2, 3)),
    )

    assert report.variance_entries
    assert all(
        entry.contributing_condition_count == 1 for entry in report.variance_entries
    )
    assert not any(
        entry.used_global_variance_fallback for entry in report.variance_entries
    )
    assert report.effect_size_grid


def test_power_estimation_report_accepts_canonical_quant_matrix_input() -> None:
    report = build_power_estimation_report(
        _table().to_quant_matrix(),
        _design(),
        policy=PowerEstimationPolicy(candidate_replicates_per_condition=(2, 5)),
    )

    assert report.summary.sample_count == 4
    assert report.effect_size_grid[0].replicates_per_condition == 2
