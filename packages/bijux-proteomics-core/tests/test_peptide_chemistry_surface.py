# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from math import isclose
from pathlib import Path

import pytest

from bijux_proteomics import (
    FragmentIonSeries,
    MassType,
    ModificationPosition,
    StaticModification,
    VariableModification,
    build_modification_registry,
    calculate_average_peptide_mass,
    calculate_fragment_ions,
    calculate_monoisotopic_peptide_mass,
    calculate_peptide_mz,
    get_modification,
    load_modification_registry,
    modification_registry,
    parse_modified_peptide,
)


def _modification_fixture(name: str) -> Path:
    return (
        Path(__file__).parent
        / "fixtures"
        / "modifications"
        / name
    )


def test_mass_calculators_cover_monoisotopic_average_and_mz() -> None:
    mono_mass = calculate_monoisotopic_peptide_mass("ACD")
    average_mass = calculate_average_peptide_mass("ACD")
    precursor_mz = calculate_peptide_mz("ACD", charge=2)

    assert isclose(mono_mass, 307.0838, rel_tol=0.0, abs_tol=1e-6)
    assert isclose(average_mass, 307.32148, rel_tol=0.0, abs_tol=1e-6)
    assert isclose(precursor_mz, 154.549176466812, rel_tol=0.0, abs_tol=1e-9)


def test_static_modification_model_applies_residue_delta() -> None:
    carbamidomethyl = StaticModification(
        name="Carbamidomethyl",
        residues=("C",),
        position=ModificationPosition.ANYWHERE,
        mass_delta_monoisotopic=57.021464,
        mass_delta_average=57.05132,
    )

    modified_mass = calculate_monoisotopic_peptide_mass(
        "ACD",
        static_modifications=(carbamidomethyl,),
    )

    assert isclose(modified_mass, 364.105264, rel_tol=0.0, abs_tol=1e-6)


def test_variable_modification_registry_and_parser_support_named_and_delta_notation() -> None:
    registry = modification_registry()

    named = parse_modified_peptide("M[Oxidation]PEPTIDE", registry=registry)
    delta = parse_modified_peptide("M[+15.994915]PEPTIDE", registry=registry)
    terminal = parse_modified_peptide("[Acetyl]-PEPTIDE", registry=registry)

    assert named.sequence == "MPEPTIDE"
    assert named.modifications[0].name == "Oxidation"
    assert delta.modifications[0].source == "delta"
    assert terminal.modifications[0].site is ModificationPosition.PEPTIDE_N_TERM
    assert terminal.canonical_notation == "[Acetyl]-PEPTIDE"


def test_modification_registry_loader_accepts_valid_fixture_and_rejects_invalid_fixture() -> None:
    valid_registry = load_modification_registry(_modification_fixture("valid_registry.json"))

    assert valid_registry.static_modifications[0].name == "Carbamidomethyl"
    assert valid_registry.variable_modifications[0].max_occurrences == 2

    with pytest.raises(ValueError, match="invalid modification residues"):
        load_modification_registry(_modification_fixture("invalid_registry.json"))


def test_get_modification_returns_built_in_definitions() -> None:
    phospho = get_modification("Phospho")

    assert phospho.name == "Phospho"
    assert phospho.residues == ("S", "T", "Y")
    assert phospho.neutral_losses[0].name == "phosphoric_acid"


def test_fragment_ion_calculator_emits_b_and_y_series() -> None:
    ions = calculate_fragment_ions(
        "ACDE",
        charges=(1,),
        series=(FragmentIonSeries.B, FragmentIonSeries.Y),
    )

    b1 = next(ion for ion in ions if ion.series is FragmentIonSeries.B and ion.ordinal == 1)
    y1 = next(ion for ion in ions if ion.series is FragmentIonSeries.Y and ion.ordinal == 1)

    assert isclose(b1.mz_monoisotopic, 72.044386466812, rel_tol=0.0, abs_tol=1e-9)
    assert isclose(y1.mz_monoisotopic, 148.060426466812, rel_tol=0.0, abs_tol=1e-9)


def test_fragment_ions_support_water_and_ammonia_losses() -> None:
    ions = calculate_fragment_ions(
        "STNQ",
        charges=(1,),
        include_neutral_losses=True,
    )

    water_loss = [
        ion
        for ion in ions
        if ion.neutral_loss == "water" and ion.series is FragmentIonSeries.B and ion.ordinal == 1
    ]
    ammonia_loss = [
        ion
        for ion in ions
        if ion.neutral_loss == "ammonia" and ion.series is FragmentIonSeries.Y and ion.ordinal == 1
    ]

    assert water_loss
    assert ammonia_loss


def test_fragment_ions_carry_modification_mass_shift_on_correct_side() -> None:
    registry = modification_registry()
    peptide = parse_modified_peptide("ACDM[Oxidation]P", registry=registry)

    ions = calculate_fragment_ions(
        peptide,
        charges=(1,),
        series=(FragmentIonSeries.B,),
        registry=registry,
    )

    b3 = next(ion for ion in ions if ion.ordinal == 3)
    b4 = next(ion for ion in ions if ion.ordinal == 4)

    assert isclose(
        b4.mz_monoisotopic - b3.mz_monoisotopic,
        147.035405,
        rel_tol=0.0,
        abs_tol=1e-6,
    )


def test_build_modification_registry_creates_stable_document() -> None:
    registry = build_modification_registry(
        static_modifications=(
            StaticModification(
                name="Carbamidomethyl",
                residues=("C",),
                mass_delta_monoisotopic=57.021464,
                mass_delta_average=57.05132,
            ),
        ),
        variable_modifications=(
            VariableModification(
                name="Oxidation",
                residues=("M",),
                mass_delta_monoisotopic=15.994915,
                mass_delta_average=15.9994,
                max_occurrences=3,
            ),
        ),
    )

    assert registry.document_schema.document_kind == "peptide_modification_registry"
    assert registry.document_schema.content_hash is not None


def test_modified_peptide_parser_rejects_invalid_site_assignment() -> None:
    with pytest.raises(ValueError, match="not valid on residue"):
        parse_modified_peptide("M[Phospho]PEPTIDE", registry=modification_registry())


def test_mz_calculator_rejects_invalid_charge() -> None:
    with pytest.raises(ValueError, match="charge must be at least 1"):
        calculate_peptide_mz("PEPTIDE", charge=0, mass_type=MassType.MONOISOTOPIC)
