# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import run_public_benchmark_descriptor_suite
from bijux_proteomics.workflow.public_benchmark_descriptors import (
    load_public_benchmark_descriptor,
    public_benchmark_root,
)


def _benchmark_root() -> Path:
    return public_benchmark_root()


def _descriptor(name: str) -> Path:
    return _benchmark_root() / name / "dataset.yml"


def test_load_public_benchmark_descriptor_preserves_required_contract_fields() -> None:
    descriptor = load_public_benchmark_descriptor(
        _descriptor("ptm_localization_review_package")
    )

    assert descriptor.dataset_id == "ptm_localization_review_package"
    assert (
        descriptor.accession
        == "flagship_public_package:ptm_localization_review_package"
    )
    assert descriptor.search_engine == "ptm"
    assert descriptor.expected_input_schemas == (
        "evidence_tsv",
        "feature_tsv",
        "proteins_fasta",
        "design_tsv",
        "annotation_tsv",
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

    assert suite.passed_count == 8
    assert suite.failed_count == 3

    diann_benchmark_run = runs["dia_diann_benchmark_dataset"]
    assert diann_benchmark_run.status == "passed"
    assert diann_benchmark_run.verified_counts["imported_precursor_count"] == 31
    assert diann_benchmark_run.verified_counts["significant_protein_count"] == 3
    assert Path(
        diann_benchmark_run.output_dir, "diann_biological_report_manifest.json"
    ).exists()

    maxquant_benchmark_run = runs["maxquant_lfq_benchmark_dataset"]
    assert maxquant_benchmark_run.status == "passed"
    assert maxquant_benchmark_run.verified_counts["imported_evidence_count"] == 8
    assert maxquant_benchmark_run.verified_counts["significant_protein_count"] == 3
    assert Path(
        maxquant_benchmark_run.output_dir, "maxquant_biological_report_manifest.json"
    ).exists()

    fragpipe_benchmark_run = runs["fragpipe_msfragger_benchmark_dataset"]
    assert fragpipe_benchmark_run.status == "passed"
    assert fragpipe_benchmark_run.verified_counts["accepted_psm_count"] == 30
    assert (
        fragpipe_benchmark_run.verified_counts["protein_group_discrepancy_count"] == 2
    )
    assert Path(
        fragpipe_benchmark_run.output_dir, "fragpipe_biological_report_manifest.json"
    ).exists()

    lfq_run = runs["lfq_cohort_review_package"]
    assert lfq_run.status == "passed"
    assert lfq_run.verified_counts["protein_card_count"] == 3
    assert Path(lfq_run.output_dir, "biological_report_manifest.json").exists()

    sparse_lfq_run = runs["lfq_sparse_contrast_benchmark_dataset"]
    assert sparse_lfq_run.status == "passed"
    assert sparse_lfq_run.verified_counts["significant_protein_count"] == 0
    assert sparse_lfq_run.verified_counts["cohort_blocked_stratum_count"] == 2
    assert Path(sparse_lfq_run.output_dir, "biological_rejected_claims.tsv").exists()
    assert Path(
        sparse_lfq_run.output_dir, "biological_report_section_confidence.tsv"
    ).exists()

    ptm_run = runs["ptm_localization_review_package"]
    assert ptm_run.status == "passed"
    assert ptm_run.verified_counts["accepted_evidence_count"] == 8
    assert ptm_run.verified_counts["ambiguous_group_row_count"] == 2
    assert ptm_run.verified_counts["evidence_card_count"] == 3
    assert ptm_run.verified_counts["motif_term_count"] == 22
    assert Path(ptm_run.output_dir, "ptm_site_workflow_manifest.json").exists()
    assert Path(ptm_run.output_dir, "ptm_site_group_matrix.tsv").exists()
    assert Path(ptm_run.output_dir, "ptm_regulator_enrichment.tsv").exists()

    diann_run = runs["dia_diann_review_snapshot"]
    assert diann_run.status == "failed"
    assert diann_run.failures[0].kind == "execution_failed"
    assert "peptide_sequence" in diann_run.failures[0].message

    fragpipe_snapshot_run = runs["dda_fragpipe_review_snapshot"]
    assert fragpipe_snapshot_run.status == "failed"
    assert fragpipe_snapshot_run.failures[0].kind == "execution_failed"
    assert (
        "missing required PSM column 'Charge'"
        in fragpipe_snapshot_run.failures[0].message
    )

    maxquant_run = runs["dda_maxquant_review_snapshot"]
    assert maxquant_run.status == "failed"
    assert {failure.subject for failure in maxquant_run.failures} == {
        "evidence_txt",
        "peptides_txt",
        "protein_groups_txt",
    }

    tmt_run = runs["multiplex_tmtpro_review_package"]
    assert tmt_run.status == "passed"
    assert tmt_run.verified_counts["accepted_input_row_count"] == 4
    assert tmt_run.verified_counts["flagged_interference_count"] == 6
    assert Path(tmt_run.output_dir, "tmt_workflow_manifest.json").exists()
    assert Path(tmt_run.output_dir, "tmt_interference_summary.tsv").exists()

    targeted_run = runs["targeted_transition_review_package"]
    assert targeted_run.status == "passed"
    assert targeted_run.verified_counts["target_count"] == 2
    assert targeted_run.verified_counts["unreliable_target_count"] == 2
    assert Path(
        targeted_run.output_dir, "targeted_assay_qc_workflow_manifest.json"
    ).exists()
    assert Path(
        targeted_run.output_dir, "targeted_assay_qc_fragment_ratios.tsv"
    ).exists()
