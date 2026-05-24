# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    load_public_benchmark_descriptor,
    run_public_benchmark_descriptor_suite,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _benchmark_root() -> Path:
    return _repo_root() / "benchmarks" / "public"


def _descriptor(name: str) -> Path:
    return _benchmark_root() / name / "dataset.yml"


def test_load_public_benchmark_descriptor_preserves_required_contract_fields() -> None:
    descriptor = load_public_benchmark_descriptor(
        _descriptor("ptm_localization_review_package")
    )

    assert descriptor.dataset_id == "ptm_localization_review_package"
    assert descriptor.accession == "flagship_public_package:ptm_localization_review_package"
    assert descriptor.search_engine == "ptm"
    assert descriptor.expected_input_schemas == (
        "evidence_tsv",
        "feature_tsv",
        "proteins_fasta",
        "design_tsv",
    )
    assert descriptor.contrast.condition_a == "control"
    assert descriptor.contrast.condition_b == "treated"


def test_public_benchmark_descriptor_suite_records_explicit_success_and_failures(
    tmp_path: Path,
) -> None:
    suite = run_public_benchmark_descriptor_suite(
        _benchmark_root(),
        output_root=tmp_path / "runs",
    )
    runs = {run.dataset_id: run for run in suite.runs}

    assert suite.passed_count == 4
    assert suite.failed_count == 5

    diann_benchmark_run = runs["dia_diann_benchmark_dataset"]
    assert diann_benchmark_run.status == "passed"
    assert diann_benchmark_run.verified_counts["imported_precursor_count"] == 31
    assert diann_benchmark_run.verified_counts["significant_protein_count"] == 3
    assert Path(diann_benchmark_run.output_dir, "diann_biological_report_manifest.json").exists()

    maxquant_benchmark_run = runs["maxquant_lfq_benchmark_dataset"]
    assert maxquant_benchmark_run.status == "passed"
    assert maxquant_benchmark_run.verified_counts["imported_evidence_count"] == 8
    assert maxquant_benchmark_run.verified_counts["significant_protein_count"] == 3
    assert Path(
        maxquant_benchmark_run.output_dir, "maxquant_biological_report_manifest.json"
    ).exists()

    lfq_run = runs["lfq_cohort_review_package"]
    assert lfq_run.status == "passed"
    assert lfq_run.verified_counts["protein_card_count"] == 3
    assert Path(lfq_run.output_dir, "biological_report_manifest.json").exists()

    ptm_run = runs["ptm_localization_review_package"]
    assert ptm_run.status == "passed"
    assert ptm_run.verified_counts["accepted_evidence_count"] == 8
    assert Path(ptm_run.output_dir, "ptm_site_workflow_manifest.json").exists()

    diann_run = runs["dia_diann_review_snapshot"]
    assert diann_run.status == "failed"
    assert diann_run.failures[0].kind == "execution_failed"
    assert "peptide_sequence" in diann_run.failures[0].message

    fragpipe_run = runs["dda_fragpipe_review_snapshot"]
    assert fragpipe_run.status == "failed"
    assert fragpipe_run.failures[0].kind == "execution_failed"
    assert "spectrum_id" in fragpipe_run.failures[0].message

    maxquant_run = runs["dda_maxquant_review_snapshot"]
    assert maxquant_run.status == "failed"
    assert {failure.subject for failure in maxquant_run.failures} == {
        "evidence_txt",
        "peptides_txt",
        "protein_groups_txt",
    }

    tmt_run = runs["multiplex_tmtpro_review_package"]
    assert tmt_run.status == "failed"
    assert tmt_run.failures[0].kind == "execution_failed"
    assert "Modified sequence" in tmt_run.failures[0].message

    targeted_run = runs["targeted_transition_review_package"]
    assert targeted_run.status == "failed"
    assert targeted_run.failures[0].kind == "execution_failed"
    assert targeted_run.failures[0].message
