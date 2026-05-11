from __future__ import annotations

from agentic_proteins.execution import RunConfig, ToolReliabilityTracker


def test_legacy_run_config_normalizes_runtime_defaults() -> None:
    config, warnings = RunConfig().with_defaults()

    assert config.predictors_enabled == ["heuristic_proxy"]
    assert config.retry_policy == {"max_retries": 0}
    assert "default_predictors_enabled" in warnings
    assert "default_retry_policy" in warnings


def test_legacy_tool_reliability_tracker_preserves_runtime_summary_behavior() -> None:
    tracker = ToolReliabilityTracker(tool_name="folding")
    tracker.record("success", 10.0)
    tracker.record("failure", 30.0)
    summary = tracker.summary()

    assert summary.tool_name == "folding"
    assert summary.sample_count == 2
    assert summary.success_rate == 0.5
    assert summary.latency_p95_ms >= summary.latency_p50_ms
