# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import FragmentIonSeries, calculate_fragment_ions, parse_modified_peptide
from bijux_proteomics.io.spectra import SpectrumPeak
from bijux_proteomics.ptm.fragment_scoring import (
    render_ptm_fragment_scores_tsv,
    score_ptm_fragments,
)


def test_ptm_fragment_scoring_separates_phosphate_neutral_loss_from_site_determining_support() -> (
    None
):
    peptide = parse_modified_peptide("AS[Phospho]TYK")
    ions = calculate_fragment_ions(
        peptide,
        charges=(1,),
        series=(FragmentIonSeries.B,),
        include_neutral_losses=True,
    )
    b2 = next(
        ion
        for ion in ions
        if ion.series is FragmentIonSeries.B and ion.ordinal == 2 and ion.neutral_loss is None
    )
    b2_neutral_loss = next(
        ion
        for ion in ions
        if ion.series is FragmentIonSeries.B
        and ion.ordinal == 2
        and ion.neutral_loss == "phosphoric_acid"
    )
    b3 = next(
        ion
        for ion in ions
        if ion.series is FragmentIonSeries.B and ion.ordinal == 3 and ion.neutral_loss is None
    )

    rows = score_ptm_fragments(
        peptide,
        (
            SpectrumPeak(mz=b2.mz_monoisotopic, intensity=120.0),
            SpectrumPeak(mz=b2_neutral_loss.mz_monoisotopic, intensity=95.0),
            SpectrumPeak(mz=b3.mz_monoisotopic, intensity=80.0),
        ),
        tolerance=0.01,
        charges=(1,),
        series=(FragmentIonSeries.B,),
    )
    rendered = render_ptm_fragment_scores_tsv(rows)
    by_id = {row.ion_id: row for row in rows}

    assert by_id["b2+1"].site_determining is True
    assert by_id["b2+1-phosphoric_acid"].neutral_loss == "phosphoric_acid"
    assert by_id["b2+1-phosphoric_acid"].site_determining is False
    assert by_id["b3+1"].site_determining is False
    assert "site_determining" in rendered


def test_ptm_fragment_scoring_returns_no_rows_when_no_peaks_support_theoretical_ions() -> None:
    rows = score_ptm_fragments(
        "AS[Phospho]TYK",
        (
            SpectrumPeak(mz=100.0, intensity=50.0),
            SpectrumPeak(mz=250.0, intensity=30.0),
        ),
        tolerance=0.01,
        charges=(1,),
        series=(FragmentIonSeries.B,),
    )

    assert rows == ()
