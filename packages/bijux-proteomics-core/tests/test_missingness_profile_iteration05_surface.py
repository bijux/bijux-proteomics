# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
)
from bijux_proteomics.quantification_iteration05 import (
    MissingnessMechanismKind,
    build_missingness_mechanism_profile_report,
)


def _table_and_design() -> tuple:
    records = (
        Ms1FeatureRecord(feature_id="m-001", sample_id="a1", peptide="PEPA", canonical_peptide="PEPA", intensity=500.0, protein_refs=("P1",), missing_value_kind=MissingValueKind.OBSERVED),
        Ms1FeatureRecord(feature_id="m-002", sample_id="a2", peptide="PEPA", canonical_peptide="PEPA", intensity=520.0, protein_refs=("P1",), missing_value_kind=MissingValueKind.OBSERVED),
        Ms1FeatureRecord(feature_id="m-003", sample_id="b1", peptide="PEPA", canonical_peptide="PEPA", intensity=None, protein_refs=("P1",), missing_value_kind=MissingValueKind.NOT_OBSERVED),
        Ms1FeatureRecord(feature_id="m-004", sample_id="b2", peptide="PEPA", canonical_peptide="PEPA", intensity=None, protein_refs=("P1",), missing_value_kind=MissingValueKind.NOT_OBSERVED),
        Ms1FeatureRecord(feature_id="m-005", sample_id="a1", peptide="PEPB", canonical_peptide="PEPB", intensity=300.0, protein_refs=("P2",), missing_value_kind=MissingValueKind.OBSERVED),
        Ms1FeatureRecord(feature_id="m-006", sample_id="a2", peptide="PEPB", canonical_peptide="PEPB", intensity=320.0, protein_refs=("P2",), missing_value_kind=MissingValueKind.OBSERVED),
        Ms1FeatureRecord(feature_id="m-007", sample_id="b1", peptide="PEPB", canonical_peptide="PEPB", intensity=310.0, protein_refs=("P2",), missing_value_kind=MissingValueKind.OBSERVED),
        Ms1FeatureRecord(feature_id="m-008", sample_id="b2", peptide="PEPB", canonical_peptide="PEPB", intensity=None, protein_refs=("P2",), missing_value_kind=MissingValueKind.NOT_OBSERVED),
    )
    design = (
        ExperimentalDesignEntry(sample_id="a1", condition="case", replicate=1, fraction=1, spectra_file="a1.mzml", batch="b1"),
        ExperimentalDesignEntry(sample_id="a2", condition="case", replicate=2, fraction=1, spectra_file="a2.mzml", batch="b1"),
        ExperimentalDesignEntry(sample_id="b1", condition="ctrl", replicate=1, fraction=1, spectra_file="b1.mzml", batch="b2"),
        ExperimentalDesignEntry(sample_id="b2", condition="ctrl", replicate=2, fraction=1, spectra_file="b2.mzml", batch="b2"),
    )
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )
    return table, design


def test_missingness_mechanism_profile_report_classifies_sparse_and_technical_patterns() -> None:
    table, design = _table_and_design()
    report = build_missingness_mechanism_profile_report(table, design_entries=design)

    by_entity = {entry.entity_id: entry for entry in report.entries}
    assert by_entity["PEPA"].mechanism is MissingnessMechanismKind.SPARSE_BIOLOGY_CANDIDATE
    assert by_entity["PEPB"].mechanism is MissingnessMechanismKind.TECHNICAL_FAILURE
    assert report.summary_counts[MissingnessMechanismKind.SPARSE_BIOLOGY_CANDIDATE] >= 1
