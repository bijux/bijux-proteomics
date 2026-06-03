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
    build_multi_condition_differential_abundance_report,
)


def _table_and_design() -> tuple[
    tuple[ExperimentalDesignEntry, ...],
    tuple[Ms1FeatureRecord, ...],
]:
    design = (
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.mzml",
        ),
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
            sample_id="rescue-1",
            condition="rescue",
            replicate=1,
            fraction=1,
            spectra_file="rescue-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="rescue-2",
            condition="rescue",
            replicate=2,
            fraction=1,
            spectra_file="rescue-2.mzml",
        ),
    )
    records = (
        Ms1FeatureRecord(
            feature_id="mc-001",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=120.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-002",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=125.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-003",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=600.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-004",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=610.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-005",
            sample_id="rescue-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=300.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-006",
            sample_id="rescue-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=290.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-007",
            sample_id="ctrl-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=800.0,
            protein_refs=("P002",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-008",
            sample_id="ctrl-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=780.0,
            protein_refs=("P002",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-009",
            sample_id="case-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=200.0,
            protein_refs=("P002",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-010",
            sample_id="case-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=210.0,
            protein_refs=("P002",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-011",
            sample_id="rescue-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=500.0,
            protein_refs=("P002",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mc-012",
            sample_id="rescue-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=490.0,
            protein_refs=("P002",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    return design, records


def test_multi_condition_differential_abundance_builds_all_pairwise_reports() -> None:
    design, records = _table_and_design()
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    report = build_multi_condition_differential_abundance_report(table, design)

    assert report.condition_count == 3
    assert len(report.contrasts) == 3
    assert len(report.reports) == 3
    assert all(
        entry.adjusted_p_value is not None
        for contrast in report.reports
        for entry in contrast.entries
    )
    contrast_pairs = {
        (entry.condition_a, entry.condition_b) for entry in report.contrasts
    }
    assert contrast_pairs == {
        ("case", "control"),
        ("case", "rescue"),
        ("control", "rescue"),
    }


def test_multi_condition_differential_abundance_supports_selected_contrasts() -> None:
    design, records = _table_and_design()
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    report = build_multi_condition_differential_abundance_report(
        table,
        design,
        contrasts=(("case", "control"),),
    )

    assert len(report.contrasts) == 1
    assert report.reports[0].condition_a == "case"
    assert report.reports[0].condition_b == "control"
