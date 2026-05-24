# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    build_public_benchmark_trust_bundle,
    render_trust_bundle_run_summary_tsv,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_render_trust_bundle_run_summary_tsv_lists_generated_bundle_runs(
    tmp_path: Path,
) -> None:
    report = build_public_benchmark_trust_bundle(
        _repo_root() / "benchmarks" / "public",
        output_dir=tmp_path / "trust_bundle",
    )

    summary_tsv = render_trust_bundle_run_summary_tsv(report)

    assert summary_tsv.splitlines()[0] == (
        "dataset_id\taccession\tstatus\tworkflow_output_dir\tfailure_count\tartifact_count\trejected_artifact_count\tqc_artifact_count\tcard_artifact_count\tcomparison_artifact_count"
    )
    assert "lfq_cohort_review_package" in summary_tsv
    assert "dia_diann_benchmark_dataset" in summary_tsv
    assert "fragpipe_msfragger_benchmark_dataset" in summary_tsv
    assert "maxquant_lfq_benchmark_dataset" in summary_tsv
    assert "ptm_localization_review_package" in summary_tsv
    assert "dia_diann_review_snapshot" in summary_tsv
