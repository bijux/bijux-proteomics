# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import SearchAdapterKind
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import TmtSearchResultSourceKind
from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
)
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.targeted import (
    TargetedPanelCandidateKind,
    TargetedValidationDiscoveryClaimInput,
    TargetedValidationPanelAssayInput,
)
from bijux_proteomics.workflow import (
    AdvancedDiannWorkflowConfig,
    AdvancedFragpipeWorkflowConfig,
    AdvancedMaxquantWorkflowConfig,
    AdvancedPtmWorkflowConfig,
    AdvancedTmtWorkflowConfig,
    ProteomicsRunEngine,
    TargetedValidationWorkflowConfig,
    build_biological_result_report_bundle,
    build_dda_biological_workflow_bundle,
    build_diann_biological_workflow_bundle,
    build_maxquant_biological_workflow_bundle,
    build_proteomics_run_bundle,
    build_ptm_site_workflow_bundle,
    build_tmt_experiment_workflow_bundle,
    run_advanced_diann_workflow,
    run_advanced_fragpipe_workflow,
    run_advanced_maxquant_workflow,
    run_advanced_ptm_workflow,
    run_advanced_tmt_workflow,
    run_targeted_validation_workflow,
)
from bijux_proteomics.workflow.study_result import (
    ProteomicsStudyCardKind,
    ProteomicsStudyConclusionKind,
    ProteomicsStudyKind,
    ProteomicsStudyMatrixKind,
    ProteomicsStudyQcKind,
    ProteomicsStudyStatisticKind,
    build_proteomics_study_result,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _multiplex_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def _write_targeted_validation_design(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file",
                "control_r1\tcontrol\t1\t1\tcontrol_r1.raw\tcontrol_r1.tsv",
                "control_r2\tcontrol\t2\t1\tcontrol_r2.raw\tcontrol_r2.tsv",
                "treat_r1\ttreatment\t1\t1\ttreat_r1.raw\ttreat_r1.tsv",
                "treat_r2\ttreatment\t2\t1\ttreat_r2.raw\ttreat_r2.tsv",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _write_targeted_validation_results(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality",
                "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r1\t25000\t12.50\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r1\t20000\t12.56\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r2\t27000\t12.48\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r2\t21000\t12.55\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r1\t120000\t12.51\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r1\t98000\t12.57\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r2\t118000\t12.52\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r2\t95000\t12.58\tpass",
                "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r1\t90000\t18.40\tpass",
                "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r1\t87000\t18.47\tpass",
                "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r2\t92000\t18.41\tpass",
                "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r2\t86000\t18.48\tpass",
                "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r1\t93000\t18.42\tpass",
                "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r1\t85000\t18.46\tpass",
                "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r2\t91500\t18.40\tpass",
                "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r2\t85500\t18.45\tpass",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def test_build_proteomics_study_result_preserves_label_free_biological_bundle() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_biological_result_report_bundle(
        _workflow_fixture("biological_report_features.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_workflow_fixture("biological_report_complexes.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    study_result = build_proteomics_study_result(report)

    assert study_result.study_kind is ProteomicsStudyKind.LABEL_FREE
    assert study_result.source_surface == "BiologicalResultReportBundle"
    assert study_result.design.sample_count == 6
    assert study_result.matrix_surfaces[0].kind is ProteomicsStudyMatrixKind.HEATMAP_REVIEW
    assert {
        surface.kind for surface in study_result.qc_surfaces
    } == {
        ProteomicsStudyQcKind.SAMPLE_EXPLORATION,
        ProteomicsStudyQcKind.EXPERIMENT_CONFIDENCE,
    }
    assert {
        surface.kind for surface in study_result.card_surfaces
    } == {
        ProteomicsStudyCardKind.PROTEIN_EVIDENCE,
        ProteomicsStudyCardKind.PROTEIN_MECHANISM,
    }
    assert any(
        entry.kind is ProteomicsStudyConclusionKind.SUPPORTED_CLAIM
        for entry in study_result.biological_conclusions
    )


def test_build_proteomics_study_result_preserves_diann_workflow_surfaces() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("diann_biological.design.tsv")
        ).accepted_entries
    )
    workflow = build_diann_biological_workflow_bundle(
        _workflow_fixture("diann_biological_report.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_workflow_fixture("biological_report_complexes.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    study_result = build_proteomics_study_result(workflow)

    assert study_result.study_kind is ProteomicsStudyKind.DIA
    assert {surface.kind for surface in study_result.matrix_surfaces} == {
        ProteomicsStudyMatrixKind.DIA_PRECURSOR,
        ProteomicsStudyMatrixKind.DIA_PEPTIDE,
        ProteomicsStudyMatrixKind.DIA_PROTEIN,
    }
    assert any(
        surface.kind is ProteomicsStudyStatisticKind.DIFFERENTIAL_PROTEIN
        for surface in study_result.statistic_surfaces
    )


def test_build_proteomics_study_result_preserves_fragpipe_workflow_surfaces() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    workflow = build_dda_biological_workflow_bundle(
        _workflow_fixture("fragpipe_biological_psms.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        adapter_kind=SearchAdapterKind.MSFRAGGER,
        dialect_id="fragpipe-psm",
        source_protein_tsv_path=_workflow_fixture("fragpipe_biological_proteins.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    study_result = build_proteomics_study_result(workflow)

    assert study_result.study_kind is ProteomicsStudyKind.DDA
    assert {
        surface.kind for surface in study_result.matrix_surfaces
    } == {
        ProteomicsStudyMatrixKind.LABEL_FREE_PROTEIN,
        ProteomicsStudyMatrixKind.HEATMAP_REVIEW,
    }
    assert {
        surface.kind for surface in study_result.qc_surfaces
    } == {
        ProteomicsStudyQcKind.DDA_ACCEPTANCE,
        ProteomicsStudyQcKind.DDA_PARSIMONY,
        ProteomicsStudyQcKind.SAMPLE_EXPLORATION,
        ProteomicsStudyQcKind.EXPERIMENT_CONFIDENCE,
    }
    assert any(
        surface.kind is ProteomicsStudyStatisticKind.DIFFERENTIAL_PROTEIN
        for surface in study_result.statistic_surfaces
    )
    assert study_result.biological_report is workflow.biological_report


def test_build_proteomics_study_result_preserves_maxquant_workflow_surfaces() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("maxquant_biological/design.tsv")
        ).accepted_entries
    )
    workflow = build_maxquant_biological_workflow_bundle(
        _workflow_fixture("maxquant_biological/evidence.txt"),
        build_experiment_design(design_entries),
        peptides_txt_path=_workflow_fixture("maxquant_biological/peptides.txt"),
        protein_groups_txt_path=_workflow_fixture(
            "maxquant_biological/proteinGroups.txt"
        ),
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        config_path=_workflow_fixture("maxquant_biological/maxquant_settings.txt"),
        condition_a="control",
        condition_b="treatment",
    )

    study_result = build_proteomics_study_result(workflow)

    assert study_result.study_kind is ProteomicsStudyKind.MAXQUANT
    assert {
        surface.kind for surface in study_result.matrix_surfaces
    } == {
        ProteomicsStudyMatrixKind.LABEL_FREE_PROTEIN,
        ProteomicsStudyMatrixKind.HEATMAP_REVIEW,
    }
    assert any(
        surface.kind is ProteomicsStudyQcKind.MAXQUANT_IMPORT
        for surface in study_result.qc_surfaces
    )
    assert any(
        surface.kind is ProteomicsStudyStatisticKind.DIFFERENTIAL_PROTEIN
        for surface in study_result.statistic_surfaces
    )
    assert {
        surface.kind for surface in study_result.qc_surfaces
    } == {
        ProteomicsStudyQcKind.MAXQUANT_IMPORT,
        ProteomicsStudyQcKind.MAXQUANT_ACCEPTANCE,
        ProteomicsStudyQcKind.SAMPLE_EXPLORATION,
        ProteomicsStudyQcKind.EXPERIMENT_CONFIDENCE,
    }
    assert study_result.biological_report is workflow.biological_report
    assert study_result.summary.matrix_surface_count == 2


def test_build_proteomics_study_result_preserves_tmt_and_ptm_studies_for_comparison() -> (
    None
):
    tmt_workflow = build_tmt_experiment_workflow_bundle(
        _multiplex_fixture("maxquant_tmt_evidence.tsv"),
        _multiplex_fixture("tmt.design.tsv"),
        control_channel="126",
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    ptm_workflow = build_ptm_site_workflow_bundle(
        _ptm_fixture("localization_results.tsv"),
        _fasta_fixture("ptm_sites.fasta"),
        feature_tsv_path=_ptm_fixture("ptm_features.tsv"),
        design_path=_ptm_fixture("ptm.design.tsv"),
        annotation_tsv_path=_ptm_fixture("ptm_site_annotations.tsv"),
        annotation_target_species="Homo sapiens",
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
        batch_field="",
        condition_a="control",
        condition_b="treated",
        regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        evidence_card_policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )

    tmt_study = build_proteomics_study_result(tmt_workflow)
    ptm_study = build_proteomics_study_result(ptm_workflow)

    assert tmt_study.study_kind is ProteomicsStudyKind.TMT
    assert ptm_study.study_kind is ProteomicsStudyKind.PTM
    assert tmt_study.design.sample_count == 8
    assert ptm_study.design.sample_count == 4
    assert {
        surface.kind for surface in tmt_study.matrix_surfaces
    } == {
        ProteomicsStudyMatrixKind.REPORTER_CHANNEL,
        ProteomicsStudyMatrixKind.PROTEIN_RATIO,
    }
    assert ptm_study.matrix_surfaces[0].kind is ProteomicsStudyMatrixKind.PTM_SITE
    assert (
        tmt_study.statistic_surfaces[0].kind
        is ProteomicsStudyStatisticKind.DIFFERENTIAL_LABEL_BASED
    )
    assert (
        ptm_study.statistic_surfaces[0].kind
        is ProteomicsStudyStatisticKind.DIFFERENTIAL_PTM_SITE
    )
    assert any(
        entry.kind is ProteomicsStudyConclusionKind.PTM_NARRATIVE_CLAIM
        for entry in ptm_study.biological_conclusions
    )


def test_build_proteomics_study_result_dispatches_flagship_run_bundles() -> None:
    metadata_entries = build_experiment_design(
        tuple(
            parse_experimental_design_table(
                _workflow_fixture("diann_biological.design.tsv")
            ).accepted_entries
        )
    )
    bundle = build_proteomics_run_bundle(
        engine=ProteomicsRunEngine.DIANN,
        metadata_entries=metadata_entries,
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        report_tsv_path=_workflow_fixture("diann_biological_report.tsv"),
        contrast="control-treatment",
        go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_workflow_fixture("biological_report_complexes.tsv"),
    )

    study_result = build_proteomics_study_result(bundle)

    assert study_result.study_kind is ProteomicsStudyKind.DIA
    assert study_result.design.sample_count == 6
    assert study_result.summary.conclusion_count >= 1


def test_build_proteomics_study_result_normalizes_advanced_diann_and_maxquant_reports(
    tmp_path: Path,
) -> None:
    advanced_diann = run_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "advanced_diann_study_result",
            condition_a="control",
            condition_b="treatment",
        )
    )
    advanced_maxquant = run_advanced_maxquant_workflow(
        AdvancedMaxquantWorkflowConfig(
            evidence_txt_path=_workflow_fixture("maxquant_biological/evidence.txt"),
            peptides_txt_path=_workflow_fixture("maxquant_biological/peptides.txt"),
            protein_groups_txt_path=_workflow_fixture(
                "maxquant_biological/proteinGroups.txt"
            ),
            design_tsv_path=_workflow_fixture("maxquant_biological/design.tsv"),
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            output_dir=tmp_path / "advanced_maxquant_study_result",
            config_path=_workflow_fixture("maxquant_biological/maxquant_settings.txt"),
            condition_a="control",
            condition_b="treatment",
        )
    )

    diann_study = build_proteomics_study_result(advanced_diann)
    maxquant_study = build_proteomics_study_result(advanced_maxquant)

    assert diann_study.study_kind is ProteomicsStudyKind.DIA
    assert diann_study.source_surface == "AdvancedDiannWorkflowReport"
    assert any(
        surface.kind is ProteomicsStudyQcKind.BELIEF_AUDIT
        for surface in diann_study.qc_surfaces
    )
    assert diann_study.biological_report is advanced_diann.diann_workflow.biological_report
    assert maxquant_study.study_kind is ProteomicsStudyKind.MAXQUANT
    assert maxquant_study.source_surface == "AdvancedMaxquantWorkflowReport"
    assert any(
        surface.kind is ProteomicsStudyQcKind.PROTEIN_GROUP_DISCREPANCY
        for surface in maxquant_study.qc_surfaces
    )
    assert (
        maxquant_study.biological_report
        is advanced_maxquant.maxquant_workflow.biological_report
    )


def test_build_proteomics_study_result_normalizes_advanced_fragpipe_and_ptm_reports(
    tmp_path: Path,
) -> None:
    advanced_fragpipe = run_advanced_fragpipe_workflow(
        AdvancedFragpipeWorkflowConfig(
            psm_tsv_path=_workflow_fixture("fragpipe_biological_psms.tsv"),
            design_tsv_path=_workflow_fixture("biological_report.design.tsv"),
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            output_dir=tmp_path / "advanced_fragpipe_study_result",
            philosopher_protein_tsv_path=_workflow_fixture(
                "fragpipe_biological_proteins.tsv"
            ),
            condition_a="control",
            condition_b="treatment",
        )
    )
    advanced_ptm = run_advanced_ptm_workflow(
        AdvancedPtmWorkflowConfig(
            evidence_tsv_path=_ptm_fixture("localization_results.tsv"),
            proteins_fasta_path=_fasta_fixture("ptm_sites.fasta"),
            feature_tsv_path=_ptm_fixture("ptm_features.tsv"),
            design_tsv_path=_ptm_fixture("ptm.design.tsv"),
            output_dir=tmp_path / "advanced_ptm_study_result",
            batch_field="",
            condition_a="control",
            condition_b="treated",
        )
    )

    fragpipe_study = build_proteomics_study_result(advanced_fragpipe)
    ptm_study = build_proteomics_study_result(advanced_ptm)

    assert fragpipe_study.study_kind is ProteomicsStudyKind.DDA
    assert fragpipe_study.source_surface == "AdvancedFragpipeWorkflowReport"
    assert any(
        surface.kind is ProteomicsStudyQcKind.PROTEIN_GROUP_DISCREPANCY
        for surface in fragpipe_study.qc_surfaces
    )
    assert fragpipe_study.biological_report is advanced_fragpipe.fragpipe_workflow.biological_report
    assert ptm_study.study_kind is ProteomicsStudyKind.PTM
    assert ptm_study.source_surface == "AdvancedPtmWorkflowReport"
    assert any(
        surface.kind is ProteomicsStudyQcKind.PTM_AMBIGUITY_REVIEW
        for surface in ptm_study.qc_surfaces
    )
    assert ptm_study.ptm_report is advanced_ptm.ptm_workflow.report


def test_build_proteomics_study_result_normalizes_advanced_tmt_and_targeted_reports(
    tmp_path: Path,
) -> None:
    advanced_tmt = run_advanced_tmt_workflow(
        AdvancedTmtWorkflowConfig(
            result_tsv_path=_multiplex_fixture("maxquant_tmt_interference.tsv"),
            design_tsv_path=_multiplex_fixture("tmt.design.tsv"),
            output_dir=tmp_path / "advanced_tmt_study_result",
            control_channel="126",
            condition_a="control",
            condition_b="treatment",
        )
    )
    targeted_results_path = tmp_path / "targeted_validation.skyline.tsv"
    targeted_design_path = tmp_path / "targeted_validation.design.tsv"
    _write_targeted_validation_results(targeted_results_path)
    _write_targeted_validation_design(targeted_design_path)
    targeted_report = run_targeted_validation_workflow(
        TargetedValidationWorkflowConfig(
            result_tsv_path=targeted_results_path,
            design_tsv_path=targeted_design_path,
            output_dir=tmp_path / "advanced_targeted_study_result",
            discovery_claims=(
                TargetedValidationDiscoveryClaimInput(
                    candidate_id="protein:P11111",
                    candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    display_label="P11111 robust candidate",
                    target_protein_ref="P11111",
                    priority_rank=1,
                    final_score=0.92,
                    penalty_total=0.0,
                    discovery_effect_size=1.3,
                    support_count=4,
                    robustness_score=0.88,
                    assay_feasibility_score=0.91,
                    rank_reason_codes=("assay_ready",),
                    ranking_note="strong discovery support",
                ),
                TargetedValidationDiscoveryClaimInput(
                    candidate_id="protein:P22222",
                    candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    display_label="P22222 flat conflict candidate",
                    target_protein_ref="P22222",
                    priority_rank=2,
                    final_score=0.71,
                    penalty_total=0.0,
                    discovery_effect_size=0.9,
                    support_count=3,
                    robustness_score=0.73,
                    assay_feasibility_score=0.84,
                    rank_reason_codes=("assay_ready",),
                    ranking_note="discovery claimed treatment increase",
                ),
                TargetedValidationDiscoveryClaimInput(
                    candidate_id="ptm_site:P33333:S21",
                    candidate_kind=TargetedPanelCandidateKind.PTM_SITE,
                    display_label="P33333 S21 site candidate",
                    target_protein_ref="P33333",
                    site_key="P33333:S21:phosphorylation",
                    priority_rank=3,
                    final_score=0.67,
                    penalty_total=0.0,
                    discovery_effect_size=0.8,
                    support_count=2,
                    robustness_score=0.66,
                    assay_feasibility_score=0.40,
                    rank_reason_codes=("low_assay_feasibility",),
                    ranking_note="site candidate was not converted into a site-specific assay",
                ),
            ),
            panel_assays=(
                TargetedValidationPanelAssayInput(
                    assay_entry_id="assay:P11111:PEPTIDER",
                    biomarker_candidate_id="protein:P11111",
                    biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    biomarker_display_label="P11111 robust candidate",
                    biomarker_priority_rank=1,
                    target_protein_ref="P11111",
                    target_protein_group_id="protein_group_1",
                    gene_symbol="GENE1",
                    peptide_sequence="PEPTIDER",
                    canonical_peptide="PEPTIDER",
                    uniqueness_class=PeptideUniquenessClass.UNIQUE,
                    precursor_charge=2,
                    selected_transition_count=3,
                    exported_transition_count=3,
                    warning_note="assay retained for panel export",
                ),
                TargetedValidationPanelAssayInput(
                    assay_entry_id="assay:P22222:AAAAK",
                    biomarker_candidate_id="protein:P22222",
                    biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    biomarker_display_label="P22222 flat conflict candidate",
                    biomarker_priority_rank=2,
                    target_protein_ref="P22222",
                    target_protein_group_id="protein_group_2",
                    gene_symbol="GENE2",
                    peptide_sequence="AAAAK",
                    canonical_peptide="AAAAK",
                    uniqueness_class=PeptideUniquenessClass.UNIQUE,
                    precursor_charge=2,
                    selected_transition_count=3,
                    exported_transition_count=3,
                    warning_note="assay retained for panel export",
                ),
            ),
            case_condition="treatment",
            control_condition="control",
        )
    )

    tmt_study = build_proteomics_study_result(advanced_tmt)
    targeted_study = build_proteomics_study_result(targeted_report)

    assert tmt_study.study_kind is ProteomicsStudyKind.TMT
    assert tmt_study.source_surface == "AdvancedTmtWorkflowReport"
    assert any(
        surface.kind is ProteomicsStudyQcKind.LABEL_BASED_SIGNAL_REVIEW
        for surface in tmt_study.qc_surfaces
    )
    assert any(
        surface.kind is ProteomicsStudyCardKind.PROTEIN_EVIDENCE
        for surface in tmt_study.card_surfaces
    )
    assert targeted_study.study_kind is ProteomicsStudyKind.TARGETED
    assert targeted_study.source_surface == "TargetedValidationWorkflowReport"
    assert targeted_study.design.sample_count == 4
    assert targeted_study.matrix_surfaces[0].kind is ProteomicsStudyMatrixKind.TARGETED_TARGET
    assert any(
        surface.kind is ProteomicsStudyQcKind.TARGETED_ASSAY_QC
        for surface in targeted_study.qc_surfaces
    )
    assert any(
        surface.kind is ProteomicsStudyCardKind.TARGETED_VALIDATION
        for surface in targeted_study.card_surfaces
    )
    assert {
        entry.kind for entry in targeted_study.biological_conclusions
    } == {
        ProteomicsStudyConclusionKind.SUPPORTED_CLAIM,
        ProteomicsStudyConclusionKind.REJECTED_CLAIM,
        ProteomicsStudyConclusionKind.REFUSED_CLAIM,
    }
