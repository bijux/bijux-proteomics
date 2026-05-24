# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import workflow
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.study import build_experiment_design


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_workflow_package_exports_protein_evidence_card_surface() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = workflow.build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )

    assert hasattr(workflow, "build_protein_evidence_card_report")
    assert hasattr(workflow, "build_biological_result_graph_report")
    assert "card_id" in workflow.render_protein_evidence_card_tsv(report.protein_cards)
    assert "graph_claim_node_id" in workflow.render_protein_evidence_card_tsv(
        report.protein_cards
    )
    assert "proteogenomic_support_class" in workflow.render_protein_evidence_card_tsv(
        report.protein_cards
    )
    assert report.protein_cards.summary.protein_result_count == report.summary.protein_count
    assert report.experiment_confidence_report.summary.component_count == 7


def test_workflow_package_exports_protein_mechanism_card_surface(tmp_path: Path) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    fasta_path = tmp_path / "matching_regions.fasta"
    fasta_path.write_text(
        (
            ">sp|P04637|SIGA_HUMAN Signaling protein A\nMPEPAAAK\n"
            ">sp|Q9Y243|SIGB_HUMAN Signaling protein B\nMPEPDDDK\n"
            ">sp|O14920|SIGC_HUMAN Signaling protein C\nMPEPCCCK\n"
        ),
        encoding="utf-8",
    )
    report = workflow.build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=fasta_path,
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
        protein_region_context_tsv_path=_fixture("biological_report_regions.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    assert hasattr(workflow, "build_protein_mechanism_card_report")
    assert "evidence_tier" in workflow.render_protein_mechanism_card_tsv(
        report.protein_mechanism_cards
    )
    assert report.evidence_aware_ranking_report is not None
    assert "graph_claim_node_id" in workflow.render_protein_mechanism_card_tsv(
        report.protein_mechanism_cards
    )
    assert (
        report.protein_mechanism_cards.summary.card_count
        == report.summary.protein_count
    )
    assert report.protein_mechanism_cards.summary.domain_annotated_card_count >= 1
    assert report.evidence_aware_ranking_report.summary.pathway_entry_count >= 1


def test_workflow_package_exports_core_orchestrator_surface() -> None:
    assert hasattr(workflow, "run_proteomics_workflow")
    assert workflow.WorkflowMode.FRAGPIPE.value == "fragpipe"
    assert workflow.TargetedWorkflowStage.ASSAY_QC.value == "assay_qc"


def test_workflow_package_exports_public_benchmark_runner_surface() -> None:
    descriptor = workflow.load_public_benchmark_descriptor(
        Path(__file__).resolve().parents[4]
        / "benchmarks"
        / "public"
        / "ptm_localization_review_package"
        / "dataset.yml"
    )

    assert hasattr(workflow, "run_public_benchmark_descriptor_suite")
    assert descriptor.dataset_id == "ptm_localization_review_package"


def test_workflow_package_exports_trust_bundle_surface(tmp_path: Path) -> None:
    report = workflow.build_public_benchmark_trust_bundle(
        Path(__file__).resolve().parents[4] / "benchmarks" / "public",
        output_dir=tmp_path / "trust_bundle",
    )

    assert hasattr(workflow, "build_public_benchmark_trust_bundle")
    assert report.suite_report.passed_count == 2
    assert Path(report.html_index_path).exists()
