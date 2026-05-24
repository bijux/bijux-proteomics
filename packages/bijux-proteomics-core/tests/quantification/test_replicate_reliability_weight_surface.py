# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    SampleReliabilityQcEntry,
    SampleReliabilityQcStatus,
    build_label_free_intensity_table,
    estimate_sample_weights,
    render_sample_reliability_weights_tsv,
)


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="control-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="control-1.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="control-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="control-2.mzml",
            batch="batch-b",
        ),
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
            batch="batch-b",
        ),
        ExperimentalDesignEntry(
            sample_id="case-3",
            condition="case",
            replicate=3,
            fraction=1,
            spectra_file="case-3.mzml",
            batch="batch-a",
        ),
    )


def _table():
    records = (
        Ms1FeatureRecord(
            feature_id="weight-001",
            sample_id="control-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="weight-002",
            sample_id="control-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=102.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="weight-003",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=390.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="weight-004",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=410.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="weight-005",
            sample_id="case-3",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=40.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="weight-006",
            sample_id="control-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=150.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="weight-007",
            sample_id="control-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=152.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="weight-008",
            sample_id="case-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=600.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="weight-009",
            sample_id="case-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=620.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="weight-010",
            sample_id="case-3",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=None,
            protein_refs=("P002",),
            missing_value_kind=MissingValueKind.FILTERED,
        ),
        Ms1FeatureRecord(
            feature_id="weight-011",
            sample_id="control-1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=90.0,
            protein_refs=("P003",),
        ),
        Ms1FeatureRecord(
            feature_id="weight-012",
            sample_id="control-2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=92.0,
            protein_refs=("P003",),
        ),
        Ms1FeatureRecord(
            feature_id="weight-013",
            sample_id="case-1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=360.0,
            protein_refs=("P003",),
        ),
        Ms1FeatureRecord(
            feature_id="weight-014",
            sample_id="case-2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=370.0,
            protein_refs=("P003",),
        ),
        Ms1FeatureRecord(
            feature_id="weight-015",
            sample_id="case-3",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=25.0,
            protein_refs=("P003",),
        ),
    )
    return build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )


def test_estimate_sample_weights_zeroes_failed_outlier_sample() -> None:
    report = estimate_sample_weights(
        _table(),
        _design(),
        (
            SampleReliabilityQcEntry(
                sample_id="case-3",
                qc_status=SampleReliabilityQcStatus.FAIL,
                blocked=True,
                status_reason_codes=("identification_rate",),
            ),
        ),
    )

    by_sample = {entry.sample_id: entry for entry in report.entries}
    rendered = render_sample_reliability_weights_tsv(report)

    assert report.low_weight_sample_count >= 1
    assert report.excluded_sample_count == 1
    assert by_sample["case-3"].reliability_weight == 0.0
    assert "failed_sample_qc" in by_sample["case-3"].low_weight_reasons
    assert "sample_exploration_outlier" in by_sample["case-3"].low_weight_reasons
    assert "high_relative_missingness" in by_sample["case-3"].low_weight_reasons
    assert by_sample["case-1"].reliability_weight > by_sample["case-3"].reliability_weight
    assert by_sample["control-1"].reliability_weight > by_sample["case-3"].reliability_weight
    assert rendered.startswith("sample_id\treliability_weight\tlow_weight_reasons\n")
    assert "case-3\t0.0000\t" in rendered
