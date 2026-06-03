# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.domain import (
    load_structure_from_pdb_text,
    parse_structure_from_pdb_text,
)

_MINIMAL_PDB = """\
ATOM      1  N   ALA A   1      11.104  13.207  14.100  1.00 42.00           N
ATOM      2  CA  ALA A   1      12.560  13.207  14.100  1.00 55.00           C
ATOM      3  C   ALA A   1      13.000  14.600  14.700  1.00 38.00           C
TER
END
"""


def test_parse_structure_from_pdb_text_reads_raw_pdb_payload() -> None:
    structure = parse_structure_from_pdb_text(_MINIMAL_PDB)

    assert structure.id == "pred"
    residues = list(structure.get_residues())  # type: ignore[no-untyped-call]
    assert len(residues) == 1
    assert residues[0].get_resname() == "ALA"


def test_load_structure_from_pdb_text_stays_as_deprecating_wrapper() -> None:
    with pytest.warns(DeprecationWarning, match="parse_structure_from_pdb_text"):
        legacy = load_structure_from_pdb_text(_MINIMAL_PDB)

    canonical = parse_structure_from_pdb_text(_MINIMAL_PDB)
    assert legacy.id == canonical.id == "pred"
