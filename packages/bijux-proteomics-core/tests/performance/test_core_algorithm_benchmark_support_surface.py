# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from . import core_algorithm_benchmark_support as support


def test_runtime_retry_prefers_settled_measurement_after_budget_breach(
    monkeypatch,
) -> None:
    case = support.CoreAlgorithmBenchmarkCase(
        algorithm_id="digest",
        workload_unit="proteins",
        generated_unit_count=1600,
        baseline_seconds=0.46,
        regression_threshold_ratio=3.0,
    )
    samples = iter(((1.41, "first"), (0.70, "second")))

    def fake_measure_runtime(operation, *, rounds=2):
        return next(samples)

    monkeypatch.setattr(support, "_measure_runtime", fake_measure_runtime)
    monkeypatch.setattr(support.time, "sleep", lambda _: None)

    observed_seconds, value = support._measure_runtime_against_case(
        case,
        lambda: "workload",
    )

    assert observed_seconds == 0.70
    assert value == "second"
