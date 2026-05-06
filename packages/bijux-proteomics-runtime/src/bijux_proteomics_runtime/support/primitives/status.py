# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Public-facing status enums for summaries and CLI output."""

from __future__ import annotations

from enum import StrEnum


class ExecutionStatus(StrEnum):
    """ExecutionStatus."""

    COMPLETED = "completed"
    ERRORED = "errored"
    ABORTED = "aborted"


class WorkflowState(StrEnum):
    """WorkflowState."""

    RUNNING = "running"
    PAUSED = "paused"
    AWAITING_HUMAN_REVIEW = "awaiting_human_review"
    DONE = "done"


class Outcome(StrEnum):
    """Outcome."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    INCONCLUSIVE = "inconclusive"


class ToolStatus(StrEnum):
    """ToolStatus."""

    SUCCESS = "success"
    DEGRADED = "degraded"
    FAILED = "failed"
    SKIPPED = "skipped"
