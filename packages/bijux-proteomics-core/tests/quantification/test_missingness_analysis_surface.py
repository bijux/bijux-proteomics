# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    build_missingness_classifier_report,
    build_missingness_condition_summary_report,
    build_missingness_entity_summary_report,
    build_missingness_intensity_dependence_report,
    classify_missingness,
)


def _table_and_design() -> tuple[
    LabelFreeQuantTable,
    tuple[ExperimentalDesignEntry, ...],
]:
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


def test_missingness_intensity_dependence_report_exposes_plot_points_and_bins() -> None:
    records = (
        Ms1FeatureRecord(
            feature_id="mid-001",
            sample_id="s1",
            peptide="HIGHPEP",
            canonical_peptide="HIGHPEP",
            intensity=2048.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mid-002",
            sample_id="s2",
            peptide="HIGHPEP",
            canonical_peptide="HIGHPEP",
            intensity=1980.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mid-003",
            sample_id="s3",
            peptide="HIGHPEP",
            canonical_peptide="HIGHPEP",
            intensity=2100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mid-004",
            sample_id="s4",
            peptide="HIGHPEP",
            canonical_peptide="HIGHPEP",
            intensity=2000.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mid-005",
            sample_id="s1",
            peptide="MIDPEP",
            canonical_peptide="MIDPEP",
            intensity=256.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mid-006",
            sample_id="s2",
            peptide="MIDPEP",
            canonical_peptide="MIDPEP",
            intensity=240.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mid-007",
            sample_id="s3",
            peptide="MIDPEP",
            canonical_peptide="MIDPEP",
            intensity=None,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mid-008",
            sample_id="s4",
            peptide="MIDPEP",
            canonical_peptide="MIDPEP",
            intensity=250.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mid-009",
            sample_id="s1",
            peptide="LOWPEP",
            canonical_peptide="LOWPEP",
            intensity=32.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mid-010",
            sample_id="s2",
            peptide="LOWPEP",
            canonical_peptide="LOWPEP",
            intensity=None,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mid-011",
            sample_id="s3",
            peptide="LOWPEP",
            canonical_peptide="LOWPEP",
            intensity=None,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mid-012",
            sample_id="s4",
            peptide="LOWPEP",
            canonical_peptide="LOWPEP",
            intensity=None,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
    )
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )

    report = build_missingness_intensity_dependence_report(table, bin_count=3)

    assert len(report.plot_points) == 3
    assert len(report.bins) == 3
    assert report.trend_correlation is not None
    assert report.intensity_dependent_missingness_detected is True
    assert report.plot_points[0].entity_id == "LOWPEP"
    assert report.plot_points[-1].entity_id == "HIGHPEP"


def test_missingness_classifier_report_distinguishes_condition_specific_and_random_patterns() -> (
    None
):
    table, design = _table_and_design()

    report = build_missingness_classifier_report(
        table,
        design_entries=design,
    )

    mechanism_by_entity = {
        entry.entity_id: entry for entry in report.mechanism_report.entries
    }

    assert report.sample_summary.entries
    assert report.entity_summary.entries
    assert report.condition_summary.entries
    assert report.intensity_dependence.bins
    assert mechanism_by_entity["PEPA"].mechanism.value == "condition_specific_absence"
    assert mechanism_by_entity["PEPA"].missing_conditions == ("ctrl",)
    assert mechanism_by_entity["PEPB"].mechanism.value == "likely_technical_failure"

    random_table = build_label_free_intensity_table(
        (
            Ms1FeatureRecord(
                feature_id="rand-001",
                sample_id="a1",
                peptide="PEPC",
                canonical_peptide="PEPC",
                intensity=200.0,
                protein_refs=("P3",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="rand-002",
                sample_id="a2",
                peptide="PEPC",
                canonical_peptide="PEPC",
                intensity=None,
                protein_refs=("P3",),
                missing_value_kind=MissingValueKind.NOT_OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="rand-003",
                sample_id="b1",
                peptide="PEPC",
                canonical_peptide="PEPC",
                intensity=210.0,
                protein_refs=("P3",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="rand-004",
                sample_id="b2",
                peptide="PEPC",
                canonical_peptide="PEPC",
                intensity=None,
                protein_refs=("P3",),
                missing_value_kind=MissingValueKind.NOT_OBSERVED,
            ),
        ),
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )
    random_report = build_missingness_classifier_report(
        random_table,
        design_entries=design,
    )
    random_entry = random_report.mechanism_report.entries[0]
    assert random_entry.mechanism.value == "missing_completely_at_random"


def test_classify_missingness_preserves_condition_specific_absence_outside_random_bucket() -> (
    None
):
    table, design = _table_and_design()

    condition_summary = build_missingness_condition_summary_report(
        table,
        design_entries=design,
    )
    classification = classify_missingness(table, design)
    labels = {entry.entity_id: entry.label.value for entry in classification.entries}

    ctrl_entry = next(
        entry for entry in condition_summary.entries if entry.condition == "ctrl"
    )

    assert ctrl_entry.condition_specific_absence_entity_ids == ("PEPA",)
    assert labels["PEPA"] == "condition_specific"
    assert labels["PEPA"] != "random"
