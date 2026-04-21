"""Runtime-agnostic execution contracts owned by bijux-proteomics-core."""

from __future__ import annotations

from typing import Protocol


class CandidateLike(Protocol):
    """Runtime-agnostic candidate contract."""

    candidate_id: str
    sequence: str


class ToolResultLike(Protocol):
    """Runtime-agnostic tool result contract."""

    status: str


class ExecutionIteration(Protocol):
    """Runtime-agnostic single-iteration execution contract."""

    def run_iteration(self, candidate: CandidateLike) -> ToolResultLike:
        """Run one execution iteration for a candidate."""
        ...


__all__ = ["CandidateLike", "ExecutionIteration", "ToolResultLike"]
