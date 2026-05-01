# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
)
from bijux_proteomics.quantification_iteration05 import (
    build_effect_size_first_differential_abundance_report,
)


def _table_and_design() -> tuple[
    LabelFreeQuantTable, tuple[ExperimentalDesignEntry, ...]
]:
    records = (
        Ms1FeatureRecord(
            feature_id="da-001",
            sample_id="a1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=800.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="da-002",
            sample_id="a2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=820.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="da-003",
            sample_id="b1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=200.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="da-004",
            sample_id="b2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=210.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="da-005",
            sample_id="a1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=500.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="da-006",
            sample_id="a2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=480.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="da-007",
            sample_id="b1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=450.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="da-008",
            sample_id="b2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=460.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="a1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="a1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="a2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="a2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="b1",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="b1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="b2",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="b2.mzml",
        ),
    )
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )
    return table, design


def test_effect_size_first_differential_abundance_report_ranks_entries() -> None:
    table, design = _table_and_design()
    report = build_effect_size_first_differential_abundance_report(
        table,
        design_entries=design,
        condition_a="case",
        condition_b="ctrl",
    )

    assert report.condition_a == "case"
    assert report.condition_b == "ctrl"
    assert len(report.entries) == 2
    assert abs(report.entries[0].log2_fold_change) >= abs(
        report.entries[1].log2_fold_change
    )
    assert len(report.global_caveats) >= 1
