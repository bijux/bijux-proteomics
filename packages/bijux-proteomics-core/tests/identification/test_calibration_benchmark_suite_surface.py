# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.calibration_benchmarks import (
    AdapterCalibrationBenchmarkInput,
    build_adapter_calibration_benchmark_suite,
)
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    normalize_search_results_with_adapter,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _adapter_input(
    adapter_kind: SearchAdapterKind,
    relative_path: str,
) -> AdapterCalibrationBenchmarkInput:
    normalization = normalize_search_results_with_adapter(
        source_path=_repo_root() / relative_path,
        adapter_kind=adapter_kind,
    )
    return AdapterCalibrationBenchmarkInput(
        adapter_kind=adapter_kind,
        records=normalization.normalized_records,
        score_orientation=normalization.adapter_manifest.score_orientation.value,
        entrapment_protein_refs=("ENTRAPMENT_P99999",),
    )


def test_calibration_benchmark_suite_tracks_multiple_adapter_families() -> None:
    report = build_adapter_calibration_benchmark_suite(
        (
            _adapter_input(
                SearchAdapterKind.MSFRAGGER,
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_results.tsv",
            ),
            _adapter_input(
                SearchAdapterKind.MAXQUANT_EVIDENCE,
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_evidence.tsv",
            ),
            _adapter_input(
                SearchAdapterKind.SPECTRONAUT,
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_report.tsv",
            ),
            _adapter_input(
                SearchAdapterKind.DIANN,
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_report.tsv",
            ),
        ),
        accepted_q_value_threshold=0.01,
        bin_count=5,
        top_fraction=0.2,
    )

    assert len(report.entries) == 4
    assert all(entry.total_record_count > 0 for entry in report.entries)
    assert all(entry.q_value_monotonic is True for entry in report.entries)
    assert all(
        entry.calibration.top_fraction_decoy_interval_width >= 0.0
        for entry in report.entries
    )
    assert "adapter-family calibration suite" in report.note
