# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow.label_based_differential_analysis import (
    LabelBasedDifferentialSourceKind,
    build_silac_differential_analysis_report,
    build_silac_differential_input_report,
)


def _fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "isotope_labeling" / name
    )


def test_build_silac_differential_input_report_preserves_protein_ratio_matrix() -> None:
    report = build_silac_differential_input_report(
        _fixture("silac_differential_features.tsv")
    )

    assert report.source_kind is LabelBasedDifferentialSourceKind.SILAC
    assert report.measurement_kind.value == "ratio"
    assert report.summary.entity_count == 3
    assert report.summary.sample_count == 4
    assert report.sample_ids == ("C1", "C2", "T1", "T2")
    row = next(row for row in report.rows if row.entity_id == "P001")
    values = {value.sample_id: value.abundance for value in row.values}
    assert values["C1"] == 1.0
    assert values["T2"] == 2.0
    assert "SILAC sample ratios" in report.note


def test_build_silac_differential_analysis_report_preserves_ratio_native_effects() -> (
    None
):
    design_report = parse_experimental_design_table(
        _fixture("silac_differential.design.tsv")
    )

    report = build_silac_differential_analysis_report(
        _fixture("silac_differential_features.tsv"),
        tuple(design_report.accepted_entries),
    )

    assert report.normalization_method.value == "median"
    assert report.design_matrix.sample_count == 4
    assert report.design_model_fit.fitted_entity_count == 3
    assert report.differential_abundance_report is not None
    differential = report.differential_abundance_report
    p001 = next(entry for entry in differential.entries if entry.entity_id == "P001")
    p002 = next(entry for entry in differential.entries if entry.entity_id == "P002")
    p003 = next(entry for entry in differential.entries if entry.entity_id == "P003")
    assert p001.log2_fold_change > 0.9
    assert p001.adjusted_p_value is not None
    assert p002.log2_fold_change < -0.9
    assert p002.adjusted_p_value is not None
    assert abs(p003.log2_fold_change) < 0.1
    assert report.volcano_plot is not None
    assert report.volcano_plot.condition_a == "control"
    assert report.volcano_plot.condition_b == "treatment"
