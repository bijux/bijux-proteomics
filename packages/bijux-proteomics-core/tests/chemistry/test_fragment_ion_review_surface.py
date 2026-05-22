# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import (
    FragmentIonSeries,
    build_fragment_ion_review_report,
    render_fragment_ion_report_tsv,
)


def test_fragment_ion_review_report_covers_a_b_y_charges_losses_and_modifications() -> (
    None
):
    report = build_fragment_ion_review_report(
        "PEPM[Oxidation]TIDE",
        charges=(1, 2, 3),
        series=(FragmentIonSeries.A, FragmentIonSeries.B, FragmentIonSeries.Y),
        include_neutral_losses=True,
    )

    assert report.canonical_notation == "PEPM[Oxidation]TIDE"
    assert report.fragment_ion_count > 0
    assert report.counts_by_series["a"] > 0
    assert report.counts_by_series["b"] > 0
    assert report.counts_by_series["y"] > 0
    assert report.counts_by_charge["1"] > 0
    assert report.counts_by_charge["2"] > 0
    assert report.counts_by_charge["3"] > 0
    assert report.neutral_loss_count > 0
    assert any(ion.neutral_loss is not None for ion in report.ions)
    assert any(
        ion.series is FragmentIonSeries.A and ion.span_start == 1 for ion in report.ions
    )


def test_fragment_ion_report_tsv_renders_expected_columns() -> None:
    report = build_fragment_ion_review_report("PEPTIDE", charges=(1, 2))
    rendered = render_fragment_ion_report_tsv(report)

    assert "series\tordinal\tcharge\tspan_start\tspan_end\tsequence" in rendered
    assert "b\t1\t1\t1\t1\tP" in rendered
    assert "mz_monoisotopic" in rendered
