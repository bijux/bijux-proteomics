# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from math import isclose
from pathlib import Path

import pytest

from bijux_proteomics.chemistry import (
    AppliedModification,
    FragmentIonSeries,
    IsotopicLabelingPolicy,
    MassType,
    ModificationLocalizationState,
    ModificationPosition,
    ModificationRegistryDocument,
    ParsedModifiedPeptide,
    StaticModification,
    VariableModification,
    approximate_peptide_isotope_envelope,
    build_modification_localization_advisory,
    build_modification_registry,
    build_modified_peptide,
    build_modified_peptide_export_record,
    build_peptide_charge_state,
    calculate_average_peptide_mass,
    calculate_fragment_ions,
    calculate_modified_peptide_mass,
    calculate_monoisotopic_peptide_mass,
    calculate_peptide_mz,
    canonicalize_modified_peptide,
    enumerate_variable_modifications,
    export_modified_peptides_jsonl,
    export_modified_peptides_tsv,
    get_modification,
    load_modification_registry,
    modification_registry,
    parse_modified_peptide,
    validate_modification_registry,
    validate_modified_peptide_fragment_ions,
    validate_modified_peptide_sites,
)


def _modification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "modifications" / name


def _chemistry_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "chemistry" / name


def test_mass_calculators_cover_monoisotopic_average_and_mz() -> None:
    mono_mass = calculate_monoisotopic_peptide_mass("ACD")
    average_mass = calculate_average_peptide_mass("ACD")
    precursor_mz = calculate_peptide_mz("ACD", charge=2)

    assert isclose(mono_mass, 307.0838, rel_tol=0.0, abs_tol=1e-6)
    assert isclose(average_mass, 307.32148, rel_tol=0.0, abs_tol=1e-6)
    assert isclose(precursor_mz, 154.549176466812, rel_tol=0.0, abs_tol=1e-9)


def test_mass_calculators_match_curated_reference_fixture() -> None:
    fixture = json.loads(_chemistry_fixture("reference_masses.json").read_text())

    for case in fixture:
        assert isclose(
            calculate_monoisotopic_peptide_mass(case["sequence"]),
            case["monoisotopic_mass"],
            rel_tol=0.0,
            abs_tol=1e-6,
        )
        assert isclose(
            calculate_average_peptide_mass(case["sequence"]),
            case["average_mass"],
            rel_tol=0.0,
            abs_tol=1e-6,
        )
        assert isclose(
            calculate_peptide_mz(case["sequence"], charge=case["charge"]),
            case["mz"],
            rel_tol=0.0,
            abs_tol=1e-9,
        )


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


def test_variable_modification_registry_and_parser_support_named_and_delta_notation() -> (
    None
):
    registry = modification_registry()

    named = parse_modified_peptide("M[Oxidation]PEPTIDE", registry=registry)
    delta = parse_modified_peptide("M[+15.994915]PEPTIDE", registry=registry)
    terminal = parse_modified_peptide("[Acetyl]-PEPTIDE", registry=registry)

    assert named.sequence == "MPEPTIDE"
    assert named.modifications[0].name == "Oxidation"
    assert delta.modifications[0].source == "delta"
    assert terminal.modifications[0].site is ModificationPosition.PEPTIDE_N_TERM
    assert terminal.canonical_notation == "[Acetyl]-PEPTIDE"


def test_canonicalizer_normalizes_equivalent_named_and_delta_notation() -> None:
    registry = modification_registry()

    canonical_named = canonicalize_modified_peptide(
        "ACDM[Oxidation]K",
        registry=registry,
    )
    canonical_delta = canonicalize_modified_peptide(
        "ACDM[+15.994915]K",
        registry=registry,
    )

    assert canonical_named == "ACDM[Oxidation]K"
    assert canonical_delta == canonical_named


def test_modification_registry_loader_accepts_valid_fixture_and_rejects_invalid_fixture() -> (
    None
):
    valid_registry = load_modification_registry(
        _modification_fixture("valid_registry.json")
    )

    assert valid_registry.static_modifications[0].name == "Carbamidomethyl"
    assert valid_registry.variable_modifications[0].max_occurrences == 2

    with pytest.raises(ValueError, match="invalid modification residues"):
        load_modification_registry(_modification_fixture("invalid_registry.json"))


def test_get_modification_returns_built_in_definitions() -> None:
    phospho = get_modification("Phospho")

    assert phospho.name == "Phospho"
    assert phospho.residues == ("S", "T", "Y")
    assert phospho.neutral_losses[0].name == "phosphoric_acid"


def test_fragment_ion_calculator_emits_a_b_and_y_series_with_residue_spans() -> None:
    ions = calculate_fragment_ions(
        "ACDE",
        charges=(1,),
        series=(FragmentIonSeries.A, FragmentIonSeries.B, FragmentIonSeries.Y),
    )

    a1 = next(
        ion for ion in ions if ion.series is FragmentIonSeries.A and ion.ordinal == 1
    )
    b1 = next(
        ion for ion in ions if ion.series is FragmentIonSeries.B and ion.ordinal == 1
    )
    y1 = next(
        ion for ion in ions if ion.series is FragmentIonSeries.Y and ion.ordinal == 1
    )

    assert a1.span_start == 1
    assert a1.span_end == 1
    assert isclose(
        b1.mz_monoisotopic - a1.mz_monoisotopic,
        27.99491461957,
        rel_tol=0.0,
        abs_tol=1e-9,
    )
    assert isclose(b1.mz_monoisotopic, 72.044386466812, rel_tol=0.0, abs_tol=1e-9)
    assert isclose(y1.mz_monoisotopic, 148.060426466812, rel_tol=0.0, abs_tol=1e-9)
    assert y1.span_start == 4
    assert y1.span_end == 4


def test_fragment_ions_support_water_and_ammonia_losses() -> None:
    ions = calculate_fragment_ions(
        "STNQ",
        charges=(1,),
        include_neutral_losses=True,
    )

    water_loss = [
        ion
        for ion in ions
        if ion.neutral_loss == "water"
        and ion.series is FragmentIonSeries.B
        and ion.ordinal == 1
    ]
    ammonia_loss = [
        ion
        for ion in ions
        if ion.neutral_loss == "ammonia"
        and ion.series is FragmentIonSeries.Y
        and ion.ordinal == 1
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


def test_fragment_ions_support_charge_three_and_terminal_modifications() -> None:
    registry = modification_registry()
    peptide = build_modified_peptide(
        "PEPTIDE",
        assignments=("Acetyl@n-term", "Amidated@c-term"),
        registry=registry,
    )

    ions = calculate_fragment_ions(
        peptide,
        charges=(3,),
        series=(FragmentIonSeries.A, FragmentIonSeries.B, FragmentIonSeries.Y),
        registry=registry,
    )

    a2 = next(
        ion
        for ion in ions
        if ion.series is FragmentIonSeries.A and ion.ordinal == 2 and ion.charge == 3
    )
    b2 = next(
        ion
        for ion in ions
        if ion.series is FragmentIonSeries.B and ion.ordinal == 2 and ion.charge == 3
    )
    y2 = next(
        ion
        for ion in ions
        if ion.series is FragmentIonSeries.Y and ion.ordinal == 2 and ion.charge == 3
    )

    assert a2.span_start == 1
    assert a2.span_end == 2
    assert y2.span_start == 6
    assert y2.span_end == 7
    assert b2.mz_monoisotopic > a2.mz_monoisotopic
    assert y2.mz_monoisotopic > 0.0


def test_fragment_ion_shift_validation_matches_only_impacted_fragments() -> None:
    registry = modification_registry()
    peptide = build_modified_peptide(
        "PEMTIDE",
        assignments=("Acetyl@n-term", "Oxidation@3"),
        registry=registry,
    )

    report = validate_modified_peptide_fragment_ions(
        peptide,
        charges=(1,),
        series=(FragmentIonSeries.B, FragmentIonSeries.Y),
        registry=registry,
    )

    b1 = next(
        entry
        for entry in report.entries
        if entry.series is FragmentIonSeries.B and entry.ordinal == 1
    )
    b2 = next(
        entry
        for entry in report.entries
        if entry.series is FragmentIonSeries.B and entry.ordinal == 2
    )
    y1 = next(
        entry
        for entry in report.entries
        if entry.series is FragmentIonSeries.Y and entry.ordinal == 1
    )

    assert report.valid is True
    assert b1.shifted is True
    assert isclose(b1.expected_shift_monoisotopic, 42.010565, rel_tol=0.0, abs_tol=1e-9)
    assert b2.shifted is True
    assert isclose(
        b2.expected_shift_monoisotopic,
        42.010565,
        rel_tol=0.0,
        abs_tol=1e-9,
    )
    b3 = next(
        entry
        for entry in report.entries
        if entry.series is FragmentIonSeries.B and entry.ordinal == 3
    )
    assert b3.shifted is True
    assert isclose(
        b3.expected_shift_monoisotopic,
        58.00548,
        rel_tol=0.0,
        abs_tol=1e-9,
    )
    assert y1.shifted is False
    assert isclose(y1.observed_shift_monoisotopic, 0.0, rel_tol=0.0, abs_tol=1e-12)


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


def test_modification_registry_validation_catches_duplicate_and_conflicting_definitions() -> (
    None
):
    duplicate_registry = ModificationRegistryDocument.model_validate_json(
        _modification_fixture("invalid_duplicate_registry.json").read_text()
    )
    conflicting_registry = ModificationRegistryDocument.model_validate_json(
        _modification_fixture("invalid_conflicting_registry.json").read_text()
    )

    duplicate_report = validate_modification_registry(duplicate_registry)
    conflicting_report = validate_modification_registry(conflicting_registry)

    assert duplicate_report.valid is False
    assert duplicate_report.issues[0].code == "duplicate_modification_name"
    assert conflicting_report.valid is False
    assert conflicting_report.issues[0].code == "conflicting_controlled_id"

    with pytest.raises(ValueError, match="defined more than once"):
        load_modification_registry(
            _modification_fixture("invalid_duplicate_registry.json")
        )
    with pytest.raises(ValueError, match="conflicting registry definitions"):
        load_modification_registry(
            _modification_fixture("invalid_conflicting_registry.json")
        )


def test_modified_peptide_parser_rejects_invalid_site_assignment() -> None:
    with pytest.raises(ValueError, match="not valid on residue"):
        parse_modified_peptide("M[Phospho]PEPTIDE", registry=modification_registry())


def test_site_validation_report_exposes_invalid_assignment() -> None:
    report = validate_modified_peptide_sites(
        "M[Phospho]PEPTIDE",
        registry=modification_registry(),
    )

    assert report.valid is False
    assert report.issues[0].code == "invalid_modification_site"


def test_modified_peptide_mass_wrapper_and_charge_state_model() -> None:
    peptide = parse_modified_peptide(
        "M[Oxidation]PEPTIDE", registry=modification_registry()
    )

    neutral_mass = calculate_modified_peptide_mass(peptide)
    charge_state = build_peptide_charge_state(peptide, charge=3)

    assert isclose(neutral_mass, 946.395345, rel_tol=0.0, abs_tol=1e-6)
    assert charge_state.charge == 3
    assert isclose(charge_state.mz, 316.472391466812, rel_tol=0.0, abs_tol=1e-9)


def test_build_modified_peptide_supports_assignment_syntax() -> None:
    peptide = build_modified_peptide(
        "PESTIDE",
        assignments=("Acetyl@n-term", "Phospho@3"),
        registry=modification_registry(),
    )

    assert peptide.canonical_notation == "[Acetyl]-PES[Phospho]TIDE"
    assert peptide.modifications[0].provenance is not None
    assert peptide.modifications[0].provenance.rule_path == (
        "modification_registry",
        "variable",
        "Acetyl",
    )


def test_named_and_delta_modifications_record_assignment_provenance() -> None:
    registry = modification_registry()
    named = parse_modified_peptide("M[Oxidation]PEPTIDE", registry=registry)
    delta = parse_modified_peptide("M[+15.994915]PEPTIDE", registry=registry)

    assert named.modifications[0].provenance is not None
    assert named.modifications[0].provenance.assignment_token == "Oxidation"
    assert named.modifications[0].provenance.rule_path == (
        "modification_registry",
        "variable",
        "Oxidation",
    )
    assert delta.modifications[0].provenance is not None
    assert delta.modifications[0].provenance.assignment_token == "+15.994915"
    assert delta.modifications[0].provenance.rule_path == (
        "explicit_delta",
        "+15.994915",
    )


def test_build_modified_peptide_supports_explicit_protein_terminal_assignments() -> (
    None
):
    peptide = build_modified_peptide(
        "PEPTIDE",
        assignments=("Acetyl@protein-n-term", "Amidated@protein-c-term"),
        registry=modification_registry(),
        at_protein_n_term=True,
        at_protein_c_term=True,
    )

    assert peptide.modifications[0].site is ModificationPosition.PROTEIN_N_TERM
    assert peptide.modifications[1].site is ModificationPosition.PROTEIN_C_TERM
    assert (
        peptide.canonical_notation
        == "[Acetyl@protein-n-term]-PEPTIDE-[Amidated@protein-c-term]"
    )


def test_parse_modified_peptide_supports_explicit_protein_terminal_notation() -> None:
    peptide = parse_modified_peptide(
        "[Acetyl@protein-n-term]-PEPTIDE-[Amidated@protein-c-term]",
        registry=modification_registry(),
        at_protein_n_term=True,
        at_protein_c_term=True,
    )

    assert peptide.at_protein_n_term is True
    assert peptide.at_protein_c_term is True
    assert peptide.canonical_notation == (
        "[Acetyl@protein-n-term]-PEPTIDE-[Amidated@protein-c-term]"
    )


def test_protein_terminal_modifications_require_explicit_terminal_context() -> None:
    with pytest.raises(ValueError, match="protein N-terminus"):
        build_modified_peptide(
            "PEPTIDE",
            assignments=("Acetyl@protein-n-term",),
            registry=modification_registry(),
        )


def test_same_site_modification_stacking_is_refused() -> None:
    with pytest.raises(ValueError, match="same physical site"):
        build_modified_peptide(
            "PESTIDE",
            assignments=("Phospho@3", "+10.0@3"),
            registry=modification_registry(),
        )


def test_variable_modification_enumeration_is_bounded_and_reported() -> None:
    report = enumerate_variable_modifications(
        "MMMM",
        variable_modifications=(
            VariableModification(
                name="Oxidation",
                residues=("M",),
                mass_delta_monoisotopic=15.994915,
                mass_delta_average=15.9994,
                max_occurrences=4,
            ),
        ),
        max_variants=5,
    )

    assert report.candidate_site_count == 4
    assert report.generated_variant_count == 5
    assert report.truncated is True
    assert report.variants[0].canonical_notation == "MMMM"


def test_variable_modification_enumeration_respects_max_occurrences() -> None:
    report = enumerate_variable_modifications(
        "MMM",
        variable_modifications=(
            VariableModification(
                name="Oxidation",
                residues=("M",),
                mass_delta_monoisotopic=15.994915,
                mass_delta_average=15.9994,
                max_occurrences=1,
            ),
        ),
        max_variants=10,
    )

    assert report.truncated is False
    assert [entry.canonical_notation for entry in report.variants] == [
        "MMM",
        "M[Oxidation]MM",
        "MM[Oxidation]M",
        "MMM[Oxidation]",
    ]


def test_isotopic_label_modifications_require_explicit_policy() -> None:
    heavy_registry = build_modification_registry(
        variable_modifications=(
            VariableModification(
                name="HeavyLys8",
                residues=("K",),
                position=ModificationPosition.ANYWHERE,
                mass_delta_monoisotopic=8.014199,
                mass_delta_average=8.014199,
                isotopic_label_family="silac_lys",
            ),
        ),
    )

    with pytest.raises(ValueError, match="explicit labeling policy"):
        build_modified_peptide(
            "PEPKTIDE",
            assignments=("HeavyLys8@4",),
            registry=heavy_registry,
        )

    peptide = build_modified_peptide(
        "PEPKTIDE",
        assignments=("HeavyLys8@4",),
        registry=heavy_registry,
        labeling_policy=IsotopicLabelingPolicy(
            allow_isotopic_labels=True,
            allowed_label_families=("silac_lys",),
        ),
    )

    assert peptide.modifications[0].mass_delta_monoisotopic == 8.014199


def test_modified_peptide_export_record_stays_stable_across_jsonl_and_tsv(
    tmp_path: Path,
) -> None:
    peptides = (
        build_modified_peptide(
            "PEPTIDE",
            assignments=("Acetyl@n-term", "Amidated@c-term"),
            registry=modification_registry(),
        ),
        build_modified_peptide(
            "ASTY",
            assignments=("Phospho@2",),
            registry=modification_registry(),
        ),
    )
    jsonl_path = tmp_path / "modified_peptides.jsonl"
    tsv_path = tmp_path / "modified_peptides.tsv"

    export_modified_peptides_jsonl(
        peptides, jsonl_path, registry=modification_registry()
    )
    export_modified_peptides_tsv(peptides, tsv_path, registry=modification_registry())

    jsonl_rows = [json.loads(line) for line in jsonl_path.read_text().splitlines()]
    tsv_lines = tsv_path.read_text().splitlines()
    export_record = build_modified_peptide_export_record(
        peptides[0], registry=modification_registry()
    )

    assert jsonl_rows[0]["canonical_notation"] == export_record.canonical_notation
    assert jsonl_rows[0]["modification_sites"] == list(export_record.modification_sites)
    assert tsv_lines[1].split("\t")[0] == export_record.canonical_notation
    assert tsv_lines[1].split("\t")[3] == ";".join(export_record.modification_sites)


def test_isotope_envelope_approximation_is_normalized_and_advisory() -> None:
    envelope = approximate_peptide_isotope_envelope("PEPTIDE", charge=2, peak_count=4)

    assert envelope.status.value == "predicted"
    assert len(envelope.peaks) == 4
    assert isclose(
        sum(peak.intensity for peak in envelope.peaks), 1.0, rel_tol=0.0, abs_tol=1e-9
    )
    assert envelope.peaks[1].mz > envelope.peaks[0].mz


def test_localization_placeholder_is_advisory_and_reports_candidate_sites() -> None:
    peptide = build_modified_peptide(
        "ASTY",
        assignments=("Phospho@2",),
        registry=modification_registry(),
    )

    advisory = build_modification_localization_advisory(
        peptide,
        registry=modification_registry(),
    )

    assert advisory.status.value == "advisory"
    assert advisory.candidates[0].candidate_site_indices == (2, 3, 4)
    assert advisory.candidates[0].ambiguous is True
    assert (
        advisory.candidates[0].localization_state
        is ModificationLocalizationState.AMBIGUOUS
    )


def test_localization_advisory_reports_explicit_assignment_states() -> None:
    registry = modification_registry()
    phospho = get_modification("Phospho", registry=registry)
    acetyl = get_modification("Acetyl", registry=registry)
    advisory = build_modification_localization_advisory(
        ParsedModifiedPeptide(
            sequence="ASTY",
            modifications=(
                AppliedModification(
                    name=acetyl.name,
                    token=acetyl.name,
                    site=ModificationPosition.PEPTIDE_N_TERM,
                    site_index=None,
                    residue=None,
                    mass_delta_monoisotopic=acetyl.mass_delta_monoisotopic,
                    mass_delta_average=acetyl.mass_delta_average,
                    neutral_losses=acetyl.neutral_losses,
                    controlled_id=acetyl.controlled_id,
                    source="registry",
                ),
                AppliedModification(
                    name=phospho.name,
                    token=phospho.name,
                    site=ModificationPosition.ANYWHERE,
                    site_index=None,
                    residue=None,
                    mass_delta_monoisotopic=phospho.mass_delta_monoisotopic,
                    mass_delta_average=phospho.mass_delta_average,
                    neutral_losses=phospho.neutral_losses,
                    controlled_id=phospho.controlled_id,
                    source="registry",
                ),
                AppliedModification(
                    name=phospho.name,
                    token=phospho.name,
                    site=ModificationPosition.ANYWHERE,
                    site_index=1,
                    residue="A",
                    mass_delta_monoisotopic=phospho.mass_delta_monoisotopic,
                    mass_delta_average=phospho.mass_delta_average,
                    neutral_losses=phospho.neutral_losses,
                    controlled_id=phospho.controlled_id,
                    source="registry",
                ),
                AppliedModification(
                    name="delta:+10.0",
                    token="+10.0",
                    site=ModificationPosition.ANYWHERE,
                    site_index=None,
                    residue=None,
                    mass_delta_monoisotopic=10.0,
                    mass_delta_average=10.0,
                    neutral_losses=(),
                    controlled_id=None,
                    source="delta",
                ),
            ),
            canonical_notation="[Acetyl]-ASTY",
        ),
        registry=registry,
    )

    assert [candidate.localization_state for candidate in advisory.candidates] == [
        ModificationLocalizationState.LOCALIZED,
        ModificationLocalizationState.UNLOCALIZED,
        ModificationLocalizationState.CONFLICTING,
        ModificationLocalizationState.UNSUPPORTED,
    ]


def test_chemistry_regression_fixture_pack_stays_stable() -> None:
    cases = json.loads(_chemistry_fixture("regression_cases.json").read_text())
    registry = modification_registry()

    for case in cases:
        peptide = parse_modified_peptide(case["notation"], registry=registry)
        assert (
            canonicalize_modified_peptide(peptide, registry=registry)
            == case["canonical_notation"]
        )
        assert isclose(
            calculate_modified_peptide_mass(peptide, registry=registry),
            case["monoisotopic_mass"],
            rel_tol=0.0,
            abs_tol=1e-6,
        )
        assert isclose(
            calculate_modified_peptide_mass(
                peptide,
                mass_type=MassType.AVERAGE,
                registry=registry,
            ),
            case["average_mass"],
            rel_tol=0.0,
            abs_tol=1e-6,
        )
        assert isclose(
            calculate_peptide_mz(peptide, charge=case["charge"], registry=registry),
            case["mz"],
            rel_tol=0.0,
            abs_tol=1e-9,
        )


def test_modified_peptide_canonicalization_fixture_pack_is_deterministic() -> None:
    cases = json.loads(_chemistry_fixture("canonicalization_cases.json").read_text())
    registry = modification_registry()

    for case in cases:
        for notation in case["inputs"]:
            assert (
                canonicalize_modified_peptide(notation, registry=registry)
                == case["expected"]
            )

    forward = build_modified_peptide(
        "PESTIDE",
        assignments=("Acetyl@n-term", "Phospho@3"),
        registry=registry,
    )
    reversed_assignments = build_modified_peptide(
        "PESTIDE",
        assignments=("Phospho@3", "Acetyl@n-term"),
        registry=registry,
    )

    assert forward.canonical_notation == reversed_assignments.canonical_notation


def test_mz_calculator_rejects_invalid_charge() -> None:
    with pytest.raises(ValueError, match="charge must be at least 1"):
        calculate_peptide_mz("PEPTIDE", charge=0, mass_type=MassType.MONOISOTOPIC)
