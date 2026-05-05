# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Run-analysis helpers for runtime execution review."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bijux_proteomics_runtime.runtime.workspace import write_json_atomic


@dataclass
class ToolStats:
    """Collected per-tool execution statistics."""

    success: int = 0
    failure: int = 0
    latencies_ms: list[float] = field(default_factory=list)


@dataclass
class RunAnalysis:
    """Collected analysis events for one runtime run."""

    candidate_timeline: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    tool_stats: dict[str, ToolStats] = field(default_factory=dict)
    iteration_deltas: list[dict[str, Any]] = field(default_factory=list)

    def record_candidate_event(
        self, candidate_id: str, event: str, payload: dict[str, Any] | None = None
    ) -> None:
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
        stats = self.tool_stats.setdefault(tool_name, ToolStats())
        if status == "success":
            stats.success += 1
        else:
            stats.failure += 1
        stats.latencies_ms.append(float(latency_ms))

    def record_iteration_delta(
        self, iteration_index: int, improvement_delta: float, score: float | None
    ) -> None:
        self.iteration_deltas.append(
            {
                "iteration_index": iteration_index,
                "improvement_delta": round(float(improvement_delta), 3),
                "score": None if score is None else round(float(score), 3),
            }
        )

    def write(self, path: Path) -> None:
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


__all__ = ["RunAnalysis", "ToolStats"]
