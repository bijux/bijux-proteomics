# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Tool reliability tracking for runtime review outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
import statistics

from bijux_proteomics_intelligence.domain.metrics.quality import ToolReliability


@dataclass
class ToolReliabilityTracker:
    """Track success and latency distributions for one tool."""

    tool_name: str
    latencies_ms: list[float] = field(default_factory=list)
    successes: int = 0
    failures: int = 0

    def record(self, status: str, latency_ms: float) -> None:
        self.latencies_ms.append(float(latency_ms))
        if status == "success":
            self.successes += 1
        else:
            self.failures += 1

    def summary(self) -> ToolReliability:
        total = self.successes + self.failures
        success_rate = self.successes / total if total else 0.0
        p50 = _percentile(self.latencies_ms, 50.0)
        p95 = _percentile(self.latencies_ms, 95.0)
        variance = (
            statistics.pvariance(self.latencies_ms)
            if len(self.latencies_ms) > 1
            else 0.0
        )
        return ToolReliability(
            tool_name=self.tool_name,
            success_rate=success_rate,
            latency_p50_ms=p50,
            latency_p95_ms=p95,
            latency_variance=variance,
            sample_count=total,
        )


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * (pct / 100.0)
    floor = int(index)
    ceiling = min(floor + 1, len(ordered) - 1)
    if floor == ceiling:
        return ordered[floor]
    return ordered[floor] + (ordered[ceiling] - ordered[floor]) * (index - floor)


__all__ = ["ToolReliabilityTracker"]
