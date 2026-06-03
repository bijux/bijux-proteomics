# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    AdvancedMaxquantWorkflowConfig,
    run_advanced_maxquant_workflow,
    validate_advanced_workflow_family_contract,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _bundle_fixture(name: str) -> Path:
    return _workflow_fixture("maxquant_biological") / name


def test_run_advanced_maxquant_workflow_excludes_reverse_and_contaminants_from_biology(
    tmp_path: Path,
) -> None:
    report = run_advanced_maxquant_workflow(
        AdvancedMaxquantWorkflowConfig(
            evidence_txt_path=_bundle_fixture("evidence.txt"),
            peptides_txt_path=_bundle_fixture("peptides.txt"),
            protein_groups_txt_path=_bundle_fixture("proteinGroups.txt"),
            design_tsv_path=_bundle_fixture("design.tsv"),
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            output_dir=tmp_path / "advanced_maxquant_review",
            config_path=_bundle_fixture("maxquant_settings.txt"),
            annotation_tsv_path=(
                Path(__file__).resolve().parent.parent
                / "fixtures"
                / "interpretation"
                / "protein_annotation_custom.tsv"
            ),
            context_annotation_tsv_path=_workflow_fixture(
                "biological_report_context.tsv"
            ),
            go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
            pathway_membership_tsv_path=_workflow_fixture(
                "biological_report_pathways.tsv"
            ),
            complex_membership_tsv_path=_workflow_fixture(
                "biological_report_complexes.tsv"
            ),
            condition_a="control",
            condition_b="treatment",
        )
    )
    assert report.manifest.family_protocol == report.family_protocol
    assert validate_advanced_workflow_family_contract(report.family_protocol) == ()
    assert (
        report.family_protocol.artifacts.workflow_manifest_json
        == "advanced_maxquant_workflow_manifest.json"
    )

    output_dir = tmp_path / "advanced_maxquant_review"
    foreground_tsv = (
        output_dir
        / report.maxquant_workflow_manifest.artifacts.enrichment_foreground_tsv
    ).read_text(encoding="utf-8")
    excluded_tsv = (
        output_dir / report.manifest.artifacts.excluded_protein_groups_tsv
    ).read_text(encoding="utf-8")
    peptide_contribution_tsv = (
        output_dir / report.manifest.artifacts.peptide_contribution_tsv
    ).read_text(encoding="utf-8")
    rejected_evidence_tsv = (
        output_dir / report.manifest.artifacts.rejected_evidence_tsv
    ).read_text(encoding="utf-8")

    assert report.summary.excluded_reverse_or_contaminant_count == 2
    assert report.summary.biological_foreground_protein_count >= 1
    assert report.summary.peptide_contribution_count >= 1
    assert "CON__KRT1" in excluded_tsv
    assert "REV__P77777" in excluded_tsv
    assert "P04637" in foreground_tsv
    assert "CON__KRT1" not in foreground_tsv
    assert "REV__P77777" not in foreground_tsv
    assert "P04637\tP04637\tPEPAAA" in peptide_contribution_tsv
    assert "CON__KRT1" in rejected_evidence_tsv
    assert "REV__P77777" in rejected_evidence_tsv
    assert report.manifest.artifacts.supported_claim_tsv is not None
    assert report.manifest.artifacts.rejected_claim_tsv is not None
    assert (output_dir / report.manifest.artifacts.supported_claim_tsv).exists()
    assert (output_dir / report.manifest.artifacts.rejected_claim_tsv).exists()


def test_run_advanced_maxquant_workflow_preserves_only_site_filtered_groups_separately(
    tmp_path: Path,
) -> None:
    report = run_advanced_maxquant_workflow(
        AdvancedMaxquantWorkflowConfig(
            evidence_txt_path=_bundle_fixture("evidence.txt"),
            peptides_txt_path=_bundle_fixture("peptides.txt"),
            protein_groups_txt_path=_bundle_fixture("proteinGroups.txt"),
            design_tsv_path=_bundle_fixture("design.tsv"),
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            output_dir=tmp_path / "advanced_maxquant_site_filtering",
            config_path=_bundle_fixture("maxquant_settings.txt"),
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert report.summary.additional_filtered_protein_group_count == 1
    rejected_evidence_tsv = (
        tmp_path
        / "advanced_maxquant_site_filtering"
        / report.manifest.artifacts.rejected_evidence_tsv
    ).read_text(encoding="utf-8")
    assert {entry.entity_id for entry in report.excluded_protein_groups} == {
        "CON__KRT1",
        "REV__P77777",
    }
    assert any(
        entry.entity_id == "P12345"
        for entry in report.maxquant_workflow.filtered_protein_groups
    )
    assert "P12345" in rejected_evidence_tsv
