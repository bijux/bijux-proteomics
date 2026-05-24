# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import workflow
from bijux_proteomics.interpretation import OrthologRecord, PathwayMemberKind
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import TmtSearchResultSourceKind
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


def test_workflow_package_exports_proteomics_study_result_surface() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("diann_biological.design.tsv")
        ).accepted_entries
    )
    diann_workflow = workflow.build_diann_biological_workflow_bundle(
        _fixture("diann_biological_report.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )
    tmt_workflow = workflow.build_tmt_experiment_workflow_bundle(
        Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / "maxquant_tmt_evidence.tsv",
        Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / "tmt.design.tsv",
        control_channel="126",
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )

    diann_study = workflow.build_proteomics_study_result(diann_workflow)
    tmt_study = workflow.build_proteomics_study_result(tmt_workflow)

    assert hasattr(workflow, "build_proteomics_study_result")
    assert workflow.ProteomicsStudyKind.DIA.value == "dia"
    assert diann_study.design.sample_count == 6
    assert tmt_study.design.sample_count == 8
    assert diann_study.summary.matrix_surface_count == 3
    assert tmt_study.summary.statistic_surface_count == 1


def test_workflow_package_exports_cross_study_protein_harmonization_surface() -> None:
    report = workflow.build_cross_study_protein_harmonization_report_from_observations(
        (
            workflow.CrossStudyProteinObservation(
                observation_id="study_a:card_1",
                study_id="study_a",
                study_label="study a",
                study_kind=workflow.ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=workflow.CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="card_1",
                representative_protein_ref="P11111",
                protein_refs=("P11111",),
                accession_aliases=(),
                gene_symbol="STAT1",
                note="study a card",
            ),
            workflow.CrossStudyProteinObservation(
                observation_id="study_b:card_2",
                study_id="study_b",
                study_label="study b",
                study_kind=workflow.ProteomicsStudyKind.DIA,
                species="Homo sapiens",
                source_kind=workflow.CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="card_2",
                representative_protein_ref="A0A0HUMAN1",
                protein_refs=("A0A0HUMAN1",),
                accession_aliases=("P11111",),
                gene_symbol="STAT1",
                note="study b alias-backed card",
            ),
        )
    )

    assert hasattr(workflow, "build_cross_study_protein_harmonization_report")
    assert workflow.CrossStudyProteinMatchBasis.EXACT_ACCESSION.value == "exact_accession"
    assert report.summary.harmonized_group_count == 1
    assert report.unresolved_entries == ()
    assert "harmonized_id" in workflow.render_cross_study_protein_harmonization_tsv(report)


def test_workflow_package_exports_cross_study_effect_comparison_surface() -> None:
    report = workflow.build_cross_study_effect_comparison_report_from_observations(
        (
            workflow.CrossStudyProteinEffectObservation(
                observation_id="study_a:protein_1",
                study_id="study_a",
                study_label="study a",
                study_kind=workflow.ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=workflow.CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="P11111",
                protein_refs=("P11111",),
                accession_aliases=(),
                gene_symbol="STAT1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=1.2,
                direction=workflow.CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                robustness_score=0.8,
                significant=True,
                note="study a effect",
            ),
            workflow.CrossStudyProteinEffectObservation(
                observation_id="study_b:protein_1",
                study_id="study_b",
                study_label="study b",
                study_kind=workflow.ProteomicsStudyKind.DIA,
                species="Homo sapiens",
                source_kind=workflow.CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="A0A0HUMAN1",
                protein_refs=("A0A0HUMAN1",),
                accession_aliases=("P11111",),
                gene_symbol="STAT1",
                condition_a="control",
                condition_b="treated",
                log2_fold_change=-1.1,
                direction=workflow.CrossStudyEffectDirection.DOWN,
                p_value=0.002,
                adjusted_p_value=0.02,
                robustness_score=0.7,
                significant=True,
                note="study b reversed-order effect",
            ),
        )
    )

    assert hasattr(workflow, "build_cross_study_effect_comparison_report")
    assert workflow.CrossStudyEffectComparisonStatus.REPLICATED_HIT.value == "replicated_hit"
    assert report.summary.replicated_hit_count == 1
    assert report.comparisons[0].replicated_hit is True
    assert "comparison_status" in workflow.render_cross_study_effect_comparison_tsv(report)
    assert "replicated_hit" in workflow.render_cross_study_replicated_hit_tsv(report)


def test_workflow_package_exports_cross_study_pathway_comparison_surface() -> None:
    report = workflow.build_cross_study_pathway_comparison_report_from_observations(
        (
            workflow.CrossStudyPathwayObservation(
                observation_id="study_a:enrichment:stress_response",
                study_id="study_a",
                study_label="study a",
                study_kind=workflow.ProteomicsStudyKind.LABEL_FREE,
                signal_kind=workflow.CrossStudyPathwaySignalKind.ENRICHMENT,
                pathway_id="reactome:stress_response",
                pathway_name="Stress response",
                source_name="reactome",
                source_accession="R-HSA-123",
                member_kind=PathwayMemberKind.PROTEIN,
                p_value=0.001,
                adjusted_p_value=0.01,
                enrichment_ratio=2.0,
                significant=True,
                total_member_count=20,
                foreground_overlap_count=9,
                background_member_count=10,
                coverage_fraction=0.9,
                note="study a enrichment",
            ),
            workflow.CrossStudyPathwayObservation(
                observation_id="study_b:enrichment:stress_response",
                study_id="study_b",
                study_label="study b",
                study_kind=workflow.ProteomicsStudyKind.DIA,
                signal_kind=workflow.CrossStudyPathwaySignalKind.ENRICHMENT,
                pathway_id="reactome:stress_response",
                pathway_name="Stress response",
                source_name="reactome",
                source_accession="R-HSA-123",
                member_kind=PathwayMemberKind.PROTEIN,
                p_value=0.003,
                adjusted_p_value=0.02,
                enrichment_ratio=1.7,
                significant=True,
                total_member_count=18,
                foreground_overlap_count=5,
                background_member_count=10,
                coverage_fraction=0.5,
                note="study b enrichment",
            ),
        )
    )

    assert hasattr(workflow, "build_cross_study_pathway_comparison_report")
    assert workflow.CrossStudyPathwayComparisonStatus.SHARED_SIGNAL.value == "shared_signal"
    assert report.summary.shared_signal_count == 1
    assert report.comparisons[0].coverage_fraction_range == 0.4
    assert "comparison_status" in workflow.render_cross_study_pathway_comparison_tsv(report)
    assert "shared_signal" in workflow.render_cross_study_shared_pathway_signal_tsv(report)


def test_workflow_package_exports_cross_species_effect_comparison_surface() -> None:
    report = workflow.build_cross_species_effect_comparison_report_from_observations(
        (
            workflow.CrossStudyProteinEffectObservation(
                observation_id="human:protein_1",
                study_id="human",
                study_label="human study",
                study_kind=workflow.ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=workflow.CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="P11111",
                protein_refs=("P11111",),
                accession_aliases=(),
                gene_symbol="STAT1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=1.2,
                direction=workflow.CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                robustness_score=0.8,
                significant=True,
                note="human effect",
            ),
            workflow.CrossStudyProteinEffectObservation(
                observation_id="mouse:protein_1",
                study_id="mouse",
                study_label="mouse study",
                study_kind=workflow.ProteomicsStudyKind.DDA,
                species="Mus musculus",
                source_kind=workflow.CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="Q9MOUSE1",
                protein_refs=("Q9MOUSE1",),
                accession_aliases=(),
                gene_symbol="Stat1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=0.9,
                direction=workflow.CrossStudyEffectDirection.UP,
                p_value=0.002,
                adjusted_p_value=0.02,
                robustness_score=0.7,
                significant=True,
                note="mouse effect",
            ),
        ),
        ortholog_records=(
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P11111",
                target_species="Mus musculus",
                target_protein_ref="Q9MOUSE1",
            ),
        ),
    )

    assert hasattr(workflow, "build_cross_species_effect_comparison_report")
    assert (
        workflow.CrossSpeciesEffectEvidenceStatus.CONSERVED_EFFECT.value
        == "conserved_effect"
    )
    assert report.summary.conserved_effect_count == 1
    assert report.comparisons[0].target_protein_ref == "Q9MOUSE1"
    assert "evidence_status" in workflow.render_cross_species_effect_comparison_tsv(report)


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
