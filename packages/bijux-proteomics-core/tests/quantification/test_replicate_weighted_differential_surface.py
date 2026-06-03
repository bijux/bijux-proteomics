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
    build_differential_abundance_report,
    build_label_free_intensity_table,
    estimate_sample_weights,
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
            feature_id="weighted-da-001",
            sample_id="control-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="weighted-da-002",
            sample_id="control-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=102.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="weighted-da-003",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=390.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="weighted-da-004",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=410.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="weighted-da-005",
            sample_id="case-3",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=40.0,
            protein_refs=("P001",),
        ),
        Ms1FeatureRecord(
            feature_id="weighted-da-006",
            sample_id="control-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=150.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="weighted-da-007",
            sample_id="control-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=152.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="weighted-da-008",
            sample_id="case-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=600.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="weighted-da-009",
            sample_id="case-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=620.0,
            protein_refs=("P002",),
        ),
        Ms1FeatureRecord(
            feature_id="weighted-da-010",
            sample_id="case-3",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=None,
            protein_refs=("P002",),
            missing_value_kind=MissingValueKind.FILTERED,
        ),
        Ms1FeatureRecord(
            feature_id="weighted-da-011",
            sample_id="control-1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=90.0,
            protein_refs=("P003",),
        ),
        Ms1FeatureRecord(
            feature_id="weighted-da-012",
            sample_id="control-2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=92.0,
            protein_refs=("P003",),
        ),
        Ms1FeatureRecord(
            feature_id="weighted-da-013",
            sample_id="case-1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=360.0,
            protein_refs=("P003",),
        ),
        Ms1FeatureRecord(
            feature_id="weighted-da-014",
            sample_id="case-2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=370.0,
            protein_refs=("P003",),
        ),
        Ms1FeatureRecord(
            feature_id="weighted-da-015",
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


def test_differential_abundance_excludes_failed_sample_from_weighted_statistics() -> (
    None
):
    table = _table()
    design = _design()
    sample_weights = estimate_sample_weights(
        table,
        design,
        (
            SampleReliabilityQcEntry(
                sample_id="case-3",
                qc_status=SampleReliabilityQcStatus.FAIL,
                blocked=True,
                status_reason_codes=("identification_rate",),
            ),
        ),
    )

    unweighted = build_differential_abundance_report(
        table,
        design,
        condition_a="control",
        condition_b="case",
    )
    weighted = build_differential_abundance_report(
        table,
        design,
        condition_a="control",
        condition_b="case",
        sample_weights_report=sample_weights,
    )

    unweighted_p001 = next(
        entry for entry in unweighted.entries if entry.entity_id == "P001"
    )
    weighted_p001 = next(
        entry for entry in weighted.entries if entry.entity_id == "P001"
    )

    assert weighted.assumption_report.sample_weighting == "reliability_weighted"
    assert sample_weights.excluded_sample_count == 1
    assert weighted_p001.log2_fold_change > unweighted_p001.log2_fold_change
    assert weighted_p001.p_value < unweighted_p001.p_value
    assert weighted_p001.uncertainty_note is not None
    assert "reliability weighting excluded" in weighted_p001.uncertainty_note
