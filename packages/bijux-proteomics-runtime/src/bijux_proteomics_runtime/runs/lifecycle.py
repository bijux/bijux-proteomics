# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Run lifecycle states."""

from __future__ import annotations

from enum import StrEnum


class RunLifecycleState(StrEnum):
    """RunLifecycleState."""

    PLANNED = "planned"
    EXECUTING = "executing"
    EVALUATED = "evaluated"
    CANDIDATE_READY = "candidate_ready"
    HUMAN_REVIEW = "human_review"
    ARCHIVED = "archived"
