# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    build_missingness_condition_summary_report,
    build_missingness_entity_summary_report,
)


def _table_and_design():
    records = (
        Ms1FeatureRecord(
            feature_id="ma-001",
            sample_id="a1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=500.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="ma-002",
            sample_id="a2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=520.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="ma-003",
            sample_id="b1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=None,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="ma-004",
            sample_id="b2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=None,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="ma-005",
            sample_id="a1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=300.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="ma-006",
            sample_id="a2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=0.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.ZERO,
        ),
        Ms1FeatureRecord(
            feature_id="ma-007",
            sample_id="b1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=310.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="ma-008",
            sample_id="b2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=None,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.FILTERED,
        ),
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="a1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="a1.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="a2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="a2.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="b1",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="b1.mzml",
            batch="b2",
        ),
        ExperimentalDesignEntry(
            sample_id="b2",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="b2.mzml",
            batch="b2",
        ),
    )
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )
    return table, design


def test_missingness_entity_summary_reports_per_entity_burden() -> None:
    table, _ = _table_and_design()
    report = build_missingness_entity_summary_report(table)

    by_entity = {entry.entity_id: entry for entry in report.entries}
    assert by_entity["PEPA"].observed_sample_count == 2
    assert by_entity["PEPA"].not_observed_sample_count == 2
    assert by_entity["PEPA"].missing_fraction == 0.5
    assert by_entity["PEPB"].zero_sample_count == 1
    assert by_entity["PEPB"].filtered_sample_count == 1


def test_missingness_condition_summary_reports_condition_specific_absence() -> None:
    table, design = _table_and_design()
    report = build_missingness_condition_summary_report(
        table,
        design_entries=design,
    )

    by_condition = {entry.condition: entry for entry in report.entries}
    assert by_condition["case"].missing_fraction == 0.0
    assert by_condition["ctrl"].not_observed_value_count == 2
    assert by_condition["ctrl"].filtered_value_count == 1
    assert by_condition["ctrl"].condition_specific_absence_entity_ids == ("PEPA",)
