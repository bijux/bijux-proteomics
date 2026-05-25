# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain import ImportedEvidenceProvenance
from bijux_proteomics.dia import DiaNnImportRow, import_dia_nn_rows


def test_import_dia_nn_rows_builds_precursor_and_protein_group_quantities() -> None:
    report = import_dia_nn_rows(
        (
            DiaNnImportRow(
                precursor_id="p1",
                peptide_sequence="PEPTIDEK",
                modified_peptide="PEPTIDEK",
                charge=2,
                q_value=0.01,
                precursor_quantity=100.0,
                protein_group_id="pg-1",
                protein_refs=("P11111", "P11112"),
                run_name="raw_A",
                sample_name="sample_A",
                protein_group_quantity=340.0,
                provenance=ImportedEvidenceProvenance.from_single_row(
                    source_engine="diann",
                    source_file="diann.tsv",
                    source_row_number=2,
                    original_identifiers={"precursor_id": "p1"},
                ),
            ),
            DiaNnImportRow(
                precursor_id="p2",
                peptide_sequence="PEPTIDER",
                modified_peptide="PEPTIDER",
                charge=2,
                q_value=0.02,
                precursor_quantity=120.0,
                protein_group_id="pg-1",
                protein_refs=("P11111",),
                run_name="raw_A",
                sample_name="sample_A",
                protein_group_quantity=340.0,
                provenance=ImportedEvidenceProvenance.from_single_row(
                    source_engine="diann",
                    source_file="diann.tsv",
                    source_row_number=3,
                    original_identifiers={"precursor_id": "p2"},
                ),
            ),
        )
    )

    assert report.imported_count == 2
    assert len(report.imported_precursors) == 2
    assert report.imported_precursors[0].run_name == "raw_A"
    assert report.imported_precursors[0].protein_group_id == "pg-1"
    assert report.imported_precursors[0].provenance is not None
    assert report.imported_protein_groups[0].quantity == 340.0
    assert report.imported_protein_groups[0].source_precursor_count == 2
    assert report.imported_protein_groups[0].provenance is not None
    assert report.imported_protein_groups[0].provenance.source_row_numbers == (2, 3)
