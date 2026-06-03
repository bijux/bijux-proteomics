# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.chemistry import (
    ModificationPosition,
    ModificationRegistryResolutionMode,
    ModificationRegistryResolutionSource,
    get_modification,
    load_modification_registry,
    modification_registry,
    resolve_modification,
)


def _modification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "modifications" / name


def test_builtin_modification_registry_covers_terminal_residue_and_isotope_definitions() -> (
    None
):
    registry = modification_registry()

    acetyl = get_modification("Acetyl", registry=registry)
    acetyl_lys = get_modification("AcetylLys", registry=registry)
    heavy_lys = get_modification("HeavyLys8", registry=registry)

    assert acetyl.position is ModificationPosition.PEPTIDE_N_TERM
    assert acetyl_lys.position is ModificationPosition.ANYWHERE
    assert acetyl_lys.residues == ("K",)
    assert heavy_lys.residues == ("K",)
    assert heavy_lys.isotopic_label_family == "silac_lys"


def test_modification_registry_resolves_name_accession_mass_delta_and_custom_entries() -> (
    None
):
    registry = load_modification_registry(
        _modification_fixture("resolution_registry.json")
    )

    named = resolve_modification(
        token="Oxidation",
        site=ModificationPosition.ANYWHERE,
        residue="M",
    )
    accession = resolve_modification(
        controlled_id="UNIMOD:35",
        site=ModificationPosition.ANYWHERE,
        residue="M",
    )
    mass_delta = resolve_modification(
        mass_delta_monoisotopic=15.994915,
        site=ModificationPosition.ANYWHERE,
        residue="M",
    )
    custom = resolve_modification(
        controlled_id="CUSTOM:HEAVY_LYS8",
        site=ModificationPosition.ANYWHERE,
        residue="K",
        registry=registry,
    )

    assert named.accepted is True
    assert named.match_mode is ModificationRegistryResolutionMode.NAME
    assert named.source is ModificationRegistryResolutionSource.BUILTIN
    assert named.modification_name == "Oxidation"

    assert accession.accepted is True
    assert accession.match_mode is ModificationRegistryResolutionMode.CONTROLLED_ID
    assert accession.controlled_id == "UNIMOD:35"

    assert mass_delta.accepted is True
    assert mass_delta.match_mode is ModificationRegistryResolutionMode.MASS_DELTA
    assert mass_delta.modification_name == "Oxidation"

    assert custom.accepted is True
    assert custom.source is ModificationRegistryResolutionSource.REGISTRY
    assert custom.modification_name == "HeavyLys8Custom"
    assert custom.isotopic_label_family == "silac_lys"
