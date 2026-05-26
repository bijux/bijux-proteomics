# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import (
    PsmRecord,
    build_protein_coverage_plot_report,
    render_protein_coverage_plot_html,
    render_protein_coverage_plot_positions_tsv,
    render_protein_coverage_plot_svg,
)


def test_protein_coverage_plot_report_keeps_positions_modifications_and_intensity() -> (
    None
):
    records = (
        PsmRecord(
            spectrum_id="scan=1",
            peptide="PEPTIDEK",
            canonical_peptide="PEPTIDEK",
            charge=2,
            score=90.0,
            intensity=1000.0,
            q_value=0.005,
            protein_refs=("P11111",),
        ),
        PsmRecord(
            spectrum_id="scan=2",
            peptide="ACDMK",
            canonical_peptide="ACDM[Oxidation]K",
            charge=2,
            score=70.0,
            intensity=500.0,
            q_value=0.02,
            protein_refs=("P11111", "P22222"),
        ),
    )

    report = build_protein_coverage_plot_report(
        records,
        protein_sequences={
            "P11111": "XXPEPTIDEKYYACDMKZZ",
            "P22222": "QQACDMKRR",
        },
        threshold=0.05,
    )

    assert report.summary.plotted_proteins == 2
    assert report.summary.total_position_rows == 3
    assert report.summary.modified_position_count == 2
    assert report.summary.shared_position_count == 2
    assert report.summary.intensity_position_count == 3
    assert report.summary.unmatched_peptide_count == 0

    p11111 = next(track for track in report.tracks if track.protein_ref == "P11111")
    modified = next(
        entry
        for entry in p11111.positions
        if entry.canonical_peptide == "ACDM[Oxidation]K"
    )
    assert modified.start_residue == 13
    assert modified.end_residue == 17
    assert modified.modified_peptide == "ACDM[Oxidation]K"
    assert modified.confidence_label.value == "moderate"
    assert modified.best_intensity == 500.0
    assert modified.shared is True

    svg = render_protein_coverage_plot_svg(report)
    html = render_protein_coverage_plot_html(report)
    positions_tsv = render_protein_coverage_plot_positions_tsv(report)

    assert svg.startswith("<svg")
    assert "ACDM[Oxidation]K" in svg
    assert html.startswith("<html>")
    assert "Protein coverage plot" in html
    assert "start_residue\tend_residue" in positions_tsv
    assert "P11111\t19\tACDM[Oxidation]K\tACDMK\tACDM[Oxidation]K\tACDMK\t13\t17" in (
        positions_tsv
    )


def test_protein_coverage_plot_report_preserves_unmatched_entries() -> None:
    records = (
        PsmRecord(
            spectrum_id="scan=missing",
            peptide="MISMATCH",
            canonical_peptide="MISMATCH",
            charge=2,
            score=20.0,
            q_value=0.03,
            protein_refs=("P99999",),
        ),
    )

    report = build_protein_coverage_plot_report(
        records,
        protein_sequences={"P99999": "PEPTIDEONLY"},
        threshold=0.05,
    )

    assert report.summary.total_position_rows == 0
    assert report.summary.unmatched_peptide_count == 1
    assert report.unmatched_entries[0].protein_ref == "P99999"
    assert report.unmatched_entries[0].canonical_peptide == "MISMATCH"
