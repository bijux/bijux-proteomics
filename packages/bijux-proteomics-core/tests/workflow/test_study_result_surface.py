# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import SearchAdapterKind
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import TmtSearchResultSourceKind
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
)
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.workflow import (
    ProteomicsRunEngine,
    build_biological_result_report_bundle,
    build_dda_biological_workflow_bundle,
    build_diann_biological_workflow_bundle,
    build_maxquant_biological_workflow_bundle,
    build_proteomics_run_bundle,
    build_ptm_site_workflow_bundle,
    build_tmt_experiment_workflow_bundle,
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
