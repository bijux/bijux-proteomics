# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.scale_iteration17 import (
    BenchmarkCorpusClass,
    classify_benchmark_corpus,
)


def test_classify_benchmark_corpus_selects_scale_for_large_non_truth_corpus() -> None:
    descriptor = classify_benchmark_corpus(
        corpus_id="corpus-large",
        spectrum_count=1_500_000,
        has_scientific_ground_truth=False,
        intended_publication_demo=False,
    )

    assert descriptor.class_label is BenchmarkCorpusClass.SCALE
