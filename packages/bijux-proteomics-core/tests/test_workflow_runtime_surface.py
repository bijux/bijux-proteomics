# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import (
    SearchAdapterKind,
    build_deterministic_execution_contract,
    build_workflow_run_directory_layout,
    build_workflow_runtime_state_manifest,
    WorkflowCheckpointStatus,
    WorkflowExecutionMode,
    WorkflowInputRole,
    WorkflowSchedulerKind,
    WorkflowStepKind,
    WorkflowStreamingMode,
    build_hpc_job_descriptor,
    build_large_file_streaming_policy,
    build_parallel_execution_plan,
    build_proteomics_workflow_manifest,
    build_proteomics_workflow_runtime_bundle,
    build_workflow_checkpoint,
    build_workflow_runtime_cache,
)


def _fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "production_run" / name


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
    assert bundle.search_contract.tool_name == "Generic search table"
    assert bundle.deterministic_execution.workflow_id == bundle.manifest.workflow_id
    assert bundle.runtime_state.workflow_id == bundle.manifest.workflow_id
    assert bundle.run_directory_layout.root_dir == bundle.manifest.artifacts_dir
    assert bundle.cache_manifest.entries
    assert bundle.artifact_registry.artifacts
    assert bundle.parallel_plan.groups[0].step_ids
    assert "#SBATCH --job-name=" in bundle.hpc_job.script_text
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
        container_steps=bundle.container_steps,
        parallel_plan=bundle.parallel_plan,
        hpc_job=bundle.hpc_job,
    )

    assert (
        repeated.execution_fingerprint
        == bundle.deterministic_execution.execution_fingerprint
    )
    assert repeated.ordered_step_ids == tuple(
        step.step_id for step in bundle.manifest.steps
    )


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
    assert "search-runner submit" in hpc_job.script_text
