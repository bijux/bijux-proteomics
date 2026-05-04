# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.lab.planning import (
    AssayProgressionModel,
    AssayProgressionState,
    transition_assay_progression,
)


def test_transition_assay_progression_tracks_discovery_to_verification() -> None:
    model = AssayProgressionModel(
        assay_id="assay-1",
        current_state=AssayProgressionState.DISCOVERY,
    )

    moved = transition_assay_progression(
        model,
        to_state=AssayProgressionState.VERIFICATION,
        rationale="discovery evidence is reproducible",
    )

    assert moved.current_state is AssayProgressionState.VERIFICATION
    assert len(moved.transitions) == 1
    assert moved.transitions[0].from_state is AssayProgressionState.DISCOVERY


def test_transition_assay_progression_rejects_invalid_completed_to_discovery() -> None:
    model = AssayProgressionModel(
        assay_id="assay-2",
        current_state=AssayProgressionState.COMPLETED,
    )

    with pytest.raises(ValueError, match="cannot move assay"):
        transition_assay_progression(
            model,
            to_state=AssayProgressionState.DISCOVERY,
            rationale="restart",
        )
