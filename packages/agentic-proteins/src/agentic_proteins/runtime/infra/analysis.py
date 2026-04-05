# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Analysis helpers for run observability."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from agentic_proteins.runtime.workspace import write_json_atomic


@dataclass
class ToolStats:
    """ToolStats."""

    success: int = 0
    failure: int = 0
    latencies_ms: list[float] = field(default_factory=list)


@dataclass
class RunAnalysis:
    """RunAnalysis."""

    candidate_timeline: dict[str, list[dict]] = field(default_factory=dict)
    tool_stats: dict[str, ToolStats] = field(default_factory=dict)
    iteration_deltas: list[dict] = field(default_factory=list)

    def record_candidate_event(
        self, candidate_id: str, event: str, payload: dict | None = None
    ) -> None:
        """record_candidate_event."""
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": event,
        }
        if payload:
            entry.update(payload)
        self.candidate_timeline.setdefault(candidate_id, []).append(entry)

    def record_tool_result(
        self, tool_name: str, status: str, latency_ms: float
    ) -> None:
        """record_tool_result."""
        stats = self.tool_stats.setdefault(tool_name, ToolStats())
        if status == "success":
            stats.success += 1
        else:
            stats.failure += 1
        stats.latencies_ms.append(float(latency_ms))

    def record_iteration_delta(
        self, iteration_index: int, improvement_delta: float, score: float | None
    ) -> None:
        """record_iteration_delta."""
        self.iteration_deltas.append(
            {
                "iteration_index": iteration_index,
                "improvement_delta": round(float(improvement_delta), 3),
                "score": None if score is None else round(float(score), 3),
            }
        )

    def write(self, path: Path) -> None:
        """write."""
        payload = {
            "candidate_timeline": self.candidate_timeline,
            "tool_stats": {
                name: {
                    "success": stats.success,
                    "failure": stats.failure,
                    "latencies_ms": stats.latencies_ms,
                }
                for name, stats in self.tool_stats.items()
            },
            "iteration_deltas": self.iteration_deltas,
        }
        write_json_atomic(path, payload)
