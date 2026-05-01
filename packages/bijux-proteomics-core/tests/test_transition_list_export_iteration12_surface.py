# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.dia_iteration12 import (
    TransitionListExportEntry,
    export_transition_list_candidates,
)


def test_export_transition_list_candidates_renders_tsv_with_control_and_caveat_columns() -> (
    None
):
    bundle = export_transition_list_candidates(
        (
            TransitionListExportEntry(
                candidate_id="cand-a",
                peptide_sequence="PEPTIDEK",
                transition_label="y7",
                precursor_mz=445.2001,
                fragment_mz=712.3344,
                control=True,
                caveat="requires RT verification",
            ),
        )
    )

    assert bundle.row_count == 1
    assert "candidate_id\tpeptide_sequence\ttransition_label" in bundle.tsv_payload
    assert "requires RT verification" in bundle.tsv_payload
