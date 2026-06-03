# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from bijux_proteomics.domain.errors import ScientificEvidenceError
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import (
    AdvancedDiannWorkflowConfig,
    load_workflow_artifact_manifest,
    run_advanced_diann_workflow,
    validate_advanced_workflow_family_contract,
    validate_workflow_artifact_completeness,
    validate_workflow_artifact_inventory,
    validate_workflow_artifact_manifest,
)
from bijux_proteomics.workflow.artifact_layout import (
    WORKFLOW_ARTIFACT_INVENTORY_NAME,
    WORKFLOW_ARTIFACT_INVENTORY_SUMMARY_NAME,
)
from bijux_proteomics.workflow.pipelines.advanced_diann import (
    build_advanced_diann_workflow_report_from_bundle,
)
from bijux_proteomics.workflow.pipelines.diann_biological_workflow import (
    build_diann_biological_workflow_bundle,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_run_advanced_diann_workflow_exports_accepted_downgraded_and_rejected_evidence(
    tmp_path: Path,
) -> None:
    report = run_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "advanced_diann_review",
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
        == "advanced_diann_workflow_manifest.json"
    )

    output_dir = tmp_path / "advanced_diann_review"
    accepted_tsv = (
        output_dir / report.manifest.artifacts.accepted_proteins_tsv
    ).read_text(encoding="utf-8")
    downgraded_tsv = (
        output_dir / report.manifest.artifacts.downgraded_proteins_tsv
    ).read_text(encoding="utf-8")
    rejected_evidence_tsv = (
        output_dir / report.manifest.artifacts.rejected_evidence_tsv
    ).read_text(encoding="utf-8")
    belief_audit_tsv = (
        output_dir / report.manifest.artifacts.belief_audit_tsv
    ).read_text(encoding="utf-8")

    assert report.summary.rejected_evidence_count == 1
    assert report.manifest.artifacts.rejected_evidence_tsv == "rejected_evidence.tsv"
    assert report.summary.accepted_protein_count >= 1
    assert report.summary.downgraded_protein_count >= 1
    assert report.summary.belief_audit_entry_count >= 1
    assert "Q9Y243" in accepted_tsv
    assert "Q99999" in downgraded_tsv
    assert "shared_peptide_only" in downgraded_tsv
    assert "raw_bad_precursor" in rejected_evidence_tsv
    assert rejected_evidence_tsv.splitlines()[0] == (
        "rejected_evidence_id\tsource_surface\tsource_file\trow_number\t"
        "entity_type\tentity_id\treason_code\tdetail\trelated_artifact"
    )
    assert "audit_id\tsubject_kind\tsubject_id" in belief_audit_tsv
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "inputs").is_dir()
    assert (output_dir / "qc").is_dir()
    assert (output_dir / "evidence").is_dir()
    assert (output_dir / "matrices").is_dir()
    assert (output_dir / "stats").is_dir()
    assert (output_dir / "biology").is_dir()
    assert (output_dir / "cards").is_dir()
    assert (output_dir / "reports").is_dir()
    assert (output_dir / "reports" / report.manifest.artifacts.summary_tsv).exists()
    assert (
        output_dir / "evidence" / report.manifest.artifacts.accepted_proteins_tsv
    ).exists()
    assert (output_dir / "qc" / report.manifest.artifacts.belief_audit_tsv).exists()
    assert (
        output_dir / report.manifest.artifacts.diann_workflow_manifest_json
    ).exists()
    assert (
        output_dir / report.manifest.artifacts.biological_report_manifest_json
    ).exists()
    assert report.manifest.artifacts.supported_claim_tsv is not None
    assert report.manifest.artifacts.rejected_claim_tsv is not None
    assert (output_dir / report.manifest.artifacts.supported_claim_tsv).exists()
    assert (output_dir / report.manifest.artifacts.rejected_claim_tsv).exists()
    assert (output_dir / WORKFLOW_ARTIFACT_INVENTORY_NAME).exists()
    assert (output_dir / WORKFLOW_ARTIFACT_INVENTORY_SUMMARY_NAME).exists()
    assert (output_dir / "reports" / WORKFLOW_ARTIFACT_INVENTORY_NAME).exists()
    assert (output_dir / "reports" / WORKFLOW_ARTIFACT_INVENTORY_SUMMARY_NAME).exists()
    layout_manifest = validate_workflow_artifact_manifest(output_dir)
    validate_workflow_artifact_inventory(
        output_dir=output_dir, manifest=layout_manifest
    )
    summary_entry = next(
        entry
        for entry in layout_manifest.artifacts
        if entry.legacy_relative_path == report.manifest.artifacts.summary_tsv
    )
    assert summary_entry.output_table_schema is not None
    assert summary_entry.artifact_schema_version == "2026-05-26"
    assert summary_entry.output_table_schema.schema_version == "2026-05-26"
    assert summary_entry.output_table_schema.columns[0].name == "field"
    assert summary_entry.output_table_schema_sidecar_relative_path == (
        f"reports/{report.manifest.artifacts.summary_tsv}.schema.json"
    )
    assert (
        output_dir / "reports" / f"{report.manifest.artifacts.summary_tsv}.schema.json"
    ).exists()
    evidence_entry = next(
        entry
        for entry in layout_manifest.artifacts
        if entry.legacy_relative_path == report.manifest.artifacts.accepted_proteins_tsv
    )
    assert evidence_entry.output_table_schema is not None
    assert evidence_entry.artifact_schema_version == "2026-05-26"
    assert evidence_entry.output_table_schema.schema_version == "2026-05-26"
    assert "protein_group_id" in {
        column.name for column in evidence_entry.output_table_schema.columns
    }
    assert evidence_entry.output_table_schema_sidecar_relative_path == (
        f"evidence/{report.manifest.artifacts.accepted_proteins_tsv}.schema.json"
    )
    inventory_rows = tuple(
        csv.DictReader(
            (output_dir / WORKFLOW_ARTIFACT_INVENTORY_NAME)
            .read_text(encoding="utf-8")
            .splitlines(),
            delimiter="\t",
        )
    )
    summary_row_count = (
        len(
            (output_dir / report.manifest.artifacts.summary_tsv)
            .read_text(encoding="utf-8")
            .splitlines()
        )
        - 1
    )
    inventory_by_legacy_path = {
        row["legacy_relative_path"]: row for row in inventory_rows
    }
    assert inventory_by_legacy_path[report.manifest.artifacts.summary_tsv][
        "row_count"
    ] == str(summary_row_count)
    assert inventory_by_legacy_path[report.manifest.artifacts.accepted_proteins_tsv][
        "row_count"
    ] == str(report.summary.accepted_protein_count)
    inventory_summary = {
        row["field"]: row["value"]
        for row in csv.DictReader(
            (output_dir / WORKFLOW_ARTIFACT_INVENTORY_SUMMARY_NAME)
            .read_text(encoding="utf-8")
            .splitlines(),
            delimiter="\t",
        )
    }
    assert (
        int(inventory_summary["artifact_count"]) == len(layout_manifest.artifacts) - 2
    )
    assert int(inventory_summary["tsv_artifact_count"]) >= 10
    assert (
        int(inventory_summary["total_tsv_row_count"])
        >= report.summary.accepted_protein_count
    )


def test_run_advanced_diann_workflow_exports_fragment_coelution_when_fragment_evidence_is_supplied(
    tmp_path: Path,
) -> None:
    report = run_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "advanced_diann_with_fragments",
            condition_a="control",
            condition_b="treatment",
            fragment_mzml_paths=(_format_fixture("dia_fragment_coelution.mzml"),),
            fragment_target_tsv_path=_format_fixture("dia_fragment_targets.tsv"),
        )
    )

    output_dir = tmp_path / "advanced_diann_with_fragments"

    assert report.fragment_coelution_report is not None
    assert report.summary.fragment_coelution_run_count >= 1
    assert report.manifest.artifacts.fragment_coelution_runs_tsv is not None
    assert report.manifest.artifacts.fragment_coelution_fragments_tsv is not None
    assert (output_dir / report.manifest.artifacts.fragment_coelution_runs_tsv).exists()
    assert (
        output_dir / report.manifest.artifacts.fragment_coelution_fragments_tsv
    ).exists()


def test_advanced_diann_workflow_builds_from_a_precomputed_biological_bundle(
    tmp_path: Path,
) -> None:
    config = AdvancedDiannWorkflowConfig(
        result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
        design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
        proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
        output_dir=tmp_path / "advanced_diann_precomputed_bundle",
        condition_a="control",
        condition_b="treatment",
    )
    base_bundle = build_diann_biological_workflow_bundle(
        config.result_tsv_path,
        tuple(parse_experimental_design_table(config.design_tsv_path).accepted_entries),
        proteins_fasta_path=config.proteins_fasta_path,
        include_decoys=config.include_decoys,
        max_q_value=config.max_q_value,
        peptide_rollup_method=config.peptide_rollup_method,
        target_kind=config.target_kind,
        shared_peptide_policy=config.shared_peptide_policy,
        protein_rollup_method=config.protein_rollup_method,
        normalization_method=config.normalization_method,
        condition_a=config.condition_a,
        condition_b=config.condition_b,
    )

    report = build_advanced_diann_workflow_report_from_bundle(base_bundle, config)

    assert report.summary.accepted_protein_count >= 1
    assert report.summary.downgraded_protein_count >= 1
    assert (config.output_dir / report.manifest.artifacts.summary_tsv).exists()


def test_advanced_diann_workflow_completeness_requires_declared_belief_audit_artifact(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "advanced_diann_completeness_surface"
    report = run_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=output_dir,
            condition_a="control",
            condition_b="treatment",
        )
    )

    missing_name = report.manifest.artifacts.belief_audit_tsv
    (output_dir / missing_name).unlink()
    (output_dir / "qc" / missing_name).unlink()
    manifest = load_workflow_artifact_manifest(output_dir)
    drifted_manifest = manifest.model_copy(
        update={
            "artifacts": tuple(
                artifact
                for artifact in manifest.artifacts
                if artifact.legacy_relative_path != missing_name
            )
        }
    )
    (output_dir / "manifest.json").write_text(
        drifted_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ScientificEvidenceError,
        match="missing advanced_diann_belief_audit.tsv declared at manifest.artifacts.belief_audit_tsv",
    ):
        validate_workflow_artifact_completeness(output_dir=output_dir)
