# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from typing import Callable

import yaml

from bijux_proteomics.workflow import (
    PublicBenchmarkExpectedSignalAssessmentStatus,
    PublicBenchmarkFailureKind,
    PublicBenchmarkKnownLimitationSeverity,
    PublicBenchmarkSearchEngine,
    load_public_benchmark_descriptor,
    render_public_benchmark_suite_signal_assessments_tsv,
    run_public_benchmark_descriptor,
    run_public_benchmark_descriptor_suite,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _write_descriptor_copy(
    tmp_path: Path,
    source_name: str,
    *,
    mutate: Callable[[dict], None] | None = None,
) -> Path:
    source_path = _repo_root() / "benchmarks" / "public" / source_name / "dataset.yml"
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    if mutate is not None:
        mutate(payload)
    target_dir = tmp_path / source_name
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / "dataset.yml"
    target_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return target_path


def test_public_benchmark_descriptor_loads_real_sample_metadata_signal_and_limitation_contracts() -> None:
    descriptor = load_public_benchmark_descriptor(
        _repo_root()
        / "benchmarks"
        / "public"
        / "ptm_localization_review_package"
        / "dataset.yml"
    )

    assert descriptor.search_engine is PublicBenchmarkSearchEngine.PTM
    assert len(descriptor.sample_metadata) == 4
    assert descriptor.expected_biological_signals[0].subject_id == "P11111:S5:Phospho"
    assert descriptor.known_limitations[0].severity is (
        PublicBenchmarkKnownLimitationSeverity.ADVISORY
    )


def test_public_benchmark_descriptor_loads_runnable_diann_contracts() -> None:
    descriptor = load_public_benchmark_descriptor(
        _repo_root()
        / "benchmarks"
        / "public"
        / "dia_diann_benchmark_dataset"
        / "dataset.yml"
    )

    assert descriptor.search_engine is PublicBenchmarkSearchEngine.DIANN
    assert descriptor.expected_input_schemas == (
        "result_tsv",
        "config_json",
        "design_tsv",
        "proteins_fasta",
    )
    assert len(descriptor.sample_metadata) == 6
    assert descriptor.expected_biological_signals[0].subject_id == "P04637"


def test_public_benchmark_runner_validates_expected_signal_assessments_for_real_ptm_descriptor(
    tmp_path: Path,
) -> None:
    report = run_public_benchmark_descriptor(
        _repo_root()
        / "benchmarks"
        / "public"
        / "ptm_localization_review_package"
        / "dataset.yml",
        output_root=tmp_path / "runs",
    )

    assert report.status == "passed"
    assert len(report.expected_signal_assessments) == 2
    assert {
        assessment.status for assessment in report.expected_signal_assessments
    } == {PublicBenchmarkExpectedSignalAssessmentStatus.MATCHED}


def test_public_benchmark_runner_executes_runnable_diann_descriptor(
    tmp_path: Path,
) -> None:
    report = run_public_benchmark_descriptor(
        _repo_root()
        / "benchmarks"
        / "public"
        / "dia_diann_benchmark_dataset"
        / "dataset.yml",
        output_root=tmp_path / "runs",
    )

    assert report.status == "passed"
    assert report.verified_counts["imported_precursor_count"] == 31
    assert report.verified_counts["protein_matrix_row_count"] == 5
    assert {
        assessment.status for assessment in report.expected_signal_assessments
    } == {PublicBenchmarkExpectedSignalAssessmentStatus.MATCHED}
    assert Path(report.output_dir, "diann_precursor_quantity_matrix.tsv").exists()
    assert Path(report.output_dir, "diann_import_rejected_evidence.tsv").exists()


def test_public_benchmark_runner_fails_when_descriptor_sample_metadata_conflicts_with_design(
    tmp_path: Path,
) -> None:
    descriptor_path = _write_descriptor_copy(
        tmp_path,
        "lfq_cohort_review_package",
        mutate=lambda payload: payload["sample_metadata"][0].update({"batch": "batch-z"}),
    )

    report = run_public_benchmark_descriptor(
        descriptor_path,
        output_root=tmp_path / "runs",
    )

    assert report.status == "failed"
    assert any(
        failure.kind == PublicBenchmarkFailureKind.SAMPLE_METADATA_MISMATCH
        for failure in report.failures
    )


def test_public_benchmark_runner_fails_when_declared_signal_direction_is_not_observed(
    tmp_path: Path,
) -> None:
    descriptor_path = _write_descriptor_copy(
        tmp_path,
        "ptm_localization_review_package",
        mutate=lambda payload: payload["expected_biological_signals"][0].update(
            {"expected_direction": "down"}
        ),
    )

    report = run_public_benchmark_descriptor(
        descriptor_path,
        output_root=tmp_path / "runs",
    )

    assert report.status == "failed"
    assert any(
        failure.kind == PublicBenchmarkFailureKind.EXPECTED_SIGNAL_MISMATCH
        for failure in report.failures
    )
    assert any(
        assessment.status is PublicBenchmarkExpectedSignalAssessmentStatus.MISMATCHED
        for assessment in report.expected_signal_assessments
    )


def test_public_benchmark_runner_renders_signal_assessment_ledger(
    tmp_path: Path,
) -> None:
    suite = run_public_benchmark_descriptor_suite(
        _repo_root() / "benchmarks" / "public",
        output_root=tmp_path / "runs",
    )

    signal_tsv = render_public_benchmark_suite_signal_assessments_tsv(suite)

    assert signal_tsv.splitlines()[0] == (
        "dataset_id\taccession\tstatus\tsignal_id\tsubject_kind\tsubject_id\t"
        "expected_direction\tassessment_status\tsource_surface\tobserved_direction\t"
        "observed_effect_size\tobserved_adjusted_p_value\tnote"
    )
    assert "ptm_site_p11111_s5_up" in signal_tsv
    assert "dia_sig_a_up" in signal_tsv
