# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.benchmarks import (
    BenchmarkMetricEntry,
    build_benchmark_output_bundle,
)


def test_build_benchmark_output_bundle_sorts_metrics_and_paths() -> None:
    bundle = build_benchmark_output_bundle(
        bundle_id="bench-1",
        corpus_id="corpus-large",
        environment_fingerprint="a" * 16,
        metrics=(
            BenchmarkMetricEntry(name="memory", value=1024, unit="mb"),
            BenchmarkMetricEntry(name="throughput", value=42, unit="psm_per_s"),
        ),
        artifact_paths=("artifacts/z.json", "artifacts/a.json"),
        caveats=("synthetic_corpus",),
    )

    assert bundle.metrics[0].name == "memory"
    assert bundle.artifact_paths[0] == "artifacts/a.json"
