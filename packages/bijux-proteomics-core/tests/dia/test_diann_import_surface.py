# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.dia import DiaNnImportRow, import_dia_nn_rows


def test_import_dia_nn_rows_builds_precursor_and_protein_group_quantities() -> None:
    report = import_dia_nn_rows(
        (
            DiaNnImportRow(
                precursor_id="p1",
                peptide_sequence="PEPTIDEK",
                charge=2,
                q_value=0.01,
                quantity=100.0,
                protein_group_id="pg-1",
            ),
            DiaNnImportRow(
                precursor_id="p2",
                peptide_sequence="PEPTIDER",
                charge=2,
                q_value=0.02,
                quantity=120.0,
                protein_group_id="pg-1",
            ),
        )
    )

    assert report.imported_count == 2
    assert len(report.imported_precursors) == 2
    assert report.imported_protein_groups[0].quantity == 220.0
