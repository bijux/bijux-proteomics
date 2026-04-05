# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import warnings

import numpy as np

from agentic_proteins.domain.structure import structure as structure_module


PDB_TEXT = """\
ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00 10.00           C
ATOM      2  CA  GLY A   2       1.500   0.000   0.000  1.00 20.00           C
ATOM      3  CA  SER A   3       3.000   0.000   0.000  1.00 30.00           C
TER
END
"""


def test_basic_structure_metrics() -> None:
    structure = structure_module.load_structure_from_pdb_text(PDB_TEXT)
    assert structure_module.residue_count(structure) == 3
    mean = structure_module.mean_plddt_from_ca_bfactor(structure)
    assert mean == 20.0
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="parse error at line 1: This file does not seem to be an mmCIF file",
            category=UserWarning,
        )
        plddts, sss, aas = structure_module.per_residue_plddt_ss(structure)
        assert plddts == [10.0, 20.0, 30.0]
        assert len(sss) == 3
        assert aas == ["A", "G", "S"]
        secondary = structure_module.secondary_summary_from_structure(structure)
        assert secondary.pct_coil == 100.0
        tertiary = structure_module.tertiary_summary_from_structure(structure, plddts)
        assert tertiary.mean_plddt == 20.0


def test_chain_selection_and_alignment() -> None:
    structure = structure_module.load_structure_from_pdb_text(PDB_TEXT)
    chain = structure_module.get_protein_chain(structure, "A")
    assert chain.id == "A"
    rmsd, n_pairs, _ref, _pred, seq_id, gap_frac = structure_module.kabsch_and_pairs(
        PDB_TEXT, PDB_TEXT
    )
    assert n_pairs >= 3
    assert rmsd == 0.0
    assert seq_id == 1.0
    assert gap_frac == 0.0


def test_distance_metrics() -> None:
    ref = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    pred = np.array([[0.0, 0.0, 0.0], [1.5, 0.0, 0.0]])
    assert structure_module.gdt_ts(ref, pred) > 50.0
    assert structure_module.gdt_ha(ref, pred) > 50.0
    assert structure_module.tm_score(ref, pred, l_ref=20) > 0.5
