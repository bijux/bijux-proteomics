# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_proteomics.chemistry.modification_packs import (
    ModificationPackTerminus,
    ModificationPackValidationError,
    load_modification_pack,
)


def _write_pack(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_load_modification_pack_preserves_aliases_targets_losses_and_ptm_class(
    tmp_path: Path,
) -> None:
    pack_path = _write_pack(
        tmp_path / "modification_pack_valid.json",
        {
            "pack_name": "benchmark-modifications",
            "pack_version": "2026.05",
            "modifications": [
                {
                    "modification_id": "Oxidation",
                    "aliases": ["UNIMOD:35", "ox"],
                    "delta_mass": 15.994915,
                    "allowed_residues": ["M"],
                    "allowed_termini": [],
                    "neutral_losses": [],
                    "ptm_class": "oxidation",
                },
                {
                    "modification_id": "Acetyl",
                    "aliases": ["UNIMOD:1"],
                    "delta_mass": 42.010565,
                    "allowed_residues": [],
                    "allowed_termini": ["peptide_n_term"],
                    "neutral_losses": [],
                    "ptm_class": "acetylation",
                },
                {
                    "modification_id": "Phospho",
                    "aliases": ["UNIMOD:21"],
                    "delta_mass": 79.966331,
                    "allowed_residues": ["S", "T", "Y"],
                    "allowed_termini": [],
                    "neutral_losses": [
                        {
                            "name": "phosphoric_acid",
                            "monoisotopic_mass": 97.976896,
                            "average_mass": 97.9952,
                        }
                    ],
                    "ptm_class": "phosphorylation",
                },
            ],
            "metadata": {"curator": "team-bijux"},
        },
    )

    pack = load_modification_pack(pack_path)

    assert pack.pack_name == "benchmark-modifications"
    assert pack.pack_version == "2026.05"
    assert pack.summary.modification_count == 3
    assert pack.summary.residue_targeted_count == 2
    assert pack.summary.terminus_targeted_count == 1
    assert pack.summary.ptm_class_counts == {
        "acetylation": 1,
        "oxidation": 1,
        "phosphorylation": 1,
    }
    assert pack.metadata == {"curator": "team-bijux"}
    assert pack.modifications[0].aliases == ("UNIMOD:35", "ox")
    assert pack.modifications[0].allowed_residues == ("M",)
    assert pack.modifications[1].allowed_termini == (
        ModificationPackTerminus.PEPTIDE_N_TERM,
    )
    assert pack.modifications[2].neutral_losses[0].name == "phosphoric_acid"
    assert pack.modifications[2].ptm_class == "phosphorylation"


def test_load_modification_pack_rejects_invalid_residue_and_terminus_rules(
    tmp_path: Path,
) -> None:
    pack_path = _write_pack(
        tmp_path / "modification_pack_invalid.json",
        {
            "pack_name": "broken-modifications",
            "modifications": [
                {
                    "modification_id": "BadDualTarget",
                    "aliases": [],
                    "delta_mass": 1.0,
                    "allowed_residues": ["K"],
                    "allowed_termini": ["peptide_n_term"],
                    "neutral_losses": [],
                    "ptm_class": "acetylation",
                },
                {
                    "modification_id": "BadResidue",
                    "aliases": [],
                    "delta_mass": 2.0,
                    "allowed_residues": ["B"],
                    "allowed_termini": [],
                    "neutral_losses": [],
                    "ptm_class": "artifact",
                },
                {
                    "modification_id": "MissingTarget",
                    "aliases": [],
                    "delta_mass": 3.0,
                    "allowed_residues": [],
                    "allowed_termini": [],
                    "neutral_losses": [],
                    "ptm_class": "artifact",
                },
            ],
        },
    )

    with pytest.raises(ModificationPackValidationError) as exc_info:
        load_modification_pack(pack_path)

    report = exc_info.value.report
    rejected = {row.row_number: row.reason for row in report.rejected_rows}

    assert report.source_path == str(pack_path)
    assert rejected[1] == "modification pack row must target residues or termini, not both"
    assert rejected[2] == "allowed_residues: invalid modification-pack residues: B"
    assert rejected[3] == (
        "modification pack row requires allowed_residues or allowed_termini"
    )
