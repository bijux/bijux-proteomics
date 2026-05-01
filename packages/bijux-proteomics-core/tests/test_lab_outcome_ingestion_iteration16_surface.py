# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab_planning_iteration16 import (
    LabOutcomeIngestionPolicy,
    LabOutcomeIngestionRecord,
    ingest_lab_outcomes_with_versioned_policy,
)


def test_ingest_lab_outcomes_with_versioned_policy_tracks_policy_version() -> None:
    report = ingest_lab_outcomes_with_versioned_policy(
        outcomes=(
            LabOutcomeIngestionRecord(
                outcome_id="out-1",
                candidate_id="cand-1",
                observed_status="validated",
                evidence_pointer_id="ev-44",
                observed_at_utc="2026-05-01T00:00:00Z",
            ),
        ),
        policy=LabOutcomeIngestionPolicy(
            policy_id="lab-outcome-ingest", policy_version="v1.0.0"
        ),
    )

    assert report.policy_version == "v1.0.0"
    assert report.updates[0].lifecycle_state == "validation_confirmed"
