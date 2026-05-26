# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    AdvancedFragpipeWorkflowConfig,
    run_advanced_fragpipe_workflow,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_run_advanced_fragpipe_workflow_exports_exact_discrepancy_reasons(
    tmp_path: Path,
) -> None:
    report = run_advanced_fragpipe_workflow(
        AdvancedFragpipeWorkflowConfig(
            psm_tsv_path=_workflow_fixture("fragpipe_biological_psms.tsv"),
            design_tsv_path=_workflow_fixture("biological_report.design.tsv"),
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            output_dir=tmp_path / "advanced_fragpipe_review",
            philosopher_protein_tsv_path=_workflow_fixture(
                "fragpipe_biological_proteins.tsv"
            ),
            go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
            pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
            complex_membership_tsv_path=_workflow_fixture("biological_report_complexes.tsv"),
            condition_a="control",
            condition_b="treatment",
        )
    )

    output_dir = tmp_path / "advanced_fragpipe_review"
    discrepancy_tsv = (
        output_dir / report.manifest.artifacts.discrepancy_reason_tsv
    ).read_text(encoding="utf-8")
    peptide_evidence_tsv = (
        output_dir / report.manifest.artifacts.peptide_evidence_tsv
    ).read_text(encoding="utf-8")
    rejected_evidence_tsv = (
        output_dir / report.manifest.artifacts.rejected_evidence_tsv
    ).read_text(encoding="utf-8")
    filtered_psm_tsv = (
        output_dir / report.fragpipe_workflow_manifest.artifacts.filtered_psm_tsv
    ).read_text(encoding="utf-8")

    assert report.summary.accepted_psm_count == 30
    assert report.summary.peptide_evidence_count >= 5
    assert report.summary.protein_group_discrepancy_count == 2
    assert "Q11111\tsource_only\tpresent_in_source_summary_only" in discrepancy_tsv
    assert (
        "P62993\tworkflow_only\tmissing_from_source_summary_but_inferred_and_quantified"
        in discrepancy_tsv
    )
    assert "PEPAAA" in peptide_evidence_tsv
    assert "q_value_above_threshold" in filtered_psm_tsv
    assert "decoy" in filtered_psm_tsv
    assert "contaminant" in filtered_psm_tsv
    assert "present_in_source_summary_only" in rejected_evidence_tsv
    assert "q_value_above_threshold" in rejected_evidence_tsv
    assert "rejected_psm_row" in rejected_evidence_tsv
    assert report.manifest.artifacts.supported_claim_tsv is not None
    assert report.manifest.artifacts.rejected_claim_tsv is not None
    assert (output_dir / report.manifest.artifacts.supported_claim_tsv).exists()
    assert (output_dir / report.manifest.artifacts.rejected_claim_tsv).exists()


def test_run_advanced_fragpipe_workflow_skips_discrepancy_export_without_source_summary(
    tmp_path: Path,
) -> None:
    report = run_advanced_fragpipe_workflow(
        AdvancedFragpipeWorkflowConfig(
            psm_tsv_path=_workflow_fixture("fragpipe_biological_psms.tsv"),
            design_tsv_path=_workflow_fixture("biological_report.design.tsv"),
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            output_dir=tmp_path / "advanced_fragpipe_without_source_summary",
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert report.summary.protein_group_discrepancy_count == 0
    assert report.manifest.artifacts.discrepancy_reason_tsv is None
    assert (tmp_path / "advanced_fragpipe_without_source_summary" / report.manifest.artifacts.rejected_evidence_tsv).exists()
    assert report.discrepancy_reasons == ()
