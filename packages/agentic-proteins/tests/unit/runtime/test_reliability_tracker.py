from __future__ import annotations

from agentic_proteins.runtime.infra.reliability import ToolReliabilityTracker


def test_reliability_tracker_summarizes() -> None:
    tracker = ToolReliabilityTracker(tool_name="tool")
    tracker.record("success", 10.0)
    tracker.record("failure", 20.0)
    summary = tracker.summary()
    assert summary.sample_count == 2
    assert summary.success_rate == 0.5
    assert summary.latency_p50_ms > 0.0
