# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.proteoform_identity import (
    ProteoformEvidenceLevel,
    ProteoformPtmAssignment,
    build_proteoform_identity,
)


def _biology_fixture(name: str) -> dict[str, object]:
    return json.loads(
        (
            Path(__file__).resolve().parent.parent / "fixtures" / "biology" / name
        ).read_text(encoding="utf-8")
    )


def test_build_proteoform_identity_preserves_ptm_combination_and_origin() -> None:
    fixture = _biology_fixture("ambiguity_proteoform_identity.json")
    ptm_assignments = tuple(
        ProteoformPtmAssignment(
            name=str(item["name"]),
            site=str(item["site"]),
        )
        for item in fixture["ptm_assignments"]
    )
    identity = build_proteoform_identity(
        sequence=str(fixture["sequence"]),
        protein_origin=str(fixture["protein_origin"]),
        evidence_level=ProteoformEvidenceLevel(str(fixture["evidence_level"])),
        ptm_assignments=ptm_assignments,
        ambiguity_summary=str(fixture["ambiguity_summary"]),
    )

    assert identity.sequence == "ACDMEK"
    assert identity.protein_origin == "P12345-2"
    assert identity.evidence_level is ProteoformEvidenceLevel.PROBABLE
    assert identity.ptm_assignments[0].name == "Oxidation"
    assert identity.ptm_assignments[1].name == "Acetyl"
    assert identity.canonical_proteoform_key == (
        "ACDMEK::P12345-2::M4:Oxidation:localized|n_term:Acetyl:localized"
    )
    assert "isobaric site" in identity.ambiguity_summary
