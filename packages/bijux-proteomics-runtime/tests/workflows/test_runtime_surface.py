# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.search_adapters import SearchAdapterKind
from bijux_proteomics_runtime.workflows.plans import (
    ExternalToolCapabilityReport,
    RerunComparisonScope,
    WorkflowArchiveMedium,
    WorkflowCacheMissReason,
    WorkflowCacheReuseDisposition,
    WorkflowCheckpointStatus,
    WorkflowDagValidationReport,
    WorkflowDiffCategory,
    WorkflowDiffReport,
    WorkflowExecutionMode,
    WorkflowExecutionReadinessReport,
    WorkflowInputRole,
    WorkflowManifestExplanationReport,
    WorkflowResumeKind,
    WorkflowSchedulerKind,
    WorkflowScientificSurface,
    WorkflowStepKind,
    WorkflowStepProvenanceReport,
    WorkflowStepReplayDisposition,
    WorkflowStreamingMode,
    WorkflowTemplateKind,
    build_deterministic_execution_contract,
    build_external_tool_capability_report,
    build_hpc_job_descriptor,
    build_large_file_streaming_policy,
    build_parallel_execution_plan,
    build_proteomics_artifact_inventory,
    build_proteomics_dag_plan,
    build_proteomics_workflow_manifest,
    build_proteomics_workflow_runtime_bundle,
    build_proteomics_workflow_template,
    build_workflow_cache_reuse_plan,
    build_reproducible_workflow_blueprint,
    build_workflow_cache_miss_explanation_report,
    build_workflow_checkpoint,
    build_workflow_diff_report,
    build_workflow_execution_readiness_report,
    build_workflow_manifest_explanation_report,
    build_workflow_replay_proof_report,
    build_workflow_rerun_comparison_artifact,
    build_workflow_run_directory_layout,
    build_workflow_runtime_archive_bundle,
    build_workflow_runtime_cache,
    build_workflow_runtime_export_bundle,
    build_workflow_runtime_state_manifest,
    build_workflow_runtime_validation_report,
    build_workflow_step_provenance_report,
    import_workflow_runtime_archive_bundle,
    instantiate_proteomics_workflow_template,
    validate_proteomics_dag_plan,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "production_run" / name


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


def test_workflow_execution_readiness_refuses_missing_tool_versions_and_resources() -> (
    None
):
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )
    hpc_job = build_hpc_job_descriptor(manifest)

    report = build_workflow_execution_readiness_report(
        manifest,
        hpc_job=hpc_job,
        available_tool_versions=("bijux-proteomics-core@0.0.0",),
        max_cpus=1,
        max_memory_gb=4,
        max_walltime_minutes=30,
    )

    assert isinstance(report, WorkflowExecutionReadinessReport)
    assert report.ready is False
    assert {issue.code for issue in report.issues} >= {
        "tool_versions_unavailable",
        "resource_guarantee_missing",
    }


def test_workflow_diff_report_separates_scientific_and_operational_changes() -> None:
    left = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
        default_container_image="ghcr.io/bijux/proteomics-runtime:v1",
    )
    right = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.SAGE,
        default_container_image="ghcr.io/bijux/proteomics-runtime:v2",
    )

    report = build_workflow_diff_report(left, right)

    assert isinstance(report, WorkflowDiffReport)
    assert any(
        entry.category is WorkflowDiffCategory.SCIENTIFIC for entry in report.entries
    )
    assert any(
        entry.category is WorkflowDiffCategory.OPERATIONAL for entry in report.entries
    )


def test_workflow_templates_are_reusable_and_instantiate_real_manifests() -> None:
    template = build_proteomics_workflow_template(
        WorkflowTemplateKind.IMPORTED_LFQ_REVIEW
    )
    manifest = instantiate_proteomics_workflow_template(
        template,
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
    )

    assert template.execution_mode is WorkflowExecutionMode.IMPORT_RESULTS
    assert manifest.execution_mode is template.execution_mode
    assert tuple(step.kind for step in manifest.steps) == template.step_kinds


def test_workflow_runtime_bundle_surfaces_cache_registry_checkpoint_and_job_script() -> (
    None
):
    bundle = build_proteomics_workflow_runtime_bundle(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
        completed_step_ids=(),
    )

    assert bundle.dag_plan.nodes
    assert bundle.container_steps
    assert len(bundle.container_steps[0].descriptor_sha256) == 64
    assert bundle.container_steps[0].step_kind is WorkflowStepKind.VALIDATE_INPUTS
    assert bundle.search_contract.tool_name == "Generic search table"
    assert bundle.deterministic_execution.workflow_id == bundle.manifest.workflow_id
    assert bundle.runtime_state.workflow_id == bundle.manifest.workflow_id
    assert bundle.run_directory_layout.root_dir == bundle.manifest.artifacts_dir
    assert bundle.cache_manifest.entries
    assert bundle.artifact_registry.artifacts
    assert bundle.artifact_inventory.artifacts
    assert bundle.parallel_plan.groups[0].step_ids
    assert "#SBATCH --job-name=" in bundle.hpc_job.script_text
    assert "#SBATCH --partition=proteomics" in bundle.hpc_job.script_text
    assert len(bundle.hpc_job.descriptor_sha256) == 64
    assert bundle.hpc_job.queue_name == "proteomics"
    assert bundle.hpc_job.container_image.startswith("ghcr.io/bijux/")
    assert bundle.hpc_job.expected_artifact_paths
    assert bundle.checkpoint.steps[0].status is WorkflowCheckpointStatus.READY
    assert bundle.checkpoint.blocked_step_ids


def test_deterministic_execution_contract_is_repeatable_for_same_manifest() -> None:
    bundle = build_proteomics_workflow_runtime_bundle(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    repeated = build_deterministic_execution_contract(
        bundle.manifest,
        dag_plan=bundle.dag_plan,
        container_steps=bundle.container_steps,
        parallel_plan=bundle.parallel_plan,
        hpc_job=bundle.hpc_job,
    )

    assert (
        repeated.execution_fingerprint
        == bundle.deterministic_execution.execution_fingerprint
    )
    assert repeated.ordered_step_ids == bundle.dag_plan.ordered_step_ids


def test_runtime_state_manifest_links_result_bindings_to_runtime_paths() -> None:
    bundle = build_proteomics_workflow_runtime_bundle(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    runtime_state = build_workflow_runtime_state_manifest(
        bundle.manifest,
        deterministic_execution=bundle.deterministic_execution,
        artifact_registry=bundle.artifact_registry,
    )

    assert runtime_state.manifest_sha256 == bundle.runtime_state.manifest_sha256
    assert runtime_state.result_bindings[0].artifact_id.startswith(
        f"{bundle.manifest.workflow_id}:"
    )
    assert runtime_state.result_bindings[0].runtime_path.startswith(
        bundle.manifest.artifacts_dir
    )


def test_workflow_run_directory_layout_is_predictable_and_reviewable() -> None:
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    layout = build_workflow_run_directory_layout(manifest)

    assert layout.root_dir == manifest.artifacts_dir
    assert any(entry.relative_path == "digest" for entry in layout.entries)
    assert any(
        entry.relative_path == "bundle/bundle.manifest.json" for entry in layout.entries
    )


def test_artifact_inventory_connects_outputs_to_run_and_step_lineage() -> None:
    bundle = build_proteomics_workflow_runtime_bundle(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    inventory = build_proteomics_artifact_inventory(
        bundle.manifest,
        artifact_registry=bundle.artifact_registry,
        run_directory_layout=bundle.run_directory_layout,
    )

    assert inventory.run_id == bundle.manifest.run_id
    assert inventory.artifacts[0].producer_step_id.endswith("digest-database")
    assert inventory.artifacts[0].relative_path.startswith("digest/")
    assert len(inventory.artifacts[0].provenance_sha256) == 64


def test_runtime_export_bundle_is_deterministic_for_same_inputs() -> None:
    bundle = build_proteomics_workflow_runtime_bundle(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    first = build_workflow_runtime_export_bundle(bundle)
    second = build_workflow_runtime_export_bundle(bundle)

    assert first.export_bundle_sha256 == second.export_bundle_sha256
    assert first.artifact_inventory.artifacts[0].artifact_id.startswith(
        f"{bundle.manifest.workflow_id}:"
    )


def test_workflow_runtime_archive_bundle_preserves_portable_artifact_descriptors() -> (
    None
):
    bundle = build_proteomics_workflow_runtime_bundle(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )
    export_bundle = build_workflow_runtime_export_bundle(bundle)

    archive_bundle = build_workflow_runtime_archive_bundle(
        export_bundle,
        archive_medium=WorkflowArchiveMedium.PORTABLE_JSON,
    )

    assert archive_bundle.workflow_id == export_bundle.workflow_id
    assert archive_bundle.export_bundle_sha256 == export_bundle.export_bundle_sha256
    assert archive_bundle.archived_artifacts[0].relative_path == (
        export_bundle.artifact_inventory.artifacts[0].relative_path
    )
    assert archive_bundle.archived_artifacts[0].provenance_sha256 == (
        export_bundle.artifact_inventory.artifacts[0].provenance_sha256
    )


def test_import_workflow_runtime_archive_bundle_restores_export_and_provenance() -> (
    None
):
    bundle = build_proteomics_workflow_runtime_bundle(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )
    export_bundle = build_workflow_runtime_export_bundle(bundle)
    archive_bundle = build_workflow_runtime_archive_bundle(export_bundle)

    restored_export, report = import_workflow_runtime_archive_bundle(
        archive_bundle.to_dict()
    )

    assert restored_export.export_bundle_sha256 == export_bundle.export_bundle_sha256
    assert report.imported_export_bundle_sha256 == export_bundle.export_bundle_sha256
    assert report.preserved_artifact_count == len(
        export_bundle.artifact_inventory.artifacts
    )
    assert report.portable_review_ready is True


def test_workflow_rerun_comparison_artifact_tracks_same_sample_drift() -> None:
    bundle = build_proteomics_workflow_runtime_bundle(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )
    previous_export = build_workflow_runtime_export_bundle(bundle)
    current_export = build_workflow_runtime_export_bundle(
        bundle.model_copy(
            update={
                "artifact_inventory": bundle.artifact_inventory.model_copy(
                    update={
                        "artifacts": (
                            bundle.artifact_inventory.artifacts[0].model_copy(
                                update={"relative_path": "digest/manifest-rerun.json"}
                            ),
                            *bundle.artifact_inventory.artifacts[1:],
                        )
                    }
                )
            }
        )
    )
    previous_archive = build_workflow_runtime_archive_bundle(previous_export)
    current_archive = build_workflow_runtime_archive_bundle(current_export)

    comparison = build_workflow_rerun_comparison_artifact(
        previous_archive,
        current_archive,
        comparison_scope=RerunComparisonScope.SAME_SAMPLE,
        subject_id="sample-A",
    )

    assert comparison.comparison_scope is RerunComparisonScope.SAME_SAMPLE
    assert "artifact_inventory" in comparison.changed_surfaces
    assert comparison.drifted_artifacts
    assert comparison.drifted_artifacts[0].current_relative_path.endswith(
        "manifest-rerun.json"
    )


def test_runtime_validation_report_confirms_bundle_integrity() -> None:
    bundle = build_proteomics_workflow_runtime_bundle(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    report = build_workflow_runtime_validation_report(bundle)

    assert report.valid is True
    assert report.export_bundle_sha256
    assert "dag-plan" in report.checked_surfaces
    assert "artifact-inventory" in report.checked_surfaces


def test_runtime_bundle_exposes_validated_dag_and_parallel_layers() -> None:
    bundle = build_proteomics_workflow_runtime_bundle(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    direct_dag = build_proteomics_dag_plan(bundle.manifest)
    validation = validate_proteomics_dag_plan(bundle.dag_plan)

    assert isinstance(validation, WorkflowDagValidationReport)
    assert validation.valid is True
    assert bundle.dag_plan.ordered_step_ids == direct_dag.ordered_step_ids
    assert bundle.parallel_plan.groups[0].step_ids == (
        f"{bundle.manifest.workflow_id}-validate-inputs",
    )
    assert (
        bundle.deterministic_execution.ordered_step_ids
        == bundle.dag_plan.ordered_step_ids
    )


def test_large_file_policy_and_parallel_groups_are_explicit() -> None:
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
        streaming_threshold_bytes=1,
    )

    policy = build_large_file_streaming_policy(manifest, threshold_bytes=1)
    parallel = build_parallel_execution_plan(manifest)

    assert all(
        entry.mode is WorkflowStreamingMode.STREAMING for entry in policy.entries
    )
    assert parallel.groups[0].step_ids == (f"{manifest.workflow_id}-validate-inputs",)
    assert len(parallel.groups) >= 3


def test_workflow_cache_keys_reflect_toolchain_and_policy_assumptions() -> None:
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
        default_container_image="ghcr.io/bijux/proteomics-runtime:v1",
    )
    changed_manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
        default_container_image="ghcr.io/bijux/proteomics-runtime:v2",
    )

    first_entry = build_workflow_runtime_cache(manifest).entries[0]
    changed_entry = build_workflow_runtime_cache(changed_manifest).entries[0]

    assert manifest.runtime_policies
    assert first_entry.tool_versions[-1].endswith(
        ":ghcr.io/bijux/proteomics-runtime:v1"
    )
    assert any(
        policy.startswith("digest:") for policy in first_entry.policy_assumptions
    )
    assert first_entry.cache_key != changed_entry.cache_key


def test_workflow_cache_miss_explanations_identify_toolchain_changes() -> None:
    baseline = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
        default_container_image="ghcr.io/bijux/proteomics-runtime:v1",
    )
    changed = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
        default_container_image="ghcr.io/bijux/proteomics-runtime:v2",
    )

    report = build_workflow_cache_miss_explanation_report(
        build_workflow_runtime_cache(changed),
        build_workflow_runtime_cache(baseline),
    )

    assert report.reusable is False
    assert any(
        entry.reason is WorkflowCacheMissReason.TOOLCHAIN_CHANGED
        for entry in report.entries
    )


def test_workflow_cache_miss_explanations_identify_schema_changes() -> None:
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    baseline = build_workflow_runtime_cache(
        manifest,
        cache_schema_version="1.0.0",
    )
    changed = build_workflow_runtime_cache(
        manifest,
        cache_schema_version="2.0.0",
    )
    report = build_workflow_cache_miss_explanation_report(changed, baseline)

    assert report.reusable is False
    assert any(
        entry.reason is WorkflowCacheMissReason.SCHEMA_CHANGED
        for entry in report.entries
    )


def test_workflow_manifest_records_fdr_threshold_in_policies_and_bundle_command_preview() -> (
    None
):
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
        fdr_q_value_threshold=0.05,
    )

    assert "fdr:q-value-threshold=0.05" in manifest.runtime_policies
    fdr_step = next(
        step for step in manifest.steps if step.kind is WorkflowStepKind.CALCULATE_FDR
    )
    bundle_step = next(
        step for step in manifest.steps if step.kind is WorkflowStepKind.BUILD_RUN_BUNDLE
    )
    assert "--q-value-threshold" in fdr_step.command_preview
    assert "0.05" in fdr_step.command_preview
    assert "--fdr-threshold" in bundle_step.command_preview
    assert "0.05" in bundle_step.command_preview


def test_workflow_cache_keys_track_semantic_fdr_parameters_and_dependent_bundle_surfaces() -> (
    None
):
    baseline_manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
        fdr_q_value_threshold=0.01,
    )
    changed_manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
        fdr_q_value_threshold=0.05,
    )

    baseline_entries = {
        entry.surface: entry for entry in build_workflow_runtime_cache(baseline_manifest).entries
    }
    changed_entries = {
        entry.surface: entry for entry in build_workflow_runtime_cache(changed_manifest).entries
    }

    assert baseline_entries["digestion"].cache_key == changed_entries["digestion"].cache_key
    assert (
        baseline_entries["search-normalization"].cache_key
        == changed_entries["search-normalization"].cache_key
    )
    assert baseline_entries["fdr-score"].parameter_assumptions == (
        "fdr:q-value-threshold=0.01",
    )
    assert changed_entries["fdr-score"].parameter_assumptions == (
        "fdr:q-value-threshold=0.05",
    )
    assert (
        baseline_entries["fdr-score"].cache_key
        != changed_entries["fdr-score"].cache_key
    )
    assert (
        baseline_entries["run-bundle"].dependency_cache_keys
        != changed_entries["run-bundle"].dependency_cache_keys
    )
    assert (
        baseline_entries["run-bundle"].cache_key
        != changed_entries["run-bundle"].cache_key
    )


def test_workflow_cache_miss_explanations_identify_parameter_and_dependency_changes() -> (
    None
):
    baseline_manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
        fdr_q_value_threshold=0.01,
    )
    changed_manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
        fdr_q_value_threshold=0.05,
    )

    report = build_workflow_cache_miss_explanation_report(
        build_workflow_runtime_cache(changed_manifest),
        build_workflow_runtime_cache(baseline_manifest),
    )
    reasons_by_surface = {entry.surface: entry.reason for entry in report.entries}

    assert reasons_by_surface["fdr-score"] is WorkflowCacheMissReason.PARAMETERS_CHANGED
    assert reasons_by_surface["run-bundle"] is WorkflowCacheMissReason.DEPENDENCY_CHANGED


def test_workflow_cache_miss_explanations_identify_scientific_input_checksum_changes(
    tmp_path: Path,
) -> None:
    changed_design = tmp_path / "design.changed.tsv"
    changed_design.write_text(
        _fixture("design.tsv").read_text(encoding="utf-8").replace(
            "control", "control_shifted"
        ),
        encoding="utf-8",
    )

    baseline_manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )
    changed_manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=changed_design,
        search_adapter_kind=SearchAdapterKind.GENERIC,
    )

    report = build_workflow_cache_miss_explanation_report(
        build_workflow_runtime_cache(changed_manifest),
        build_workflow_runtime_cache(baseline_manifest),
    )
    reasons_by_surface = {entry.surface: entry.reason for entry in report.entries}

    assert reasons_by_surface["quant-parse"] is (
        WorkflowCacheMissReason.SCIENTIFIC_INPUTS_CHANGED
    )


def test_workflow_cache_reuse_plan_reruns_fdr_and_bundle_when_q_value_threshold_changes() -> (
    None
):
    baseline_manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
        fdr_q_value_threshold=0.01,
    )
    changed_manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.GENERIC,
        fdr_q_value_threshold=0.05,
    )

    reuse_plan = build_workflow_cache_reuse_plan(
        changed_manifest,
        expected=build_workflow_runtime_cache(changed_manifest),
        observed=build_workflow_runtime_cache(baseline_manifest),
    )

    assert any(step_id.endswith("digest-database") for step_id in reuse_plan.reused_step_ids)
    assert any(
        step_id.endswith("normalize-identifications")
        for step_id in reuse_plan.reused_step_ids
    )
    assert any(step_id.endswith("quantify-features") for step_id in reuse_plan.reused_step_ids)
    assert any(step_id.endswith("calculate-fdr") for step_id in reuse_plan.rerun_step_ids)
    assert any(step_id.endswith("build-run-bundle") for step_id in reuse_plan.rerun_step_ids)

    decisions_by_surface = {decision.surface: decision for decision in reuse_plan.decisions}
    assert (
        decisions_by_surface["fdr-score"].disposition
        is WorkflowCacheReuseDisposition.RERUN
    )
    assert decisions_by_surface["fdr-score"].reasons == ("parameters-changed",)
    assert (
        decisions_by_surface["run-bundle"].disposition
        is WorkflowCacheReuseDisposition.RERUN
    )
    assert decisions_by_surface["run-bundle"].reasons == ("dependency-changed",)


def test_external_search_mode_and_checkpoint_resume_contract_are_stable() -> None:
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.SAGE,
        scheduler=WorkflowSchedulerKind.SLURM,
    )
    cache_manifest = build_workflow_runtime_cache(manifest)
    artifact_registry = build_proteomics_workflow_runtime_bundle(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        search_adapter_kind=SearchAdapterKind.SAGE,
    ).artifact_registry
    checkpoint = build_workflow_checkpoint(
        manifest,
        artifact_registry=artifact_registry,
        cache_manifest=cache_manifest,
        completed_step_ids=(
            f"{manifest.workflow_id}-validate-inputs",
            f"{manifest.workflow_id}-digest-database",
        ),
    )
    hpc_job = build_hpc_job_descriptor(manifest)

    assert manifest.execution_mode is WorkflowExecutionMode.EXTERNAL_SEARCH
    assert any(
        step.kind is WorkflowStepKind.RUN_SEARCH_ENGINE for step in manifest.steps
    )
    assert checkpoint.completed_step_ids == (
        f"{manifest.workflow_id}-validate-inputs",
        f"{manifest.workflow_id}-digest-database",
    )
    assert checkpoint.steps[0].resume_kind is WorkflowResumeKind.NON_RESUMABLE
    assert checkpoint.steps[1].resume_kind is WorkflowResumeKind.RESUMABLE
    assert any(
        step.resume_kind is WorkflowResumeKind.EXTERNAL_STATE
        for step in checkpoint.steps
        if step.step_id.endswith("run-search-engine")
    )
    assert "search-runner submit" in hpc_job.script_text
