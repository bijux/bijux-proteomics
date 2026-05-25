# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

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


def test_chemistry_package_exports_modification_pack_surface(tmp_path: Path) -> None:
    pack_path = tmp_path / "modification_pack.json"
    pack_path.write_text(
        json.dumps(
            {
                "pack_name": "public-modifications",
                "modifications": [
                    {
                        "modification_id": "Acetyl",
                        "aliases": ["UNIMOD:1"],
                        "delta_mass": 42.010565,
                        "allowed_residues": [],
                        "allowed_termini": ["peptide_n_term"],
                        "neutral_losses": [],
                        "ptm_class": "acetylation",
                    }
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    assert hasattr(chemistry, "load_modification_pack")
    assert hasattr(chemistry, "ModificationPackValidationError")

    pack = chemistry.load_modification_pack(pack_path)

    assert pack.pack_name == "public-modifications"
    assert pack.modifications[0].modification_id == "Acetyl"
    assert pack.summary.terminus_targeted_count == 1
