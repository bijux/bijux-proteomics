# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics import chemistry


def test_chemistry_package_exports_isotope_envelope_owner_surface() -> None:
    envelopes = chemistry.predict_peptide_isotope_envelopes("PEPTIDE", charges=(2, 3))
    rendered = chemistry.render_isotope_envelopes_tsv(envelopes)

    assert hasattr(chemistry, "build_peptide_elemental_composition")
    assert hasattr(chemistry, "predict_peptide_isotope_envelope")
    assert hasattr(chemistry, "predict_peptide_isotope_envelopes")
    assert hasattr(chemistry, "render_isotope_envelopes_tsv")
    assert envelopes[0].composition.formula == "C34H53N7O15"
    assert "probability" in rendered
