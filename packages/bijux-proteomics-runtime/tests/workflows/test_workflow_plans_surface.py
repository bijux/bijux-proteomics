# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.identification.search_adapters import SearchAdapterKind
from bijux_proteomics_runtime.workflows.plans import (
    ExternalToolCapabilityReport,
    WorkflowDataType,
    WorkflowDagValidationReport,
    WorkflowExecutionMode,
    WorkflowInputRole,
    WorkflowManifestExplanationReport,
    WorkflowScientificSurface,
    WorkflowStepKind,
    WorkflowStepProvenanceReport,
    WorkflowStepReplayDisposition,
    WorkflowStepTypeValidationReport,
    build_external_tool_capability_report,
    build_parallel_execution_plan,
    build_proteomics_dag_plan,
    build_proteomics_workflow_manifest,
    build_proteomics_workflow_runtime_bundle,
    build_reproducible_workflow_blueprint,
    validate_proteomics_workflow_step_types,
    validate_proteomics_dag_plan,
    build_workflow_manifest_explanation_report,
    build_workflow_replay_proof_report,
    build_workflow_runtime_export_bundle,
    build_workflow_step_provenance_report,
)


def _fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parents[4]
        / "packages"
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / "production_run"
        / name
    )


def test_workflow_manifest_projects_imported_results_into_dag_ready_steps() -> None:
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    assert manifest.execution_mode is WorkflowExecutionMode.IMPORT_RESULTS
    assert manifest.sample_id == "sample-A"
    assert manifest.search_adapter_kind is SearchAdapterKind.GENERIC
    assert [step.kind for step in manifest.steps] == [
        WorkflowStepKind.VALIDATE_INPUTS,
        WorkflowStepKind.DIGEST_DATABASE,
        WorkflowStepKind.NORMALIZE_IDENTIFICATIONS,
        WorkflowStepKind.CALCULATE_FDR,
        WorkflowStepKind.QUANTIFY_FEATURES,
        WorkflowStepKind.RUN_QC,
        WorkflowStepKind.BUILD_RUN_BUNDLE,
    ]
    assert {asset.role for asset in manifest.input_assets} == {
        WorkflowInputRole.PROTEINS,
        WorkflowInputRole.SPECTRA,
        WorkflowInputRole.IDENTIFICATIONS,
        WorkflowInputRole.FEATURES,
        WorkflowInputRole.DESIGN,
    }


def test_reproducible_workflow_blueprint_connects_sequence_search_fdr_quant_qc_and_evidence() -> (
    None
):
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    blueprint = build_reproducible_workflow_blueprint(manifest)

    assert blueprint.workflow_id == manifest.workflow_id
    surfaces = {entry.scientific_surface for entry in blueprint.steps}
    assert WorkflowScientificSurface.SEQUENCE_INTAKE in surfaces
    assert WorkflowScientificSurface.SEARCH_INGESTION in surfaces
    assert WorkflowScientificSurface.CONFIDENCE_SCORING in surfaces
    assert WorkflowScientificSurface.QUANTIFICATION in surfaces
    assert WorkflowScientificSurface.QUALITY_CONTROL in surfaces
    assert WorkflowScientificSurface.EVIDENCE_SYNTHESIS in surfaces


def test_workflow_dag_projection_makes_execution_order_and_surfaces_explicit() -> None:
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    dag_plan = build_proteomics_dag_plan(manifest)
    validation = validate_proteomics_dag_plan(dag_plan)
    node_by_id = {node.node_id: node for node in dag_plan.nodes}

    assert isinstance(validation, WorkflowDagValidationReport)
    assert validation.valid is True
    assert dag_plan.ordered_step_ids == (
        f"{manifest.workflow_id}-validate-inputs",
        f"{manifest.workflow_id}-digest-database",
        f"{manifest.workflow_id}-normalize-identifications",
        f"{manifest.workflow_id}-calculate-fdr",
        f"{manifest.workflow_id}-quantify-features",
        f"{manifest.workflow_id}-run-qc",
        f"{manifest.workflow_id}-build-run-bundle",
    )
    assert (
        node_by_id[f"{manifest.workflow_id}-validate-inputs"].scientific_surface
        is WorkflowScientificSurface.SEQUENCE_INTAKE
    )
    assert (
        node_by_id[f"{manifest.workflow_id}-normalize-identifications"].execution_layer
        == 1
    )
    assert node_by_id[f"{manifest.workflow_id}-quantify-features"].consumes_roles == (
        WorkflowInputRole.FEATURES,
        WorkflowInputRole.DESIGN,
    )
    assert node_by_id[f"{manifest.workflow_id}-quantify-features"].input_data_types == (
        WorkflowDataType.MS1_FEATURE_TABLE,
        WorkflowDataType.NORMALIZED_IDENTIFICATION_ROWS,
        WorkflowDataType.EXPERIMENTAL_DESIGN_TABLE,
    )
    assert node_by_id[f"{manifest.workflow_id}-quantify-features"].output_data_types == (
        WorkflowDataType.PEPTIDE_QUANT_MATRIX,
    )
    assert any(
        edge.source_node_id == f"{manifest.workflow_id}-calculate-fdr"
        and edge.target_node_id == f"{manifest.workflow_id}-build-run-bundle"
        for edge in dag_plan.edges
    )


def test_workflow_step_type_validation_makes_quant_and_bundle_contracts_explicit() -> None:
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    report = validate_proteomics_workflow_step_types(manifest)
    step_by_id = {step.step_id: step for step in manifest.steps}

    assert isinstance(report, WorkflowStepTypeValidationReport)
    assert report.valid is True
    assert step_by_id[f"{manifest.workflow_id}-build-run-bundle"].input_data_types == (
        WorkflowDataType.SPECTRA_DOCUMENT,
        WorkflowDataType.NORMALIZED_IDENTIFICATION_ROWS,
        WorkflowDataType.FDR_SCORED_IDENTIFICATION_ROWS,
        WorkflowDataType.QC_SUMMARY_REPORT,
        WorkflowDataType.PEPTIDE_QUANT_MATRIX,
    )
    assert step_by_id[f"{manifest.workflow_id}-build-run-bundle"].output_data_types == (
        WorkflowDataType.NORMALIZED_RUN_BUNDLE,
    )


def test_workflow_dag_rejects_cycles_before_parallel_execution() -> None:
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )
    mutated_steps = []
    for step in manifest.steps:
        if step.kind is WorkflowStepKind.VALIDATE_INPUTS:
            mutated_steps.append(
                step.model_copy(
                    update={
                        "depends_on": (
                            f"{manifest.workflow_id}-build-run-bundle",
                        )
                    }
                )
            )
            continue
        mutated_steps.append(step)
    cyclic_manifest = manifest.model_copy(update={"steps": tuple(mutated_steps)})

    with pytest.raises(ValueError, match="cannot be projected into a deterministic dag"):
        build_proteomics_dag_plan(cyclic_manifest)
    with pytest.raises(ValueError, match="cannot be projected into a deterministic dag"):
        build_parallel_execution_plan(cyclic_manifest)


def test_workflow_manifest_explanation_report_makes_configuration_choices_explicit() -> (
    None
):
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    report = build_workflow_manifest_explanation_report(manifest)

    assert isinstance(report, WorkflowManifestExplanationReport)
    assert report.workflow_id == manifest.workflow_id
    categories = {entry.category for entry in report.entries}
    assert {
        "execution_mode",
        "search_adapter",
        "scheduler",
        "inputs",
        "quantification",
    } <= categories


def test_workflow_step_provenance_report_survives_resume_and_replay() -> None:
    bundle = build_proteomics_workflow_runtime_bundle(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
        completed_step_ids=(
            "sample-a-generic-workflow-validate-inputs",
            "sample-a-generic-workflow-digest-database",
        ),
    )

    report = build_workflow_step_provenance_report(
        bundle.manifest,
        checkpoint=bundle.checkpoint,
        replayed_step_ids=("sample-a-generic-workflow-digest-database",),
    )

    assert isinstance(report, WorkflowStepProvenanceReport)
    replayed = next(
        entry
        for entry in report.entries
        if entry.step_id == "sample-a-generic-workflow-digest-database"
    )
    reused = next(
        entry
        for entry in report.entries
        if entry.step_id == "sample-a-generic-workflow-validate-inputs"
    )
    assert replayed.replay_disposition is WorkflowStepReplayDisposition.REPLAYED
    assert reused.replay_disposition is WorkflowStepReplayDisposition.REUSED


def test_workflow_replay_proof_report_explains_when_reruns_change_outputs() -> None:
    runtime_bundle = build_proteomics_workflow_runtime_bundle(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )
    previous_export = build_workflow_runtime_export_bundle(runtime_bundle)
    current_export = build_workflow_runtime_export_bundle(
        runtime_bundle.model_copy(
            update={
                "artifact_inventory": runtime_bundle.artifact_inventory.model_copy(
                    update={
                        "artifacts": (
                            runtime_bundle.artifact_inventory.artifacts[0].model_copy(
                                update={"absolute_path": str(_fixture("design.tsv"))}
                            ),
                            *runtime_bundle.artifact_inventory.artifacts[1:],
                        )
                    }
                )
            }
        )
    )

    report = build_workflow_replay_proof_report(previous_export, current_export)

    assert report.workflow_id == previous_export.workflow_id
    assert report.equivalent is False
    changed_surface = next(
        entry for entry in report.entries if entry.surface == "artifact_inventory"
    )
    assert changed_surface.changed is True


def test_external_tool_capability_report_blocks_nonlaunchable_adapters() -> None:
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    report = build_external_tool_capability_report(manifest)

    assert isinstance(report, ExternalToolCapabilityReport)
    assert report.executable is False
    assert any(issue.code == "adapter_not_launchable" for issue in report.issues)
