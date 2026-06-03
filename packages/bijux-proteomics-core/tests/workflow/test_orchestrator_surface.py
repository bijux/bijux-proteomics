# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import SearchAdapterKind
from bijux_proteomics.multiplex import TmtSearchResultSourceKind
from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.targeted import (
    TargetedPanelCandidateKind,
    TargetedResultSourceKind,
    TargetedValidationDiscoveryClaimInput,
    TargetedValidationPanelAssayInput,
)
from bijux_proteomics.workflow import (
    DdaWorkflowConfig,
    DiannWorkflowConfig,
    LabelFreeWorkflowConfig,
    MaxquantWorkflowConfig,
    PtmWorkflowConfig,
    SilacWorkflowConfig,
    TargetedWorkflowConfig,
    TargetedWorkflowStage,
    TmtWorkflowConfig,
    WorkflowMode,
    run_proteomics_workflow,
)


def _fixture_root() -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures"


def _workflow_fixture(name: str) -> Path:
    return _fixture_root() / "workflow" / name


def _multiplex_fixture(name: str) -> Path:
    return _fixture_root() / "multiplex" / name


def _silac_fixture(name: str) -> Path:
    return _fixture_root() / "isotope_labeling" / name


def _ptm_fixture(name: str) -> Path:
    return _fixture_root() / "ptm" / name


def _targeted_fixture(name: str) -> Path:
    return _fixture_root() / "formats" / name


def _targeted_discovery_claims() -> tuple[TargetedValidationDiscoveryClaimInput, ...]:
    return (
        TargetedValidationDiscoveryClaimInput(
            candidate_id="protein:P001",
            candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            display_label="P001 benchmark candidate",
            target_protein_ref="P001",
            priority_rank=1,
            final_score=0.91,
            penalty_total=0.0,
            discovery_effect_size=0.8,
            support_count=3,
            robustness_score=0.8,
            assay_feasibility_score=0.9,
            rank_reason_codes=("assay_ready",),
            ranking_note="benchmark candidate",
        ),
        TargetedValidationDiscoveryClaimInput(
            candidate_id="protein:P002",
            candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            display_label="P002 benchmark candidate",
            target_protein_ref="P002",
            priority_rank=2,
            final_score=0.85,
            penalty_total=0.0,
            discovery_effect_size=-0.7,
            support_count=3,
            robustness_score=0.75,
            assay_feasibility_score=0.88,
            rank_reason_codes=("assay_ready",),
            ranking_note="benchmark candidate",
        ),
    )


def _targeted_panel_assays() -> tuple[TargetedValidationPanelAssayInput, ...]:
    return (
        TargetedValidationPanelAssayInput(
            assay_entry_id="assay:P001:PEPTIDEK",
            biomarker_candidate_id="protein:P001",
            biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            biomarker_display_label="P001 benchmark candidate",
            biomarker_priority_rank=1,
            target_protein_ref="P001",
            target_protein_group_id="protein_group_1",
            gene_symbol="GENE1",
            peptide_sequence="PEPTIDEK",
            canonical_peptide="PEPTIDEK",
            uniqueness_class=PeptideUniquenessClass.UNIQUE,
            precursor_charge=2,
            selected_transition_count=2,
            exported_transition_count=2,
            warning_note="benchmark assay",
        ),
        TargetedValidationPanelAssayInput(
            assay_entry_id="assay:P002:ACDMPEP",
            biomarker_candidate_id="protein:P002",
            biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            biomarker_display_label="P002 benchmark candidate",
            biomarker_priority_rank=2,
            target_protein_ref="P002",
            target_protein_group_id="protein_group_2",
            gene_symbol="GENE2",
            peptide_sequence="ACDMPEP",
            canonical_peptide="ACDMPEP",
            uniqueness_class=PeptideUniquenessClass.UNIQUE,
            precursor_charge=3,
            selected_transition_count=2,
            exported_transition_count=2,
            warning_note="benchmark assay",
        ),
    )


def test_run_proteomics_workflow_supports_label_free_mode(tmp_path: Path) -> None:
    protocol_path = tmp_path / "protocol.tsv"
    protocol_path.write_text(
        "\n".join(
            (
                "protocol_id\tdigestion_enzyme\tacquisition_type\tlabeling_method\tenrichment_type\tfractionation_mode\tdepletion_mode\tinstrument_platform",
                "prot-001\ttrypsin\tdia\tlabel_free\tnone\tnone\tnone\tOrbitrap Astral",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    result = run_proteomics_workflow(
        LabelFreeWorkflowConfig(
            input_tsv_path=_workflow_fixture("biological_report_features.tsv"),
            design_tsv_path=_workflow_fixture("biological_report.design.tsv"),
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            protocol_context_tsv_path=protocol_path,
            condition_a="control",
            condition_b="treatment",
            output_dir=tmp_path / "label_free",
        )
    )

    assert result.mode is WorkflowMode.LABEL_FREE
    assert result.design_row_count == 6
    assert result.manifest is result.export_manifest
    assert result.export_manifest is not None
    assert result.artifacts["output_dir"] == str(tmp_path / "label_free")
    assert result.artifacts["manifest_json"].endswith("biological_report_manifest.json")
    assert result.warnings == ()
    assert result.rejected_evidence == ()
    assert result.report.summary.protein_count == 5
    assert result.report.selection_policy.heatmap_max_entity_count == 75


def test_run_proteomics_workflow_supports_generic_psm_mode() -> None:
    result = run_proteomics_workflow(
        DdaWorkflowConfig(
            mode=WorkflowMode.GENERIC_PSM,
            search_result_tsv_path=_workflow_fixture("dda_biological_results.tsv"),
            design_tsv_path=_workflow_fixture("biological_report.design.tsv"),
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            adapter_kind=SearchAdapterKind.GENERIC,
            generic_mapping_path=_workflow_fixture("dda_biological_mapping.json"),
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert result.mode is WorkflowMode.GENERIC_PSM
    assert result.report.summary.accepted_psm_count == 30
    assert result.design_row_count == 6


def test_run_proteomics_workflow_supports_fragpipe_mode() -> None:
    result = run_proteomics_workflow(
        DdaWorkflowConfig(
            mode=WorkflowMode.FRAGPIPE,
            search_result_tsv_path=_workflow_fixture("fragpipe_biological_psms.tsv"),
            design_tsv_path=_workflow_fixture("biological_report.design.tsv"),
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            source_protein_tsv_path=_workflow_fixture(
                "fragpipe_biological_proteins.tsv"
            ),
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert result.mode is WorkflowMode.FRAGPIPE
    assert result.report.summary.accepted_psm_count == 30
    assert result.report.summary.protein_group_discrepancy_count == 2
    assert result.report.biological_report.summary.protein_count == 5


def test_run_proteomics_workflow_supports_diann_mode() -> None:
    result = run_proteomics_workflow(
        DiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_biological_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            annotation_tsv_path=(
                _fixture_root() / "interpretation" / "protein_annotation_custom.tsv"
            ),
            context_annotation_tsv_path=_workflow_fixture(
                "biological_report_context.tsv"
            ),
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert result.mode is WorkflowMode.DIANN
    assert result.design_row_count == 6
    assert result.report.summary.significant_protein_count >= 1
    assert result.report.summary.protein_card_count == 5
    assert result.report.summary.context_term_count == 3


def test_run_proteomics_workflow_supports_maxquant_mode() -> None:
    maxquant_dir = _workflow_fixture("maxquant_biological")
    result = run_proteomics_workflow(
        MaxquantWorkflowConfig(
            evidence_txt_path=maxquant_dir / "evidence.txt",
            peptides_txt_path=maxquant_dir / "peptides.txt",
            protein_groups_txt_path=maxquant_dir / "proteinGroups.txt",
            design_tsv_path=maxquant_dir / "design.tsv",
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            config_path=maxquant_dir / "maxquant_settings.txt",
            annotation_tsv_path=(
                _fixture_root() / "interpretation" / "protein_annotation_custom.tsv"
            ),
            context_annotation_tsv_path=_workflow_fixture(
                "biological_report_context.tsv"
            ),
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert result.mode is WorkflowMode.MAXQUANT
    assert result.design_row_count == 6
    assert result.report.summary.accepted_protein_group_count >= 1
    assert result.report.summary.enrichment_foreground_protein_count == 3
    assert result.report.summary.protein_card_count == 5
    assert result.report.summary.context_term_count == 3


def test_run_proteomics_workflow_supports_tmt_mode() -> None:
    result = run_proteomics_workflow(
        TmtWorkflowConfig(
            result_tsv_path=_multiplex_fixture("maxquant_tmt_evidence.tsv"),
            design_tsv_path=_multiplex_fixture("tmt.design.tsv"),
            control_channel="126",
            source_kind=TmtSearchResultSourceKind.MAXQUANT,
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert result.mode is WorkflowMode.TMT
    assert result.design_row_count == 8
    assert result.report.summary.protein_ratio_count == 12


def test_run_proteomics_workflow_supports_silac_mode() -> None:
    result = run_proteomics_workflow(
        SilacWorkflowConfig(
            input_tsv_path=_silac_fixture("silac_differential_features.tsv"),
            design_tsv_path=_silac_fixture("silac_differential.design.tsv"),
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert result.mode is WorkflowMode.SILAC
    assert result.design_row_count == 4
    assert result.report.summary.differential_result_count == 3


def test_run_proteomics_workflow_supports_ptm_mode() -> None:
    result = run_proteomics_workflow(
        PtmWorkflowConfig(
            evidence_tsv_path=_ptm_fixture("localization_results.tsv"),
            proteins_fasta_path=_fixture_root() / "fasta" / "ptm_sites.fasta",
            feature_tsv_path=_ptm_fixture("ptm_features.tsv"),
            design_tsv_path=_ptm_fixture("ptm.design.tsv"),
            condition_a="control",
            condition_b="treated",
            batch_field="",
            annotation_tsv_path=_ptm_fixture("ptm_site_annotations.tsv"),
        )
    )

    assert result.mode is WorkflowMode.PTM
    assert result.design_row_count == 4
    assert result.report.summary.accepted_evidence_count >= 1


def test_run_proteomics_workflow_supports_targeted_matrix_mode() -> None:
    result = run_proteomics_workflow(
        TargetedWorkflowConfig(
            input_tsv_path=_targeted_fixture("skyline_targeted_results.tsv"),
            source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
            stage=TargetedWorkflowStage.MATRIX,
        )
    )

    assert result.mode is WorkflowMode.TARGETED
    assert result.source_report is not None
    assert result.source_report.summary.observation_count == 6
    assert result.report.summary.target_count == 2


def test_run_proteomics_workflow_supports_targeted_assay_qc_mode() -> None:
    result = run_proteomics_workflow(
        TargetedWorkflowConfig(
            input_tsv_path=_targeted_fixture("skyline_targeted_qc_results.tsv"),
            source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
            stage=TargetedWorkflowStage.ASSAY_QC,
            design_tsv_path=_targeted_fixture("skyline_targeted_qc.design.tsv"),
        )
    )

    assert result.mode is WorkflowMode.TARGETED
    assert result.design_row_count == 4
    assert result.source_report is not None
    assert result.report.summary.target_count == 2


def test_run_proteomics_workflow_supports_targeted_validation_mode(
    tmp_path: Path,
) -> None:
    result = run_proteomics_workflow(
        TargetedWorkflowConfig(
            input_tsv_path=_targeted_fixture("skyline_targeted_qc_results.tsv"),
            source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
            stage=TargetedWorkflowStage.VALIDATION,
            design_tsv_path=_targeted_fixture("skyline_targeted_qc.design.tsv"),
            discovery_claims=_targeted_discovery_claims(),
            panel_assays=_targeted_panel_assays(),
            case_condition="treatment",
            control_condition="control",
            output_dir=tmp_path / "targeted_validation",
        )
    )

    assert result.mode is WorkflowMode.TARGETED
    assert result.design_row_count == 4
    assert result.manifest is result.export_manifest
    assert result.source_report is not None
    assert (
        result.artifacts["confirmed_validation_tsv"]
        == "targeted_validation_confirmed.tsv"
    )
    assert result.warnings == result.report.warnings
    assert result.rejected_evidence == result.report.rejected_evidence
    assert result.report.summary.discovery_claim_count == 2
    assert result.report.summary.inconclusive_count == 2
