# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from math import isclose

from bijux_proteomics.chemistry import (
    build_modified_peptide,
    calculate_average_peptide_mass,
    calculate_monoisotopic_peptide_mass,
    calculate_peptide_mz,
    modification_registry,
)
from bijux_proteomics.sequences import (
    PeptideProblemFlag,
    build_peptide_property_report,
    calculate_peptide_hydrophobicity_proxy,
)


def test_build_peptide_property_report_covers_mass_length_mz_and_missed_cleavages() -> (
    None
):
    report = build_peptide_property_report(
        "AKTIDEK",
        charge=3,
        protease="trypsin",
    )

    assert report.length == 7
    assert report.missed_cleavages == 1
    assert report.problem_flags == ()
    assert isclose(
        report.monoisotopic_mass,
        calculate_monoisotopic_peptide_mass("AKTIDEK"),
        rel_tol=0.0,
        abs_tol=1e-6,
    )
    assert isclose(
        report.average_mass,
        calculate_average_peptide_mass("AKTIDEK"),
        rel_tol=0.0,
        abs_tol=1e-6,
    )
    assert isclose(
        report.mz_monoisotopic,
        calculate_peptide_mz("AKTIDEK", charge=3),
        rel_tol=0.0,
        abs_tol=1e-9,
    )


def test_build_peptide_property_report_supports_modifications() -> None:
    registry = modification_registry()
    modified = build_modified_peptide(
        "MPEPTIDE",
        assignments=("Oxidation@1",),
        registry=registry,
    )

    report = build_peptide_property_report(
        "MPEPTIDE",
        modification_assignments=("Oxidation@1",),
        charge=2,
        protease="trypsin",
        registry=registry,
    )

    assert report.canonical_notation == "M[Oxidation]PEPTIDE"
    assert report.residue_sequence == "MPEPTIDE"
    assert isclose(
        report.monoisotopic_mass,
        calculate_monoisotopic_peptide_mass(modified, registry=registry),
        rel_tol=0.0,
        abs_tol=1e-6,
    )


def test_peptide_property_report_flags_hydrophobicity_and_high_missed_cleavages() -> (
    None
):
    report = build_peptide_property_report(
        "LVVVVVVIKAKK",
        charge=2,
        protease="trypsin",
    )

    assert report.missed_cleavages == 2
    assert report.flagged_problematic is True
    assert PeptideProblemFlag.HIGH_MISSED_CLEAVAGES in report.problem_flags
    assert PeptideProblemFlag.HIGH_HYDROPHOBICITY_PROXY in report.problem_flags
    assert report.hydrophobicity_proxy > 1.5


def test_hydrophobicity_proxy_rejects_empty_sequence() -> None:
    try:
        calculate_peptide_hydrophobicity_proxy("")
    except ValueError as exc:
        assert "cannot be empty" in str(exc)
    else:
        raise AssertionError("expected empty sequence to fail")
