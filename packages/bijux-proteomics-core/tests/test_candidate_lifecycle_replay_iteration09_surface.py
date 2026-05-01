# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review_iteration09 import (
    CandidateLifecycleEvent,
    replay_candidate_lifecycle,
)


def test_replay_candidate_lifecycle_explains_state_movement() -> None:
    report = replay_candidate_lifecycle(
        (
            CandidateLifecycleEvent(
                candidate_id="cand-1",
                from_state="deferred",
                to_state="accepted",
                reason="strong quant replication",
                evidence_pointers=("E11",),
                sequence_index=1,
            ),
            CandidateLifecycleEvent(
                candidate_id="cand-1",
                from_state="accepted",
                to_state="lab_requested",
                reason="board-approved validation plan",
                evidence_pointers=("E12",),
                sequence_index=2,
            ),
        )
    )

    assert report.candidate_count == 1
    entry = report.entries[0]
    assert entry.state_path == ("deferred", "accepted", "lab_requested")
    assert entry.transition_count == 2
    assert entry.current_state == "lab_requested"
