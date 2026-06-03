# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from math import isclose

import pytest

from bijux_proteomics.chemistry import (
    amino_acid_masses,
    build_peptide_mass_report,
    calculate_sequence_average_mass,
    calculate_sequence_monoisotopic_mass,
    calculate_sequence_mz,
    free_peptide_termini,
)


def test_amino_acid_mass_table_exposes_canonical_residue_entries() -> None:
    table = amino_acid_masses()

    assert len(table) == 20
    assert table[0].residue == "A"
    assert table[-1].residue == "Y"
    assert isclose(table[0].monoisotopic_mass, 71.03711, rel_tol=0.0, abs_tol=1e-6)


def test_sequence_mass_calculators_cover_neutral_and_mz_outputs() -> None:
    assert isclose(
        calculate_sequence_monoisotopic_mass("ACD"),
        307.0838,
        rel_tol=0.0,
        abs_tol=1e-6,
    )
    assert isclose(
        calculate_sequence_average_mass("ACD"),
        307.32148,
        rel_tol=0.0,
        abs_tol=1e-6,
    )
    assert isclose(
        calculate_sequence_mz("ACD", charge=2),
        154.549176466812,
        rel_tol=0.0,
        abs_tol=1e-9,
    )


def test_peptide_mass_report_preserves_residue_contribution_order() -> None:
    report = build_peptide_mass_report("PEPTIDE", charge=2)

    assert report.sequence == "PEPTIDE"
    assert [entry.position for entry in report.residue_contributions] == list(
        range(1, 8)
    )
    assert [entry.residue for entry in report.residue_contributions] == list("PEPTIDE")
    assert isclose(report.neutral_monoisotopic_mass, 799.35994, abs_tol=1e-6)
    assert isclose(report.mz_average, 400.923666466812, abs_tol=1e-9)


def test_mass_engine_rejects_empty_or_noncanonical_sequences() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        calculate_sequence_monoisotopic_mass("")

    with pytest.raises(ValueError, match="canonical uppercase amino-acid symbols"):
        calculate_sequence_monoisotopic_mass("PEPTIDE*")


def test_mass_engine_rejects_zero_charge() -> None:
    with pytest.raises(ValueError, match="charge must be at least 1"):
        calculate_sequence_mz("PEPTIDE", charge=0)


def test_free_peptide_termini_match_water_contribution() -> None:
    termini = free_peptide_termini()

    assert isclose(
        termini.n_term_monoisotopic_mass + termini.c_term_monoisotopic_mass,
        18.01056,
        rel_tol=0.0,
        abs_tol=1e-9,
    )
    assert isclose(
        termini.n_term_average_mass + termini.c_term_average_mass,
        18.01528,
        rel_tol=0.0,
        abs_tol=1e-9,
    )
