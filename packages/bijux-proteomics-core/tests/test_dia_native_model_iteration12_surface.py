# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.dia_iteration12 import (
    DiaNativeFragment,
    DiaNativeLibraryEntryReference,
    DiaNativePrecursor,
    DiaNativeProteinGroupQuantity,
    build_dia_native_data_model,
)


def test_build_dia_native_data_model_counts_and_sorts_entities() -> None:
    model = build_dia_native_data_model(
        precursors=(
            DiaNativePrecursor(
                precursor_id="p2",
                peptide_sequence="PEPTIDEK",
                charge=2,
                q_value=0.01,
                quantity=1200.0,
            ),
            DiaNativePrecursor(
                precursor_id="p1",
                peptide_sequence="ACDMPEP",
                charge=3,
                q_value=0.02,
                quantity=900.0,
            ),
        ),
        fragments=(
            DiaNativeFragment(precursor_id="p1", fragment_id="y7", mz=712.3, intensity=500.0),
        ),
        protein_groups=(
            DiaNativeProteinGroupQuantity(
                protein_group_id="pg-1",
                q_value=0.03,
                quantity=3300.0,
            ),
        ),
        library_refs=(
            DiaNativeLibraryEntryReference(library_entry_id="lib-10", decoy=False),
        ),
    )

    assert model.precursor_count == 2
    assert model.fragment_count == 1
    assert model.protein_group_count == 1
    assert model.precursors[0].precursor_id == "p1"
