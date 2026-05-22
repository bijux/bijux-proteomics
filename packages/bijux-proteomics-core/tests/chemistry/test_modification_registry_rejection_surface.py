# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import (
    ModificationPosition,
    resolve_modification,
)


def test_modification_registry_rejects_residue_incompatible_queries() -> None:
    report = resolve_modification(
        token="Phospho",
        site=ModificationPosition.ANYWHERE,
        residue="M",
    )

    assert report.matched is True
    assert report.accepted is False
    assert report.rejection is not None
    assert report.rejection.code == "residue_incompatible"
    assert "not valid on residue M" in report.rejection.message


def test_modification_registry_rejects_terminal_and_residue_acetyl_as_distinct_sites() -> (
    None
):
    terminal_report = resolve_modification(
        token="AcetylLys",
        site=ModificationPosition.PEPTIDE_N_TERM,
    )
    ambiguous_delta = resolve_modification(
        mass_delta_monoisotopic=42.010565,
    )

    assert terminal_report.matched is True
    assert terminal_report.accepted is False
    assert terminal_report.rejection is not None
    assert terminal_report.rejection.code == "invalid_modification_site"

    assert ambiguous_delta.matched is False
    assert ambiguous_delta.accepted is False
    assert ambiguous_delta.rejection is not None
    assert ambiguous_delta.rejection.code == "ambiguous_mass_delta"
    assert "Acetyl" in ambiguous_delta.rejection.message
    assert "AcetylLys" in ambiguous_delta.rejection.message
