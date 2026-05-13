# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import calculate_peptide_mz
from bijux_proteomics.io.spectra import (
    PrecursorMassErrorQuery,
    build_precursor_mass_error_report,
    render_precursor_mass_error_distribution_tsv,
    render_precursor_mass_error_observations_tsv,
    render_precursor_mass_error_summary_tsv,
)


def test_precursor_mass_error_report_covers_charge_da_ppm_and_isotope_offsets() -> None:
    peptide = "PEPTIDE"
    theoretical_z2 = calculate_peptide_mz(peptide, charge=2)
    theoretical_z3 = calculate_peptide_mz(peptide, charge=3)
    isotope_delta_z2 = 1.0033548378 / 2.0

    report = build_precursor_mass_error_report(
        (
            PrecursorMassErrorQuery(
                spectrum_id="scan=1",
                peptide=peptide,
                observed_mz=theoretical_z2 * (1.0 + (2.0 / 1_000_000.0)),
                charge=2,
            ),
            PrecursorMassErrorQuery(
                spectrum_id="scan=2",
                peptide=peptide,
                observed_mz=theoretical_z3 * (1.0 - (8.0 / 1_000_000.0)),
                charge=3,
            ),
            PrecursorMassErrorQuery(
                spectrum_id="scan=3",
                peptide="PEPM[Oxidation]IDE",
                observed_mz=calculate_peptide_mz("PEPM[Oxidation]IDE", charge=2)
                + isotope_delta_z2,
                charge=2,
            ),
        )
    )

    assert report.observation_count == 3
    assert any(row.bucket == "2" and row.count == 2 for row in report.charge_distribution)
    assert any(
        row.bucket == "0-5" and row.count == 1 for row in report.ppm_error_distribution
    )
    assert any(
        row.bucket == "50+" and row.count == 1 for row in report.ppm_error_distribution
    )
    assert any(
        row.bucket == "1" and row.count == 1
        for row in report.isotope_offset_distribution
    )

    first = report.observations[0]
    assert round(first.delta_ppm, 3) == 2.0
    assert first.charge == 2

    third = report.observations[2]
    assert third.canonical_peptide == "PEPM[Oxidation]IDE"
    assert third.isotope_offset_advisory.recommended_offset == 1


def test_precursor_mass_error_renderers_emit_stable_tables() -> None:
    theoretical = calculate_peptide_mz("PEPTIDE", charge=2)
    report = build_precursor_mass_error_report(
        (
            PrecursorMassErrorQuery(
                spectrum_id="scan=10",
                peptide="PEPTIDE",
                observed_mz=theoretical,
                charge=2,
            ),
        )
    )

    summary_tsv = render_precursor_mass_error_summary_tsv(report)
    observations_tsv = render_precursor_mass_error_observations_tsv(report.observations)
    distribution_tsv = render_precursor_mass_error_distribution_tsv(
        report.ppm_error_distribution,
        distribution_name="abs_ppm",
    )

    assert "observation_count" in summary_tsv
    assert "recommended_isotope_offset" in observations_tsv
    assert "distribution\tbucket\tcount" in distribution_tsv
