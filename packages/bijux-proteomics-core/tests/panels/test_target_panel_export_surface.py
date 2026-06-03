# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.panels import (
    build_diann_peptide_target_panel_report,
    render_target_panel_intensity_tsv,
    render_target_panel_matrix_tsv,
    render_target_panel_missing_tsv,
    render_target_panel_summary_tsv,
    render_target_panel_target_tsv,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def _diann_fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
        / name
    )


def test_render_target_panel_exports_keep_summary_missing_and_intensity_visible() -> (
    None
):
    report = build_diann_peptide_target_panel_report(
        _diann_fixture("diann_library_coverage.tsv"),
        _format_fixture("dia_target_panel.tsv"),
    )

    summary_tsv = render_target_panel_summary_tsv(report)
    target_tsv = render_target_panel_target_tsv(report)
    missing_tsv = render_target_panel_missing_tsv(report)
    intensity_tsv = render_target_panel_intensity_tsv(report)
    matrix_tsv = render_target_panel_matrix_tsv(report)

    assert (
        "source_kind\tsource_name\ttotal_target_count\tmatched_target_count"
        in summary_tsv
    )
    assert (
        "target_id\ttarget_kind\tmodified_peptide\texpected_charge\tmatched_entity_ids\tdetected_sample_count"
        in target_tsv
    )
    assert (
        "target_id\ttarget_kind\tmodified_peptide\texpected_charge\treason"
        in missing_tsv
    )
    assert (
        "target_id\ttarget_kind\tmatched_entity_id\tmodified_peptide\texpected_charge\tsample_id\tabundance\tdetected"
        in intensity_tsv
    )
    assert (
        "target_id\ttarget_kind\tmatched_entity_id\tpeptide_sequence\tmodified_peptide\texpected_charge\tcharge_states\tprotein_refs"
        in matrix_tsv
    )
    assert (
        "dia-missing-protein\tprotein\t\t\ttarget is absent from the selected peptide-level matrix"
        in missing_tsv
    )
    assert "dia-p22222\tprotein\t\t\tPEPGAMMA|PG002\t2" in target_tsv
    assert (
        "dia-pepalfa\tpeptide\tPEPALFA|PG001\tPEPALFA\t2\tsample_A\t1200000.0\ttrue"
        in intensity_tsv
    )
    assert (
        "dia-pepalfa\tpeptide\tPEPALFA|PG001\tPEPALFA\tPEPALFA\t2\t2\tP11111\t1200000.0"
        in matrix_tsv
    )
