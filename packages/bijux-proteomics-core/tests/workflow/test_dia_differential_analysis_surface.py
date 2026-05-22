# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow.dia_differential_analysis import (
    DiaDifferentialSourceKind,
    build_diann_differential_input_report,
)


def _diann_fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
        / name
    )


def test_build_diann_differential_input_report_preserves_sample_matrix() -> None:
    report = build_diann_differential_input_report(
        _diann_fixture("diann_differential_report.tsv")
    )

    assert report.source_kind is DiaDifferentialSourceKind.DIANN
    assert report.source_name == "DIA-NN"
    assert report.matrix_summary.entity_count == 3
    assert report.matrix_summary.sample_count == 4
    assert report.matrix_summary.observed_cell_count == 12
    assert report.matrix_summary.missing_cell_count == 0
    assert report.table.sample_ids == ("C1", "C2", "T1", "T2")
    assert report.table.entity_ids == ("PG001", "PG002", "PG003")
    assert report.table.entity_protein_refs["PG001"] == ("P11111",)
    assert report.table.entity_member_peptides["PG002"] == ("ACDM[Oxidation]K",)
    values = {
        (value.entity_id, value.sample_id): value
        for value in report.table.values
    }
    assert values[("PG001", "T2")].abundance == 420000.0
    assert values[("PG001", "T2")].source_feature_count == 1
    assert values[("PG003", "C1")].abundance == 200000.0
    assert "DIA-NN rollup evidence" in report.note
