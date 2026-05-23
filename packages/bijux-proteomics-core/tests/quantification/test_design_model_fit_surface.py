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
    build_quant_design_matrix_report,
    fit_quant_design_matrix_model,
)


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="c1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c1.mzml",
            batch="batch-a",
            pair_id="pair-a",
        ),
        ExperimentalDesignEntry(
            sample_id="t1",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t1.mzml",
            batch="batch-b",
            pair_id="pair-a",
        ),
        ExperimentalDesignEntry(
            sample_id="c2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c2.mzml",
            batch="batch-b",
            pair_id="pair-b",
        ),
        ExperimentalDesignEntry(
            sample_id="t2",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="t2.mzml",
            batch="batch-c",
            pair_id="pair-b",
        ),
        ExperimentalDesignEntry(
            sample_id="c3",
            condition="control",
            replicate=3,
            fraction=1,
            spectra_file="c3.mzml",
            batch="batch-c",
            pair_id="pair-c",
        ),
        ExperimentalDesignEntry(
            sample_id="t3",
            condition="treatment",
            replicate=3,
            fraction=1,
            spectra_file="t3.mzml",
            batch="batch-a",
            pair_id="pair-c",
        ),
    )


def _records() -> tuple[Ms1FeatureRecord, ...]:
    rows: list[Ms1FeatureRecord] = []
    p1_values = {
        "c1": 100.0,
        "t1": 200.0,
        "c2": 110.0,
        "t2": 210.0,
        "c3": 90.0,
        "t3": 220.0,
    }
    p2_values = {
        "c1": 150.0,
        "t1": 148.0,
        "c2": 152.0,
        "t2": 151.0,
        "c3": 149.0,
        "t3": 150.0,
    }
    for sample_id, intensity in p1_values.items():
        rows.append(
            Ms1FeatureRecord(
                feature_id=f"p1-{sample_id}",
                sample_id=sample_id,
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=intensity,
                protein_refs=("P001",),
                missing_value_kind=MissingValueKind.OBSERVED,
            )
        )
    for sample_id, intensity in p2_values.items():
        rows.append(
            Ms1FeatureRecord(
                feature_id=f"p2-{sample_id}",
                sample_id=sample_id,
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=intensity,
                protein_refs=("P002",),
                missing_value_kind=MissingValueKind.OBSERVED,
            )
        )
    return tuple(rows)


def test_fit_quant_design_matrix_model_reports_condition_coefficients_and_contrasts() -> (
    None
):
    table = build_label_free_intensity_table(
        _records(),
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    design_matrix = build_quant_design_matrix_report(
        _design(),
        batch_field="batch",
        pairing_field="pair_id",
    )
    report = fit_quant_design_matrix_model(table, design_matrix)

    assert report.fitted_entity_count == 2
    assert report.skipped_entity_count == 0

    coefficient_lookup = {
        (entry.entity_id, entry.coefficient_name): entry.estimate
        for entry in report.coefficient_entries
    }
    assert coefficient_lookup[("P001", "condition[treatment]")] > 0.5
    assert abs(coefficient_lookup[("P002", "condition[treatment]")]) < 0.05

    contrast_lookup = {
        (entry.entity_id, entry.contrast_name): entry.estimate
        for entry in report.contrast_estimates
    }
    assert contrast_lookup[("P001", "control_vs_treatment")] < -0.5
    assert abs(contrast_lookup[("P002", "control_vs_treatment")]) < 0.05
