# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import (
    ModificationResolutionSource,
    ModificationPosition,
    VariableModification,
    build_modification_registry,
    build_modification_resolution_report,
    get_modification,
    parse_modified_peptide,
)


def test_get_modification_resolves_unimod_ids_aliases_and_deamidation() -> None:
    oxidation = get_modification("UNIMOD:35")
    phospho = get_modification("phosphorylation")
    deamidated = get_modification("deamidation")

    assert oxidation.name == "Oxidation"
    assert phospho.name == "Phospho"
    assert deamidated.name == "Deamidated"
    assert deamidated.controlled_id == "UNIMOD:7"
    assert deamidated.residues == ("N", "Q")


def test_parse_modified_peptide_accepts_unimod_ids_and_aliases() -> None:
    unimod = parse_modified_peptide("N[UNIMOD:7]Q")
    alias = parse_modified_peptide("N[Deamidation]Q")

    assert unimod.canonical_notation == "N[Deamidated]Q"
    assert alias.canonical_notation == "N[Deamidated]Q"
    assert unimod.modifications[0].site_index == 1


def test_modification_resolution_report_validates_residue_and_reports_unknown() -> None:
    resolved = build_modification_resolution_report("UNIMOD:4", residue="C")
    invalid = build_modification_resolution_report("UNIMOD:4", residue="M")
    unknown = build_modification_resolution_report("NoSuchModification")

    assert resolved.resolved is True
    assert resolved.source is ModificationResolutionSource.BUILTIN
    assert resolved.residue_allowed is True
    assert resolved.modification_name == "Carbamidomethyl"

    assert invalid.resolved is True
    assert invalid.residue_allowed is False
    assert "not valid on residue" in invalid.issues[0]

    assert unknown.resolved is False
    assert unknown.source is ModificationResolutionSource.UNKNOWN
    assert "unknown modification" in unknown.issues[0]


def test_modification_resolution_report_supports_custom_registry_definitions() -> None:
    registry = build_modification_registry(
        variable_modifications=(
            VariableModification(
                name="LysTag",
                residues=("K",),
                position=ModificationPosition.ANYWHERE,
                mass_delta_monoisotopic=144.102063,
                mass_delta_average=144.212,
                controlled_id="CUSTOM:LYSTAG",
            ),
        ),
    )

    report = build_modification_resolution_report(
        "CUSTOM:LYSTAG",
        residue="K",
        registry=registry,
    )

    assert report.resolved is True
    assert report.source is ModificationResolutionSource.REGISTRY
    assert report.modification_name == "LysTag"
    assert report.controlled_id == "CUSTOM:LYSTAG"
    assert report.residue_allowed is True
