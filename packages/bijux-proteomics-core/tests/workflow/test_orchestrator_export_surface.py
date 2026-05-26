# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.multiplex import TmtSearchResultSourceKind
from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.targeted import (
    TargetedPanelCandidateKind,
    TargetedResultSourceKind,
    TargetedValidationDiscoveryClaimInput,
    TargetedValidationPanelAssayInput,
)
from bijux_proteomics.workflow import (
    LabelFreeWorkflowConfig,
    TargetedWorkflowConfig,
    TargetedWorkflowStage,
    TmtWorkflowConfig,
    WorkflowMode,
    run_proteomics_workflow,
    validate_workflow_artifact_manifest,
)


def _fixture_root() -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures"


def _workflow_fixture(name: str) -> Path:
    return _fixture_root() / "workflow" / name


def _multiplex_fixture(name: str) -> Path:
    return _fixture_root() / "multiplex" / name


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


def test_run_proteomics_workflow_exports_label_free_bundle_assets(
    tmp_path: Path,
) -> None:
    result = run_proteomics_workflow(
        LabelFreeWorkflowConfig(
            input_tsv_path=_workflow_fixture("biological_report_features.tsv"),
            design_tsv_path=_workflow_fixture("biological_report.design.tsv"),
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            condition_a="control",
            condition_b="treatment",
            output_dir=tmp_path / "biological_report",
        )
    )

    assert result.mode is WorkflowMode.LABEL_FREE
    assert result.export_manifest is not None
    assert (tmp_path / "biological_report" / "biological_report_manifest.json").exists()
    assert (
        tmp_path
        / "biological_report"
        / result.export_manifest.artifacts.protein_card_tsv
    ).exists()
    assert result.outputs["manifest_json"].endswith("biological_report_manifest.json")
    layout_manifest = validate_workflow_artifact_manifest(tmp_path / "biological_report")
    summary_entry = next(
        entry
        for entry in layout_manifest.artifacts
        if entry.legacy_relative_path == result.export_manifest.artifacts.summary_tsv
    )
    assert summary_entry.output_table_schema is not None
    assert summary_entry.artifact_schema_version == "2026-05-26"
    assert summary_entry.output_table_schema.schema_version == "2026-05-26"
    assert summary_entry.output_table_schema.columns[0].name == "field"
    assert summary_entry.output_table_schema_sidecar_relative_path == (
        f"reports/{result.export_manifest.artifacts.summary_tsv}.schema.json"
    )


def test_run_proteomics_workflow_exports_tmt_bundle_assets(tmp_path: Path) -> None:
    result = run_proteomics_workflow(
        TmtWorkflowConfig(
            result_tsv_path=_multiplex_fixture("maxquant_tmt_evidence.tsv"),
            design_tsv_path=_multiplex_fixture("tmt.design.tsv"),
            control_channel="126",
            source_kind=TmtSearchResultSourceKind.MAXQUANT,
            condition_a="control",
            condition_b="treatment",
            output_dir=tmp_path / "tmt_report",
        )
    )

    assert result.mode is WorkflowMode.TMT
    assert result.export_manifest is not None
    assert (tmp_path / "tmt_report" / "tmt_workflow_manifest.json").exists()
    assert (tmp_path / "tmt_report" / "label_based_report_manifest.json").exists()
    assert result.outputs["workflow_manifest_json"].endswith("tmt_workflow_manifest.json")
    layout_manifest = validate_workflow_artifact_manifest(tmp_path / "tmt_report")
    summary_entry = next(
        entry
        for entry in layout_manifest.artifacts
        if entry.legacy_relative_path == result.export_manifest.artifacts.summary_tsv
    )
    assert summary_entry.output_table_schema is not None
    assert summary_entry.artifact_schema_version == "2026-05-26"
    assert summary_entry.output_table_schema.schema_version == "2026-05-26"
    assert summary_entry.output_table_schema.columns[0].name == "field"
    assert summary_entry.output_table_schema_sidecar_relative_path == (
        f"reports/{result.export_manifest.artifacts.summary_tsv}.schema.json"
    )


def test_run_proteomics_workflow_exports_targeted_matrix_assets(
    tmp_path: Path,
) -> None:
    result = run_proteomics_workflow(
        TargetedWorkflowConfig(
            input_tsv_path=_targeted_fixture("skyline_targeted_results.tsv"),
            source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
            stage=TargetedWorkflowStage.MATRIX,
            output_dir=tmp_path / "targeted_matrix",
        )
    )

    assert result.mode is WorkflowMode.TARGETED
    assert result.export_manifest is not None
    assert (
        tmp_path / "targeted_matrix" / "targeted_matrix_workflow_manifest.json"
    ).exists()
    assert (
        tmp_path / "targeted_matrix" / result.export_manifest.artifacts.matrix_targets_tsv
    ).exists()
    assert result.outputs["workflow_manifest_json"].endswith(
        "targeted_matrix_workflow_manifest.json"
    )


def test_run_proteomics_workflow_exports_targeted_assay_qc_assets(
    tmp_path: Path,
) -> None:
    result = run_proteomics_workflow(
        TargetedWorkflowConfig(
            input_tsv_path=_targeted_fixture("skyline_targeted_qc_results.tsv"),
            source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
            stage=TargetedWorkflowStage.ASSAY_QC,
            design_tsv_path=_targeted_fixture("skyline_targeted_qc.design.tsv"),
            output_dir=tmp_path / "targeted_assay_qc",
        )
    )

    assert result.mode is WorkflowMode.TARGETED
    assert result.export_manifest is not None
    assert (
        tmp_path
        / "targeted_assay_qc"
        / "targeted_assay_qc_workflow_manifest.json"
    ).exists()
    assert (
        tmp_path
        / "targeted_assay_qc"
        / result.export_manifest.artifacts.assay_qc_fragment_ratios_tsv
    ).exists()
    assert (
        tmp_path
        / "targeted_assay_qc"
        / result.export_manifest.artifacts.matrix_summary_tsv
    ).exists()
    assert result.outputs["workflow_manifest_json"].endswith(
        "targeted_assay_qc_workflow_manifest.json"
    )


def test_run_proteomics_workflow_exports_targeted_validation_assets(
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
    assert result.export_manifest is not None
    assert (
        tmp_path
        / "targeted_validation"
        / "advanced_targeted_workflow_manifest.json"
    ).exists()
    assert (
        tmp_path
        / "targeted_validation"
        / result.export_manifest.artifacts.validation_summary_tsv
    ).exists()
    assert (
        tmp_path
        / "targeted_validation"
        / result.export_manifest.artifacts.assay_qc_unreliable_targets_tsv
    ).exists()
    assert result.outputs["workflow_manifest_json"].endswith(
        "advanced_targeted_workflow_manifest.json"
    )
    layout_manifest = validate_workflow_artifact_manifest(tmp_path / "targeted_validation")
    summary_entry = next(
        entry
        for entry in layout_manifest.artifacts
        if entry.legacy_relative_path == result.export_manifest.artifacts.summary_tsv
    )
    assert summary_entry.output_table_schema is not None
    assert summary_entry.artifact_schema_version == "2026-05-26"
    assert summary_entry.output_table_schema.schema_version == "2026-05-26"
    assert summary_entry.output_table_schema.columns[0].name == "field"
    assert summary_entry.output_table_schema_sidecar_relative_path == (
        f"reports/{result.export_manifest.artifacts.summary_tsv}.schema.json"
    )
