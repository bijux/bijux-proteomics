# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import calculate_fragment_ions, calculate_peptide_mz
from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.psm_features import (
    extract_psm_features,
    render_psm_feature_tsv,
)
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak


def _good_spectrum(peptide: str, *, charge: int, spectrum_id: str) -> SpectrumModel:
    fragments = calculate_fragment_ions(peptide, charges=(1, 2))
    peaks = tuple(
        SpectrumPeak(mz=fragment.mz_monoisotopic, intensity=1200.0 - (index * 120.0))
        for index, fragment in enumerate(fragments[:6])
    ) + (
        SpectrumPeak(mz=150.0, intensity=40.0),
        SpectrumPeak(mz=700.0, intensity=20.0),
    )
    return SpectrumModel(
        spectrum_id=spectrum_id,
        precursor_mz=calculate_peptide_mz(peptide, charge=charge),
        precursor_charge=charge,
        peaks=peaks,
    )


def _poor_spectrum(peptide: str, *, charge: int, spectrum_id: str) -> SpectrumModel:
    return SpectrumModel(
        spectrum_id=spectrum_id,
        precursor_mz=calculate_peptide_mz(peptide, charge=charge),
        precursor_charge=charge,
        peaks=(
            SpectrumPeak(mz=111.111, intensity=1500.0),
            SpectrumPeak(mz=222.222, intensity=1400.0),
            SpectrumPeak(mz=333.333, intensity=1300.0),
            SpectrumPeak(mz=444.444, intensity=1200.0),
            SpectrumPeak(mz=555.555, intensity=1100.0),
            SpectrumPeak(mz=666.666, intensity=1000.0),
        ),
    )


def test_extract_psm_features_penalizes_high_score_but_poor_spectrum_support() -> None:
    peptide = "PEPTIDEK"
    charge = 2
    good_psm = PsmRecord(
        spectrum_id="good-scan",
        peptide=peptide,
        canonical_peptide=peptide,
        charge=charge,
        score=120.0,
        q_value=0.01,
        protein_refs=("P11111",),
        target_decoy_label=TargetDecoyLabel.TARGET,
    )
    poor_psm = PsmRecord(
        spectrum_id="poor-scan",
        peptide=peptide,
        canonical_peptide=peptide,
        charge=charge,
        score=220.0,
        q_value=0.0005,
        protein_refs=("P11111",),
        target_decoy_label=TargetDecoyLabel.TARGET,
    )
    rows = extract_psm_features(
        (good_psm, poor_psm),
        (
            _good_spectrum(peptide, charge=charge, spectrum_id="good-scan"),
            _poor_spectrum(peptide, charge=charge, spectrum_id="poor-scan"),
        ),
        {peptide: ("P11111",)},
        {"P11111": "MKWVTFISLLFLFSSAYSRPEPTIDEKAAAK"},
    )

    by_spectrum = {row.spectrum_id: row for row in rows}
    good_row = by_spectrum["good-scan"]
    poor_row = by_spectrum["poor-scan"]

    assert poor_row.score_native > good_row.score_native
    assert poor_row.q_value_native is not None
    assert good_row.q_value_native is not None
    assert poor_row.q_value_native < good_row.q_value_native
    assert good_row.matched_ion_count == 5
    assert poor_row.matched_ion_count == 0
    assert good_row.explained_intensity == 0.8791208791208791
    assert poor_row.explained_intensity == 0.0
    assert good_row.top_peak_unmatched_fraction == 0.12087912087912088
    assert poor_row.top_peak_unmatched_fraction == 1.0

    rendered = render_psm_feature_tsv(rows)
    assert "matched_ion_count" in rendered
    assert "top_peak_unmatched_fraction" in rendered


def test_extract_psm_features_uses_peptide_mapping_to_resolve_decoy_label() -> None:
    peptide = "PEPTIDEK"
    charge = 2
    psm = PsmRecord(
        spectrum_id="decoy-scan",
        peptide=peptide,
        canonical_peptide=peptide,
        charge=charge,
        score=55.0,
        q_value=0.4,
    )

    (row,) = extract_psm_features(
        (psm,),
        (_poor_spectrum(peptide, charge=charge, spectrum_id="decoy-scan"),),
        {peptide: ("DECOY_P99999",)},
        {"DECOY_P99999": "QQQPEPTIDEKRRR"},
    )

    assert row.target_decoy_label is TargetDecoyLabel.DECOY
