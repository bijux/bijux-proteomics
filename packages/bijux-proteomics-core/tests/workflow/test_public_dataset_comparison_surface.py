# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import yaml

from bijux_proteomics.workflow import (
    PublicDatasetComparisonDatasetStatus,
    build_public_dataset_comparison_report,
    public_benchmark_root,
    render_public_dataset_combined_summary_tsv,
    render_public_dataset_dataset_summary_tsv,
    render_public_dataset_failure_tsv,
    render_public_dataset_meta_analysis_tsv,
    render_public_dataset_pathway_comparison_tsv,
)


def _benchmark_descriptor(source_name: str) -> Path:
    return public_benchmark_root() / source_name / "dataset.yml"


def _write_descriptor_copy(
    *,
    source_name: str,
    benchmark_root: Path,
    dataset_id: str,
    accession: str,
) -> None:
    payload = yaml.safe_load(_benchmark_descriptor(source_name).read_text(encoding="utf-8"))
    payload["dataset_id"] = dataset_id
    payload["accession"] = accession
    target_dir = benchmark_root / dataset_id
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "dataset.yml").write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def test_build_public_dataset_comparison_report_preserves_per_dataset_and_combined_outputs(
    tmp_path: Path,
) -> None:
    benchmark_root = tmp_path / "benchmarks"
    _write_descriptor_copy(
        source_name="lfq_cohort_review_package",
        benchmark_root=benchmark_root,
        dataset_id="lfq_question_a",
        accession="flagship_public_package:lfq_question_a",
    )
    _write_descriptor_copy(
        source_name="lfq_cohort_review_package",
        benchmark_root=benchmark_root,
        dataset_id="lfq_question_b",
        accession="flagship_public_package:lfq_question_b",
    )
    _write_descriptor_copy(
        source_name="dda_maxquant_review_snapshot",
        benchmark_root=benchmark_root,
        dataset_id="maxquant_missing_bundle",
        accession="flagship_public_package:maxquant_missing_bundle",
    )

    report = build_public_dataset_comparison_report(
        benchmark_root,
        run_output_root=tmp_path / "runs",
    )

    assert report.summary.descriptor_count == 3
    assert report.summary.passed_dataset_count == 2
    assert report.summary.failed_dataset_count == 1
    assert report.summary.failure_entry_count == 3
    assert report.summary.effect_support_study_count == 2
    assert report.summary.pathway_support_study_count == 0
    assert report.summary.replicated_effect_group_count > 0
    assert report.summary.meta_analysis_entry_count > 0

    dataset_by_id = {entry.dataset_id: entry for entry in report.dataset_summaries}
    assert dataset_by_id["lfq_question_a"].status is PublicDatasetComparisonDatasetStatus.PASSED
    assert dataset_by_id["lfq_question_a"].effect_comparison_supported is True
    assert dataset_by_id["lfq_question_a"].pathway_comparison_supported is False
    assert dataset_by_id["maxquant_missing_bundle"].status is (
        PublicDatasetComparisonDatasetStatus.FAILED
    )
    assert dataset_by_id["maxquant_missing_bundle"].failure_count == 3

    failure_messages = {(entry.failure_kind, entry.subject) for entry in report.failure_entries}
    assert ("missing_required_schema", "evidence_txt") in failure_messages
    assert ("missing_required_schema", "peptides_txt") in failure_messages
    assert ("missing_required_schema", "protein_groups_txt") in failure_messages

    assert report.effect_comparison_report is not None
    assert report.meta_analysis_report is not None
    assert report.pathway_comparison_report is not None
    assert report.pathway_comparison_report.summary.unsupported_study_count == 2

    dataset_summary_tsv = render_public_dataset_dataset_summary_tsv(report)
    combined_summary_tsv = render_public_dataset_combined_summary_tsv(report)
    failure_tsv = render_public_dataset_failure_tsv(report)
    meta_analysis_tsv = render_public_dataset_meta_analysis_tsv(report)
    pathway_comparison_tsv = render_public_dataset_pathway_comparison_tsv(report)

    assert "lfq_question_a" in dataset_summary_tsv
    assert "maxquant_missing_bundle" in dataset_summary_tsv
    assert "meta_analysis_entry_count" in combined_summary_tsv
    assert "missing_required_schema" in failure_tsv
    assert "combined_log2_fold_change" in meta_analysis_tsv
    assert "comparison_status" in pathway_comparison_tsv


def test_build_public_dataset_comparison_report_keeps_passed_targeted_benchmarks_visible_without_study_normalization(
    tmp_path: Path,
) -> None:
    benchmark_root = tmp_path / "benchmarks"
    _write_descriptor_copy(
        source_name="lfq_cohort_review_package",
        benchmark_root=benchmark_root,
        dataset_id="lfq_reference",
        accession="flagship_public_package:lfq_reference",
    )
    _write_descriptor_copy(
        source_name="targeted_transition_review_package",
        benchmark_root=benchmark_root,
        dataset_id="targeted_validation",
        accession="flagship_public_package:targeted_validation",
    )

    report = build_public_dataset_comparison_report(
        benchmark_root,
        run_output_root=tmp_path / "runs",
    )

    assert report.summary.descriptor_count == 2
    assert report.summary.passed_dataset_count == 2
    assert report.summary.failed_dataset_count == 0
    assert report.summary.successful_study_count == 2
    assert report.summary.effect_support_study_count == 1
    assert report.summary.pathway_support_study_count == 0

    dataset_by_id = {entry.dataset_id: entry for entry in report.dataset_summaries}
    assert dataset_by_id["targeted_validation"].status is (
        PublicDatasetComparisonDatasetStatus.PASSED
    )
    assert dataset_by_id["targeted_validation"].effect_comparison_supported is False
    assert dataset_by_id["targeted_validation"].pathway_comparison_supported is False
    assert "public benchmark descriptor executed through the owned workflow orchestrator" in (
        dataset_by_id["targeted_validation"].note
    )
