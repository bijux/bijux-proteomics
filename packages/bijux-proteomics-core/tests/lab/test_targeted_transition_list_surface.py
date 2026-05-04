# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab.planning import (
    TargetedTransitionEntry,
    TargetedTransitionFragment,
    TargetedTransitionListModel,
    validate_targeted_transition_list,
)


def test_validate_targeted_transition_list_accepts_valid_transition_entries() -> None:
    model = TargetedTransitionListModel(
        method="prm",
        entries=(
            TargetedTransitionEntry(
                transition_id="t1",
                peptide_sequence="PEPTIDEK",
                charge_state=2,
                precursor_mz=445.2,
                retention_window_start_min=12.5,
                retention_window_end_min=13.2,
                fragments=(
                    TargetedTransitionFragment(
                        ion_label="y7",
                        fragment_mz=789.4,
                        relative_intensity=0.8,
                    ),
                ),
                instrument_caveats=("optimize_collision_energy",),
            ),
        ),
    )

    report = validate_targeted_transition_list(model)

    assert report.valid is True
    assert report.issues == ()
