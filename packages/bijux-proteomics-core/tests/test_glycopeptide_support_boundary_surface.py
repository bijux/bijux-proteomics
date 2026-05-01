# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.ptm_advanced_workflows import evaluate_glycopeptide_support_boundary


def test_glycopeptide_support_boundary_accepts_glyco_specific_evidence() -> None:
    report = evaluate_glycopeptide_support_boundary(
        requested_workflow="n_glycopeptide_localization",
        has_glycan_composition=True,
        has_glycosite_localization=True,
        has_oxonium_ion_support=True,
        treats_as_ordinary_modification=False,
    )

    assert report.disposition.value == "supported"
    assert report.missing_evidence_fields == ()
    assert "glycan_composition" in report.required_evidence_fields


def test_glycopeptide_support_boundary_refuses_ordinary_mod_handling() -> None:
    report = evaluate_glycopeptide_support_boundary(
        requested_workflow="o_glycopeptide_screen",
        has_glycan_composition=False,
        has_glycosite_localization=True,
        has_oxonium_ion_support=False,
        treats_as_ordinary_modification=True,
    )

    assert report.disposition.value == "refused"
    assert report.missing_evidence_fields == (
        "glycan_composition",
        "oxonium_ion_support",
    )
    assert report.notes
