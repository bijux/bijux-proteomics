# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import build_diann_vs_dda_psm_comparison_report


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_build_diann_vs_dda_psm_comparison_report_keeps_protein_overlap_visible() -> None:
    report = build_diann_vs_dda_psm_comparison_report(
        _workflow_fixture("dia_dda_comparison_diann.tsv"),
        _workflow_fixture("dia_dda_comparison_dda_psms.tsv"),
    )

    assert report.summary.dia_protein_count == 3
    assert report.summary.dda_protein_count == 3
    assert report.summary.shared_protein_count == 2
    assert report.summary.dia_only_protein_count == 1
    assert report.summary.dda_only_protein_count == 1
    assert report.protein_overlap[0].protein_ref == "P11111"
    assert report.protein_overlap[0].overlap_class == "shared"
    dia_only_entry = next(
        entry
        for entry in report.protein_overlap
        if entry.protein_ref == "P55555"
    )
    assert dia_only_entry.overlap_class == "dia_only"
    assert dia_only_entry.dia_total_intensity == 2000000.0
    dda_only_entry = next(
        entry
        for entry in report.protein_overlap
        if entry.protein_ref == "P33333"
    )
    assert dda_only_entry.overlap_class == "dda_only"
    assert dda_only_entry.dda_total_intensity == 1340000.0
