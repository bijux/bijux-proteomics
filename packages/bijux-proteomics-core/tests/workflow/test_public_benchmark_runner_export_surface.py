# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    render_public_benchmark_suite_failures_tsv,
    render_public_benchmark_suite_summary_tsv,
    run_public_benchmark_descriptor_suite,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_public_benchmark_runner_renders_summary_and_failure_ledgers(
    tmp_path: Path,
) -> None:
    suite = run_public_benchmark_descriptor_suite(
        _repo_root() / "benchmarks" / "public",
        output_root=tmp_path / "runs",
    )

    summary_tsv = render_public_benchmark_suite_summary_tsv(suite)
    failures_tsv = render_public_benchmark_suite_failures_tsv(suite)

    assert summary_tsv.splitlines()[0] == (
        "dataset_id\taccession\tsearch_engine\tstatus\tknown_limitation_count\t"
        "blocking_limitation_count\texpected_signal_count\tmatched_signal_count\t"
        "failure_count\toutput_dir\tnote"
    )
    assert "lfq_cohort_review_package" in summary_tsv
    assert "dia_diann_benchmark_dataset" in summary_tsv
    assert "maxquant_lfq_benchmark_dataset" in summary_tsv
    assert "ptm_localization_review_package" in summary_tsv
    assert "dia_diann_review_snapshot" in summary_tsv
    assert failures_tsv.splitlines()[0] == (
        "dataset_id\taccession\tstatus\tfailure_kind\tsubject\tmessage"
    )
    assert "missing_required_schema" in failures_tsv or "execution_failed" in failures_tsv
