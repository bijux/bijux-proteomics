# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import calculate_monoisotopic_peptide_mass
from bijux_proteomics.io.precursor_validation import (
    PrecursorValidationQuery,
    PrecursorValidationTier,
    PrecursorValidationWindow,
    render_precursor_validation_entries_tsv,
    render_precursor_validation_summary_tsv,
    validate_precursor_isotope_charge,
)
from bijux_proteomics.io.spectra import SpectrumPeak

_C13_NEUTRON_SHIFT = 1.0033548378
_PROTON_MONOISOTOPIC_MASS = 1.007276466812


def _mz_from_neutral_mass(neutral_mass: float, charge: int) -> float:
    return (neutral_mass + (charge * _PROTON_MONOISOTOPIC_MASS)) / charge


def _window(precursor_id: str, *, rt: float, monoisotopic_mz: float, charge: int) -> (
    PrecursorValidationWindow
):
    return PrecursorValidationWindow(
        precursor_id=precursor_id,
        rt=rt,
        peaks=(
            SpectrumPeak(mz=monoisotopic_mz, intensity=1200.0),
            SpectrumPeak(
                mz=monoisotopic_mz + (_C13_NEUTRON_SHIFT / charge),
                intensity=540.0,
            ),
            SpectrumPeak(
                mz=monoisotopic_mz + ((2 * _C13_NEUTRON_SHIFT) / charge),
                intensity=210.0,
            ),
            SpectrumPeak(mz=monoisotopic_mz + 4.0, intensity=55.0),
        ),
    )


def test_validate_precursor_isotope_charge_flags_charge_mismatch_from_charge_two_pattern() -> (
    None
):
    peptide_mass = calculate_monoisotopic_peptide_mass("PEPTIDE")
    monoisotopic_mz = _mz_from_neutral_mass(peptide_mass, charge=2)
    report = validate_precursor_isotope_charge(
        (
            _window(
                "precursor-charge-mismatch",
                rt=120.0,
                monoisotopic_mz=monoisotopic_mz,
                charge=2,
            ),
        ),
        (
            PrecursorValidationQuery(
                precursor_id="precursor-charge-mismatch",
                assigned_mz=monoisotopic_mz,
                assigned_charge=3,
                rt=120.0,
                peptide_mass=peptide_mass,
            ),
        ),
    )

    entry = report.entries[0]

    assert entry.assigned_charge == 3
    assert entry.inferred_charge == 2
    assert entry.charge_mismatch is True
    assert entry.precursor_validation_tier is PrecursorValidationTier.CHARGE_MISMATCH
    assert entry.isotope_spacing_error < 1e-4
    assert entry.monoisotope_fit_score > 0.95


def test_validate_precursor_isotope_charge_preserves_validated_and_unsupported_rows() -> (
    None
):
    peptide_mass = calculate_monoisotopic_peptide_mass("PEPTIDE")
    monoisotopic_mz = _mz_from_neutral_mass(peptide_mass, charge=2)
    report = validate_precursor_isotope_charge(
        (
            _window(
                "precursor-validated",
                rt=60.0,
                monoisotopic_mz=monoisotopic_mz,
                charge=2,
            ),
        ),
        (
            PrecursorValidationQuery(
                precursor_id="precursor-validated",
                assigned_mz=monoisotopic_mz,
                assigned_charge=2,
                rt=60.0,
                peptide_mass=peptide_mass,
            ),
            PrecursorValidationQuery(
                precursor_id="precursor-missing",
                assigned_mz=monoisotopic_mz,
                assigned_charge=2,
                rt=95.0,
                peptide_mass=peptide_mass,
            ),
        ),
    )

    entries_by_id = {entry.precursor_id: entry for entry in report.entries}
    validated = entries_by_id["precursor-validated"]
    missing = entries_by_id["precursor-missing"]
    entries_tsv = render_precursor_validation_entries_tsv(report)
    summary_tsv = render_precursor_validation_summary_tsv(report)

    assert validated.charge_mismatch is False
    assert validated.inferred_charge == 2
    assert validated.precursor_validation_tier is PrecursorValidationTier.VALIDATED
    assert missing.precursor_validation_tier is PrecursorValidationTier.UNSUPPORTED
    assert "precursor_id\tassigned_charge\tinferred_charge" in entries_tsv
    assert "precursor_count\tmismatch_count\tvalidated_count\tweak_count\tunsupported_count" in summary_tsv
    assert summary_tsv.splitlines()[1] == "2\t0\t1\t0\t1"
