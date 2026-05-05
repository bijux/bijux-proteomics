# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.reviews.analysis import (
    ReviewBoardAgendaEntry,
    ReviewBoardVote,
    ReviewBoardVoteEntry,
    run_review_board_workflow,
)


def test_run_review_board_workflow_tracks_disagreement_and_follow_up() -> None:
    report = run_review_board_workflow(
        board_id="rb-1",
        agenda=(
            ReviewBoardAgendaEntry(
                candidate_id="cand-1", agenda_reason="top ranked target"
            ),
        ),
        votes=(
            ReviewBoardVoteEntry(
                reviewer_id="rev-a",
                candidate_id="cand-1",
                vote=ReviewBoardVote.APPROVE,
                rationale="evidence supports progression",
            ),
            ReviewBoardVoteEntry(
                reviewer_id="rev-b",
                candidate_id="cand-1",
                vote=ReviewBoardVote.DEFER,
                rationale="requires orthogonal validation",
            ),
        ),
    )

    assert report.decisions[0].disagreement is True
    assert report.decisions[0].follow_up_actions
