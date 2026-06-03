# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    AdvancedMaxquantWorkflowConfig,
    AdvancedWorkflowFamilyArtifactContract,
    build_advanced_workflow_family_contract,
    validate_advanced_workflow_family_contract,
)
from bijux_proteomics.workflow.pipelines.advanced_workflow_family import (
    AdvancedWorkflowFamilyConfigContract,
    AdvancedWorkflowFamilyContract,
)


def test_build_advanced_workflow_family_contract_normalizes_shared_config_and_output_roles(
    tmp_path: Path,
) -> None:
    contract = build_advanced_workflow_family_contract(
        workflow_name="advanced_maxquant",
        config=AdvancedMaxquantWorkflowConfig(
            evidence_txt_path=Path("evidence.txt"),
            peptides_txt_path=Path("peptides.txt"),
            protein_groups_txt_path=Path("proteinGroups.txt"),
            design_tsv_path=Path("design.tsv"),
            proteins_fasta_path=Path("proteins.fasta"),
            output_dir=tmp_path / "advanced_maxquant",
        ),
        primary_input_fields=(
            "evidence_txt_path",
            "peptides_txt_path",
            "protein_groups_txt_path",
        ),
        design_input_fields=("design_tsv_path",),
        reference_input_fields=("proteins_fasta_path",),
        comparison_input_fields=("condition_a", "condition_b"),
        artifacts=AdvancedWorkflowFamilyArtifactContract(
            workflow_manifest_json="advanced_maxquant_workflow_manifest.json",
            base_workflow_manifest_json="maxquant_biological_report_manifest.json",
            review_manifest_json="biological_report_manifest.json",
            summary_tsv="advanced_maxquant_summary.tsv",
            rejected_evidence_tsv="rejected_evidence.tsv",
            supported_claim_tsv="biological_supported_claims.tsv",
            rejected_claim_tsv="biological_rejected_claims.tsv",
        ),
        note="advanced maxquant workflow contract",
    )

    assert isinstance(contract, AdvancedWorkflowFamilyContract)
    assert contract.config.output_dir_field == "output_dir"
    assert contract.config.primary_input_fields == (
        "evidence_txt_path",
        "peptides_txt_path",
        "protein_groups_txt_path",
    )
    assert contract.artifacts.workflow_manifest_json == (
        "advanced_maxquant_workflow_manifest.json"
    )
    assert validate_advanced_workflow_family_contract(contract) == ()


def test_validate_advanced_workflow_family_contract_rejects_summary_name_drift(
    tmp_path: Path,
) -> None:
    contract = AdvancedWorkflowFamilyContract(
        workflow_name="advanced_targeted",
        config=AdvancedWorkflowFamilyConfigContract(
            output_dir_field="output_dir",
            primary_input_fields=("result_tsv_path",),
            design_input_fields=("design_tsv_path",),
        ),
        artifacts=AdvancedWorkflowFamilyArtifactContract(
            workflow_manifest_json="advanced_targeted_workflow_manifest.json",
            base_workflow_manifest_json="targeted_assay_qc_workflow_manifest.json",
            summary_tsv="targeted_summary.tsv",
            rejected_evidence_tsv="rejected_evidence.tsv",
        ),
        note=str(tmp_path),
    )

    assert validate_advanced_workflow_family_contract(contract) == (
        "advanced workflow family contract requires summary_tsv 'advanced_targeted_summary.tsv'",
    )
