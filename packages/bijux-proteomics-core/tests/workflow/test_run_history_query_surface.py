# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.workflow.reproducibility import (
    WorkflowRunHistoryArtifact,
    WorkflowRunHistoryEntry,
    WorkflowRunHistoryQuery,
    WorkflowRunHistoryStatus,
    query_workflow_run_history,
)


def test_query_workflow_run_history_filters_by_status_and_artifact_role() -> None:
    report = query_workflow_run_history(
        entries=(
            WorkflowRunHistoryEntry(
                run_id="run-1",
                study_id="study-a",
                sample_id="sample-01",
                status=WorkflowRunHistoryStatus.COMPLETED,
                started_at_utc="2026-05-01T10:00:00Z",
                artifacts=(
                    WorkflowRunHistoryArtifact(artifact_id="a1", role="review_packet"),
                ),
            ),
            WorkflowRunHistoryEntry(
                run_id="run-2",
                study_id="study-a",
                sample_id="sample-02",
                status=WorkflowRunHistoryStatus.FAILED,
                started_at_utc="2026-05-01T11:00:00Z",
                artifacts=(
                    WorkflowRunHistoryArtifact(artifact_id="a2", role="qc_report"),
                ),
            ),
        ),
        query=WorkflowRunHistoryQuery(
            study_id="study-a",
            status=WorkflowRunHistoryStatus.COMPLETED,
            requires_artifact_role="review_packet",
        ),
    )

    assert report.total_matches == 1
    assert report.runs[0].run_id == "run-1"
