# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.collaboration import (
    CollaboratorChallengeInput,
    run_collaborator_challenge_workflow,
)


def test_run_collaborator_challenge_workflow_generates_open_entries() -> None:
    report = run_collaborator_challenge_workflow(
        (
            CollaboratorChallengeInput(
                challenge_id="ch-1",
                reviewer_id="rev-x",
                evidence_claim_id="claim-22",
                question="What controls support this claim?",
                comment="Need stronger contradiction analysis.",
            ),
        )
    )

    assert report.entries[0].status == "open"
    assert "What controls support this claim?" in report.entries[0].prompt
