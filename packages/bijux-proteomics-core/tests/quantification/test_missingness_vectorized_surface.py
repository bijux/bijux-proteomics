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
)
from bijux_proteomics.quantification.contracts.matrix_models import (
    LabelFreeQuantTable,
)
from bijux_proteomics.quantification.missingness.missingness import (
    _build_missingness_condition_summary_report_pure,
    _build_missingness_condition_summary_report_vectorized,
    _build_missingness_entity_summary_report_pure,
    _build_missingness_entity_summary_report_vectorized,
    _build_missingness_intensity_dependence_report_pure,
    _build_missingness_intensity_dependence_report_vectorized,
    _summarize_missing_values_pure,
    _summarize_missing_values_vectorized,
)


def _table_and_design() -> tuple[
    LabelFreeQuantTable, tuple[ExperimentalDesignEntry, ...]
]:
    records = (
        Ms1FeatureRecord(
            feature_id="mv-001",
            sample_id="a1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=500.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mv-002",
            sample_id="a2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=520.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mv-003",
            sample_id="b1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=None,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mv-004",
            sample_id="b2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=None,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mv-005",
            sample_id="a1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=300.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mv-006",
            sample_id="a2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=0.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.ZERO,
        ),
        Ms1FeatureRecord(
            feature_id="mv-007",
            sample_id="b1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=310.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mv-008",
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


def test_vectorized_missingness_reports_match_pure_reference_paths() -> None:
    table, design = _table_and_design()

    pure_entity = _build_missingness_entity_summary_report_pure(table)
    vectorized_entity = _build_missingness_entity_summary_report_vectorized(table)
    assert pure_entity.model_dump() == vectorized_entity.model_dump()

    pure_condition = _build_missingness_condition_summary_report_pure(
        table,
        design_entries=design,
    )
    vectorized_condition = _build_missingness_condition_summary_report_vectorized(
        table,
        design_entries=design,
    )
    assert pure_condition.model_dump() == vectorized_condition.model_dump()

    pure_intensity = _build_missingness_intensity_dependence_report_pure(table)
    vectorized_intensity = _build_missingness_intensity_dependence_report_vectorized(
        table
    )
    assert pure_intensity.model_dump() == vectorized_intensity.model_dump()

    pure_summary = _summarize_missing_values_pure(table)
    vectorized_summary = _summarize_missing_values_vectorized(table)
    assert pure_summary.model_dump() == vectorized_summary.model_dump()
