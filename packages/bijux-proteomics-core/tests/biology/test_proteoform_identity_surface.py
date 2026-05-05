# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.proteoform_identity import (
    ProteoformEvidenceLevel,
    ProteoformPtmAssignment,
    build_proteoform_identity,
)


def test_build_proteoform_identity_preserves_ptm_combination_and_origin() -> None:
    identity = build_proteoform_identity(
        sequence=" acdmek ",
        protein_origin="P12345-2",
        evidence_level=ProteoformEvidenceLevel.PROBABLE,
        ptm_assignments=(
            ProteoformPtmAssignment(name="Acetyl", site="n_term"),
            ProteoformPtmAssignment(name="Oxidation", site="M4"),
        ),
        ambiguity_summary="M4 oxidation could map to an isobaric site in low-resolution spectra.",
    )

    assert identity.sequence == "ACDMEK"
    assert identity.protein_origin == "P12345-2"
    assert identity.evidence_level is ProteoformEvidenceLevel.PROBABLE
    assert identity.ptm_assignments[0].name == "Oxidation"
    assert identity.ptm_assignments[1].name == "Acetyl"
    assert identity.canonical_proteoform_key == (
        "ACDMEK::P12345-2::M4:Oxidation:localized|n_term:Acetyl:localized"
    )
