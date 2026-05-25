"""Diff-owned runtime surfaces for completed scientific run comparisons."""

from __future__ import annotations

from bijux_proteomics_runtime.diff.completed_runs import (
    CompletedRunScientificDiffReport,
    CompletedRunScientificDiffSummary,
    RunConfidenceTierDiffEntry,
    diff_completed_runs,
)
from bijux_proteomics_runtime.support.primitives.stability import sealed

__all__ = [
    "CompletedRunScientificDiffReport",
    "CompletedRunScientificDiffSummary",
    "RunConfidenceTierDiffEntry",
    "diff_completed_runs",
]

sealed()
