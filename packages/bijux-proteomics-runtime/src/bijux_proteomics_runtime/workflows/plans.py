# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Workflow-runtime planning contracts for proteomics operator flows."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    get_search_adapter_manifest,
)
from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    detect_proteomics_format,
    parse_experimental_design_table,
)
from bijux_proteomics.lab.qc import _stable_sha256 as _stable_model_sha256
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class WorkflowSchedulerKind(StrEnum):
    """Supported workflow scheduler surfaces for exported job descriptors."""

    LOCAL = "local"
    SLURM = "slurm"


class WorkflowInputRole(StrEnum):
    """Stable workflow input roles."""

    PROTEINS = "proteins"
    SPECTRA = "spectra"
    IDENTIFICATIONS = "identifications"
    FEATURES = "features"
    DESIGN = "design"


class WorkflowStreamingMode(StrEnum):
    """How the workflow should access one input artifact."""

    EAGER = "eager"
    STREAMING = "streaming"


class WorkflowExecutionMode(StrEnum):
    """Whether the workflow imports results or runs an external engine."""

    IMPORT_RESULTS = "import-results"
    EXTERNAL_SEARCH = "external-search"


class WorkflowStepKind(StrEnum):
    """Stable proteomics workflow step kinds."""

    VALIDATE_INPUTS = "validate-inputs"
    DIGEST_DATABASE = "digest-database"
    RUN_SEARCH_ENGINE = "run-search-engine"
    NORMALIZE_IDENTIFICATIONS = "normalize-identifications"
    CALCULATE_FDR = "calculate-fdr"
    QUANTIFY_FEATURES = "quantify-features"
    RUN_QC = "run-qc"
    BUILD_RUN_BUNDLE = "build-run-bundle"


class WorkflowArtifactKind(StrEnum):
    """Artifact categories produced across workflow planning surfaces."""

    DIGEST_MANIFEST = "digest-manifest"
    DIGEST_EXPORT = "digest-export"
    SEARCH_JOB = "search-job"
    SEARCH_RESULTS = "search-results"
    NORMALIZED_IDENTIFICATIONS = "normalized-identifications"
    FDR_REPORT = "fdr-report"
    QUANT_REPORT = "quant-report"
    QC_REPORT = "qc-report"
    RUN_BUNDLE = "run-bundle"
    JOB_DESCRIPTOR = "job-descriptor"
    CHECKPOINT = "checkpoint"


class WorkflowCheckpointStatus(StrEnum):
    """Stable status values for checkpointed workflow steps."""

    PENDING = "pending"
    READY = "ready"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class WorkflowPathKind(StrEnum):
    """Stable distinction between runtime files and directories."""

    FILE = "file"
    DIRECTORY = "directory"


class WorkflowCacheMissReason(StrEnum):
    """Stable reasons why a reusable runtime cache entry could not be reused."""

    ENTRY_MISSING = "entry-missing"
    SCIENTIFIC_INPUTS_CHANGED = "scientific-inputs-changed"
    PARAMETERS_CHANGED = "parameters-changed"
    TOOLCHAIN_CHANGED = "toolchain-changed"
    POLICY_CHANGED = "policy-changed"
    SCHEMA_CHANGED = "schema-changed"
    DEPENDENCY_CHANGED = "dependency-changed"
    CACHE_LAYOUT_CHANGED = "cache-layout-changed"


class WorkflowResumeKind(StrEnum):
    """Stable resume semantics for one workflow step."""

    RESUMABLE = "resumable"
    NON_RESUMABLE = "non-resumable"
    EXTERNAL_STATE = "external-state"


class WorkflowScientificSurface(StrEnum):
    """Scientific surfaces connected by a runtime workflow blueprint."""

    SEQUENCE_INTAKE = "sequence_intake"
    SEARCH_INGESTION = "search_ingestion"
    CONFIDENCE_SCORING = "confidence_scoring"
    QUANTIFICATION = "quantification"
    QUALITY_CONTROL = "quality_control"
    EVIDENCE_SYNTHESIS = "evidence_synthesis"


class DeterministicExecutionContract(JsonModel):
    """Stable reproducibility contract over one runtime execution plan."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    manifest_sha256: str = Field(..., min_length=64, max_length=64)
    input_fingerprint: str = Field(..., min_length=64, max_length=64)
    policy_fingerprint: str = Field(..., min_length=64, max_length=64)
    ordered_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    parallel_group_ids: tuple[str, ...] = Field(default_factory=tuple)
    container_steps_sha256: str = Field(..., min_length=64, max_length=64)
    hpc_job_sha256: str = Field(..., min_length=64, max_length=64)
    execution_fingerprint: str = Field(..., min_length=64, max_length=64)


class WorkflowBlueprintStepMapping(JsonModel):
    """One manifest step mapped onto a scientific workflow surface."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    step_kind: WorkflowStepKind
    scientific_surface: WorkflowScientificSurface
    required_input_roles: tuple[WorkflowInputRole, ...] = Field(default_factory=tuple)
    produced_artifact_kinds: tuple[WorkflowArtifactKind, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class ReproducibleWorkflowBlueprint(JsonModel):
    """Reviewable scientific blueprint projected from a runtime workflow manifest."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    execution_mode: WorkflowExecutionMode
    input_roles: tuple[WorkflowInputRole, ...] = Field(default_factory=tuple)
    steps: tuple[WorkflowBlueprintStepMapping, ...] = Field(default_factory=tuple)


class WorkflowManifestExplanationEntry(JsonModel):
    """One explainable workflow configuration choice captured from a manifest."""

    model_config = ConfigDict(extra="forbid")

    category: str = Field(..., min_length=1)
    selected_value: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)


class WorkflowManifestExplanationReport(JsonModel):
    """Reviewable explanation of how one workflow manifest was configured."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    entries: tuple[WorkflowManifestExplanationEntry, ...] = Field(default_factory=tuple)


class WorkflowStepReplayDisposition(StrEnum):
    """How one workflow step is treated during resume or replay."""

    REUSED = "reused"
    REPLAYED = "replayed"
    PENDING = "pending"


class WorkflowStepProvenanceEntry(JsonModel):
    """Per-step provenance that survives resume and replay workflows."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    step_kind: WorkflowStepKind
    status: WorkflowCheckpointStatus
    resume_kind: WorkflowResumeKind
    replay_disposition: WorkflowStepReplayDisposition
    upstream_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    expected_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class WorkflowStepProvenanceReport(JsonModel):
    """Reviewable step provenance across checkpointed workflow state."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    entries: tuple[WorkflowStepProvenanceEntry, ...] = Field(default_factory=tuple)


class ExternalToolCapabilityIssue(JsonModel):
    """One capability issue discovered before launching heavy external steps."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(error|warning)$")
    message: str = Field(..., min_length=1)


class ExternalToolCapabilityReport(JsonModel):
    """Capability check for one workflow before external execution begins."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    adapter_kind: SearchAdapterKind
    executable: bool
    issues: tuple[ExternalToolCapabilityIssue, ...] = Field(default_factory=tuple)


class WorkflowExecutionReadinessIssue(JsonModel):
    """One refusal or warning about workflow execution readiness."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(error|warning)$")
    message: str = Field(..., min_length=1)


class WorkflowExecutionReadinessReport(JsonModel):
    """Execution readiness over tool versions, scheduler, and resource guarantees."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    ready: bool
    issues: tuple[WorkflowExecutionReadinessIssue, ...] = Field(default_factory=tuple)


class WorkflowDiffCategory(StrEnum):
    """Whether a workflow difference is scientific or operational."""

    SCIENTIFIC = "scientific"
    OPERATIONAL = "operational"


class WorkflowDiffEntry(JsonModel):
    """One explicit difference between two workflow manifests."""

    model_config = ConfigDict(extra="forbid")

    field_name: str = Field(..., min_length=1)
    category: WorkflowDiffCategory
    left_value: str | None = None
    right_value: str | None = None
    note: str = Field(..., min_length=1)


class WorkflowDiffReport(JsonModel):
    """Scientific and operational difference report over two workflows."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    left_workflow_id: str = Field(..., min_length=1)
    right_workflow_id: str = Field(..., min_length=1)
    entries: tuple[WorkflowDiffEntry, ...] = Field(default_factory=tuple)


class WorkflowTemplateKind(StrEnum):
    """Reusable workflow templates grounded in real proteomics surfaces."""

    IMPORTED_LFQ_REVIEW = "imported_lfq_review"
    EXTERNAL_SEARCH_LFQ_REVIEW = "external_search_lfq_review"


class ProteomicsWorkflowTemplate(JsonModel):
    """Reusable workflow template with concrete runtime and input expectations."""

    model_config = ConfigDict(extra="forbid")

    template_kind: WorkflowTemplateKind
    template_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    execution_mode: WorkflowExecutionMode
    required_input_roles: tuple[WorkflowInputRole, ...] = Field(default_factory=tuple)
    optional_input_roles: tuple[WorkflowInputRole, ...] = Field(default_factory=tuple)
    recommended_adapter_kind: SearchAdapterKind
    recommended_scheduler: WorkflowSchedulerKind
    default_container_image: str = Field(..., min_length=1)
    step_kinds: tuple[WorkflowStepKind, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class CoreResultRuntimeBinding(JsonModel):
    """One binding between a core result surface and runtime materialization."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    artifact_kind: WorkflowArtifactKind
    producer_step_id: str = Field(..., min_length=1)
    runtime_surface: str = Field(..., min_length=1)
    runtime_path: str = Field(..., min_length=1)
    expected_document_kind: str | None = None


class WorkflowRuntimeStateManifest(JsonModel):
    """Stable schema linking workflow planning inputs to runtime result state."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    manifest_sha256: str = Field(..., min_length=64, max_length=64)
    deterministic_execution_sha256: str = Field(..., min_length=64, max_length=64)
    checkpointable_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    result_bindings: tuple[CoreResultRuntimeBinding, ...] = Field(default_factory=tuple)


class WorkflowRunDirectoryLayoutEntry(JsonModel):
    """One predictable runtime path inside the workflow artifacts tree."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(..., min_length=1)
    path_kind: WorkflowPathKind
    relative_path: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    producer_step_id: str | None = None
    expected_artifact_kinds: tuple[WorkflowArtifactKind, ...] = Field(
        default_factory=tuple
    )
    required: bool = True


class WorkflowRunDirectoryLayout(JsonModel):
    """Stable contract for predictable workflow artifact layout."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    root_dir: str = Field(..., min_length=1)
    entries: tuple[WorkflowRunDirectoryLayoutEntry, ...] = Field(default_factory=tuple)


class WorkflowInputAsset(JsonModel):
    """One workflow input plus runtime handling hints."""

    model_config = ConfigDict(extra="forbid")

    role: WorkflowInputRole
    path: str = Field(..., min_length=1)
    input_kind: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=64, max_length=64)
    size_bytes: int = Field(..., ge=0)
    streaming_mode: WorkflowStreamingMode
    optional: bool = False


class WorkflowExecutionStep(JsonModel):
    """One reviewable workflow step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    kind: WorkflowStepKind
    label: str = Field(..., min_length=1)
    depends_on: tuple[str, ...] = Field(default_factory=tuple)
    consumes_roles: tuple[WorkflowInputRole, ...] = Field(default_factory=tuple)
    produces_artifacts: tuple[WorkflowArtifactKind, ...] = Field(default_factory=tuple)
    command_preview: tuple[str, ...] = Field(default_factory=tuple)
    cacheable: bool = False
    blocking: bool = True


class ProteomicsWorkflowManifest(JsonModel):
    """Stable operator-facing manifest for a proteomics workflow."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    workflow_name: str = Field(..., min_length=1)
    execution_mode: WorkflowExecutionMode
    scheduler: WorkflowSchedulerKind
    sample_id: str | None = None
    run_id: str = Field(..., min_length=1)
    search_adapter_kind: SearchAdapterKind
    search_adapter_name: str = Field(..., min_length=1)
    default_container_image: str = Field(..., min_length=1)
    artifacts_dir: str = Field(..., min_length=1)
    runtime_policies: tuple[str, ...] = Field(default_factory=tuple)
    input_assets: tuple[WorkflowInputAsset, ...] = Field(default_factory=tuple)
    steps: tuple[WorkflowExecutionStep, ...] = Field(default_factory=tuple)
    checkpointable_steps: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowDagNode(JsonModel):
    """One projected DAG node from a proteomics workflow manifest."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    step_kind: WorkflowStepKind
    depends_on: tuple[str, ...] = Field(default_factory=tuple)
    artifact_kinds: tuple[WorkflowArtifactKind, ...] = Field(default_factory=tuple)
    command_preview: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowDagEdge(JsonModel):
    """One projected DAG edge with a stable reason."""

    model_config = ConfigDict(extra="forbid")

    edge_id: str = Field(..., min_length=1)
    source_node_id: str = Field(..., min_length=1)
    target_node_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class ProteomicsDagPlan(JsonModel):
    """Projected DAG plan that downstream runtimes can consume."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    nodes: tuple[WorkflowDagNode, ...] = Field(default_factory=tuple)
    edges: tuple[WorkflowDagEdge, ...] = Field(default_factory=tuple)


class WorkflowContainerMount(JsonModel):
    """One stable mount binding for a containerized workflow step."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    target_path: str = Field(..., min_length=1)
    read_only: bool = True


class ContainerizedStepSpec(JsonModel):
    """Container execution plan for one workflow step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    step_kind: WorkflowStepKind
    image: str = Field(..., min_length=1)
    manifest_sha256: str = Field(..., min_length=64, max_length=64)
    command_sha256: str = Field(..., min_length=64, max_length=64)
    descriptor_sha256: str = Field(..., min_length=64, max_length=64)
    command: tuple[str, ...] = Field(default_factory=tuple)
    mounts: tuple[WorkflowContainerMount, ...] = Field(default_factory=tuple)
    network_policy: str = Field(..., min_length=1)
    workdir: str = Field(..., min_length=1)


class ExternalSearchToolContract(JsonModel):
    """Stable submit/wait/collect contract for one external search tool."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    adapter_kind: SearchAdapterKind
    tool_name: str = Field(..., min_length=1)
    submit_step_id: str = Field(..., min_length=1)
    collect_step_id: str = Field(..., min_length=1)
    submit_command: tuple[str, ...] = Field(default_factory=tuple)
    wait_command: tuple[str, ...] = Field(default_factory=tuple)
    collect_command: tuple[str, ...] = Field(default_factory=tuple)
    expected_outputs: tuple[WorkflowArtifactKind, ...] = Field(default_factory=tuple)
    supports_containerized_submission: bool = True
    supports_hpc_submission: bool = True


class HpcJobDescriptor(JsonModel):
    """Scheduler-ready job descriptor exported from a workflow manifest."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    scheduler: WorkflowSchedulerKind
    workflow_id: str = Field(..., min_length=1)
    job_name: str = Field(..., min_length=1)
    manifest_sha256: str = Field(..., min_length=64, max_length=64)
    ordered_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    descriptor_sha256: str = Field(..., min_length=64, max_length=64)
    cpus: int = Field(..., ge=1)
    memory_gb: int = Field(..., ge=1)
    walltime_minutes: int = Field(..., ge=1)
    queue_name: str = Field(..., min_length=1)
    resource_class: str = Field(..., min_length=1)
    container_image: str = Field(..., min_length=1)
    working_directory: str = Field(..., min_length=1)
    script_path: str = Field(..., min_length=1)
    script_text: str = Field(..., min_length=1)
    expected_artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    environment_assumptions: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowCacheEntry(JsonModel):
    """One deterministic cache materialization contract."""

    model_config = ConfigDict(extra="forbid")

    cache_key: str = Field(..., min_length=64, max_length=64)
    surface: str = Field(..., min_length=1)
    producer_step_id: str = Field(..., min_length=1)
    source_roles: tuple[WorkflowInputRole, ...] = Field(default_factory=tuple)
    source_hashes: tuple[str, ...] = Field(default_factory=tuple)
    scientific_inputs_sha256: str = Field(..., min_length=64, max_length=64)
    schema_refs: tuple[str, ...] = Field(default_factory=tuple)
    schema_sha256: str = Field(..., min_length=64, max_length=64)
    parameter_assumptions: tuple[str, ...] = Field(default_factory=tuple)
    parameter_sha256: str = Field(..., min_length=64, max_length=64)
    dependency_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    dependency_cache_keys: tuple[str, ...] = Field(default_factory=tuple)
    dependency_sha256: str = Field(..., min_length=64, max_length=64)
    cache_schema_version: str = Field(..., min_length=1)
    tool_versions: tuple[str, ...] = Field(default_factory=tuple)
    policy_assumptions: tuple[str, ...] = Field(default_factory=tuple)
    expected_artifacts: tuple[WorkflowArtifactKind, ...] = Field(default_factory=tuple)
    cache_path: str = Field(..., min_length=1)


class WorkflowCacheManifest(JsonModel):
    """Workflow-level cache contract over deterministic reusable surfaces."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    entries: tuple[WorkflowCacheEntry, ...] = Field(default_factory=tuple)


class WorkflowCacheMissExplanationEntry(JsonModel):
    """One explicit explanation for why a workflow cache entry was not reused."""

    model_config = ConfigDict(extra="forbid")

    surface: str = Field(..., min_length=1)
    expected_cache_key: str = Field(..., min_length=64, max_length=64)
    observed_cache_key: str | None = None
    reason: WorkflowCacheMissReason
    detail: str = Field(..., min_length=1)


class WorkflowCacheMissExplanationReport(JsonModel):
    """Workflow-level explanation of reusable-cache misses."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    reusable: bool
    entries: tuple[WorkflowCacheMissExplanationEntry, ...] = Field(
        default_factory=tuple
    )


class WorkflowCacheReuseDisposition(StrEnum):
    """Whether one cache-aware workflow step can be reused or must rerun."""

    REUSED = "reused"
    RERUN = "rerun"


class WorkflowCacheReuseDecision(JsonModel):
    """Reuse decision for one cache-aware workflow step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    surface: str = Field(..., min_length=1)
    disposition: WorkflowCacheReuseDisposition
    reasons: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowCacheReusePlan(JsonModel):
    """Deterministic rerun plan derived from cache keys and step dependencies."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    reused_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    rerun_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    decisions: tuple[WorkflowCacheReuseDecision, ...] = Field(default_factory=tuple)


class ArtifactRegistryEntry(JsonModel):
    """One expected workflow artifact with stable lineage."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    artifact_kind: WorkflowArtifactKind
    producer_step_id: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    upstream_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)


class ProteomicsArtifactRegistry(JsonModel):
    """Stable artifact registry for one workflow."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    artifacts: tuple[ArtifactRegistryEntry, ...] = Field(default_factory=tuple)


class ArtifactInventoryEntry(JsonModel):
    """One produced runtime artifact with run and step lineage."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    workflow_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    producer_step_id: str = Field(..., min_length=1)
    producer_step_kind: WorkflowStepKind
    artifact_kind: WorkflowArtifactKind
    relative_path: str = Field(..., min_length=1)
    absolute_path: str = Field(..., min_length=1)
    provenance_sha256: str = Field(..., min_length=64, max_length=64)
    layout_entry_id: str = Field(..., min_length=1)
    expected_document_kind: str | None = None
    upstream_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)


class ProteomicsArtifactInventory(JsonModel):
    """Stable artifact inventory for one workflow run."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    artifacts: tuple[ArtifactInventoryEntry, ...] = Field(default_factory=tuple)


class StreamingPolicyEntry(JsonModel):
    """Streaming guidance for one workflow input."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., min_length=1)
    role: WorkflowInputRole
    size_bytes: int = Field(..., ge=0)
    mode: WorkflowStreamingMode
    rationale: str = Field(..., min_length=1)


class LargeFileStreamingPolicy(JsonModel):
    """Workflow streaming policy derived from file size and format."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    threshold_bytes: int = Field(..., ge=1)
    entries: tuple[StreamingPolicyEntry, ...] = Field(default_factory=tuple)


class ParallelExecutionGroup(JsonModel):
    """One parallelizable stage in a workflow plan."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    step_ids: tuple[str, ...] = Field(default_factory=tuple)
    rationale: str = Field(..., min_length=1)


class ParallelExecutionPlan(JsonModel):
    """Grouped execution plan for deterministic parallel stages."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    groups: tuple[ParallelExecutionGroup, ...] = Field(default_factory=tuple)


class WorkflowCheckpointStep(JsonModel):
    """Checkpoint state for one workflow step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    status: WorkflowCheckpointStatus
    resume_kind: WorkflowResumeKind
    resume_rationale: str = Field(..., min_length=1)
    expected_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowCheckpoint(JsonModel):
    """Checkpoint payload for resuming a workflow after completed steps."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    completed_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    resumable_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    non_resumable_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    external_state_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    pending_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    blocked_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    artifact_registry_sha256: str = Field(..., min_length=64, max_length=64)
    cache_manifest_sha256: str = Field(..., min_length=64, max_length=64)
    steps: tuple[WorkflowCheckpointStep, ...] = Field(default_factory=tuple)


class ProteomicsWorkflowRuntimeBundle(JsonModel):
    """Aggregated operator-facing workflow planning bundle."""

    model_config = ConfigDict(extra="forbid")

    manifest: ProteomicsWorkflowManifest
    dag_plan: ProteomicsDagPlan
    deterministic_execution: DeterministicExecutionContract
    runtime_state: WorkflowRuntimeStateManifest
    run_directory_layout: WorkflowRunDirectoryLayout
    container_steps: tuple[ContainerizedStepSpec, ...] = Field(default_factory=tuple)
    search_contract: ExternalSearchToolContract
    hpc_job: HpcJobDescriptor
    cache_manifest: WorkflowCacheManifest
    artifact_registry: ProteomicsArtifactRegistry
    artifact_inventory: ProteomicsArtifactInventory
    streaming_policy: LargeFileStreamingPolicy
    parallel_plan: ParallelExecutionPlan
    checkpoint: WorkflowCheckpoint


class WorkflowRuntimeExportBundle(JsonModel):
    """Deterministic export bundle for local review and bug reproduction."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    export_bundle_sha256: str = Field(..., min_length=64, max_length=64)
    manifest: ProteomicsWorkflowManifest
    dag_plan: ProteomicsDagPlan
    deterministic_execution: DeterministicExecutionContract
    runtime_state: WorkflowRuntimeStateManifest
    run_directory_layout: WorkflowRunDirectoryLayout
    container_steps: tuple[ContainerizedStepSpec, ...] = Field(default_factory=tuple)
    search_contract: ExternalSearchToolContract
    hpc_job: HpcJobDescriptor
    cache_manifest: WorkflowCacheManifest
    artifact_registry: ProteomicsArtifactRegistry
    artifact_inventory: ProteomicsArtifactInventory
    streaming_policy: LargeFileStreamingPolicy
    parallel_plan: ParallelExecutionPlan
    checkpoint: WorkflowCheckpoint


class WorkflowRuntimeValidationIssue(JsonModel):
    """One integrity issue discovered while validating a runtime bundle."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(error|warning)$")
    message: str = Field(..., min_length=1)


class WorkflowRuntimeValidationReport(JsonModel):
    """Fast integrity report over a runtime bundle without executing the workflow."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    valid: bool
    checked_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    export_bundle_sha256: str = Field(..., min_length=64, max_length=64)
    issues: tuple[WorkflowRuntimeValidationIssue, ...] = Field(default_factory=tuple)


class WorkflowReplayProofEntry(JsonModel):
    """One governed surface compared across replay or rerun exports."""

    model_config = ConfigDict(extra="forbid")

    surface: str = Field(..., min_length=1)
    previous_sha256: str = Field(..., min_length=64, max_length=64)
    current_sha256: str = Field(..., min_length=64, max_length=64)
    changed: bool
    rationale: str = Field(..., min_length=1)


class WorkflowReplayComparisonReport(JsonModel):
    """Comparison report showing whether a replay or rerun changed workflow outputs."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    equivalent: bool
    previous_export_bundle_sha256: str = Field(..., min_length=64, max_length=64)
    current_export_bundle_sha256: str = Field(..., min_length=64, max_length=64)
    entries: tuple[WorkflowReplayProofEntry, ...] = Field(default_factory=tuple)


class WorkflowArchiveMedium(StrEnum):
    """Portable archival medium for offline review bundles."""

    PORTABLE_JSON = "portable_json"
    OFFLINE_REVIEW_DIRECTORY = "offline_review_directory"


class ArchivedArtifactDescriptor(JsonModel):
    """Portable artifact descriptor preserved inside an archival bundle."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    relative_path: str = Field(..., min_length=1)
    provenance_sha256: str = Field(..., min_length=64, max_length=64)
    expected_document_kind: str | None = None


class WorkflowRuntimeArchiveBundle(JsonModel):
    """Portable archival wrapper over one workflow runtime export bundle."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    archive_medium: WorkflowArchiveMedium
    export_bundle_sha256: str = Field(..., min_length=64, max_length=64)
    archive_bundle_sha256: str = Field(..., min_length=64, max_length=64)
    archived_artifacts: tuple[ArchivedArtifactDescriptor, ...] = Field(
        default_factory=tuple
    )
    export_bundle: WorkflowRuntimeExportBundle


class WorkflowRuntimeArchiveImportReport(JsonModel):
    """Import-time provenance report for a portable archival workflow bundle."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    archive_bundle_sha256: str = Field(..., min_length=64, max_length=64)
    imported_export_bundle_sha256: str = Field(..., min_length=64, max_length=64)
    preserved_artifact_count: int = Field(..., ge=0)
    preserved_provenance_fields: tuple[str, ...] = Field(default_factory=tuple)
    portable_review_ready: bool


class RerunComparisonScope(StrEnum):
    """Long-lived scope for comparing repeated workflow executions."""

    SAME_SAMPLE = "same_sample"
    SAME_STUDY = "same_study"


class RerunArtifactDriftEntry(JsonModel):
    """One archived artifact that drifted across repeated workflow executions."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    previous_relative_path: str = Field(..., min_length=1)
    current_relative_path: str = Field(..., min_length=1)
    previous_provenance_sha256: str = Field(..., min_length=64, max_length=64)
    current_provenance_sha256: str = Field(..., min_length=64, max_length=64)


class WorkflowRerunComparisonArtifact(JsonModel):
    """Portable comparison artifact for same-sample or same-study reruns."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    comparison_scope: RerunComparisonScope
    subject_id: str = Field(..., min_length=1)
    previous_archive_bundle_sha256: str = Field(..., min_length=64, max_length=64)
    current_archive_bundle_sha256: str = Field(..., min_length=64, max_length=64)
    replay_proof: WorkflowReplayComparisonReport
    changed_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    stable_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    drifted_artifacts: tuple[RerunArtifactDriftEntry, ...] = Field(
        default_factory=tuple
    )
    summary: str = Field(..., min_length=1)


def _build_document_schema(document_kind: str) -> DocumentSchema:
    return DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind=document_kind,
        package_name="bijux-proteomics-core",
        status="generated",
    )


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_sequence_sha256(values: tuple[str, ...]) -> str:
    return hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()


def _artifact_provenance_sha256(
    *,
    workflow_id: str,
    run_id: str,
    artifact_id: str,
    producer_step_id: str,
    artifact_kind: WorkflowArtifactKind,
    relative_path: str,
    expected_document_kind: str | None,
    upstream_artifact_ids: tuple[str, ...],
) -> str:
    return hashlib.sha256(
        "|".join(
            (
                workflow_id,
                run_id,
                artifact_id,
                producer_step_id,
                artifact_kind.value,
                relative_path,
                expected_document_kind or "",
                ",".join(upstream_artifact_ids),
            )
        ).encode("utf-8")
    ).hexdigest()


def _sanitize_identifier(value: str) -> str:
    return (
        "".join(character if character.isalnum() else "-" for character in value)
        .strip("-")
        .lower()
    )


_WORKFLOW_CACHE_SCHEMA_VERSION = "2.0.0"
_DEFAULT_FDR_Q_VALUE_THRESHOLD = 0.01


@dataclass(frozen=True)
class _WorkflowCacheSurfaceSpec:
    """One cache-aware workflow surface tied to a producer step."""

    surface: str
    producer_step_id: str
    source_roles: tuple[WorkflowInputRole, ...]
    expected_artifacts: tuple[WorkflowArtifactKind, ...]
    schema_refs: tuple[str, ...]
    parameter_assumptions: tuple[str, ...]
    policy_assumptions: tuple[str, ...]
    dependency_surfaces: tuple[str, ...] = ()


def _resolve_input_kind(path: Path, role: WorkflowInputRole) -> str:
    if role is WorkflowInputRole.FEATURES:
        return "ms1-features"
    detected = detect_proteomics_format(path)
    return detected.value


def _expected_artifact_document_kind(
    artifact_kind: WorkflowArtifactKind,
) -> str | None:
    mapping = {
        WorkflowArtifactKind.DIGEST_MANIFEST: "peptide_digest_manifest",
        WorkflowArtifactKind.RUN_BUNDLE: "normalized_run_bundle_manifest",
        WorkflowArtifactKind.CHECKPOINT: "workflow_checkpoint",
    }
    return mapping.get(artifact_kind)


def _artifact_relative_path(
    artifact_kind: WorkflowArtifactKind,
    workflow_id: str,
) -> str:
    mapping: dict[WorkflowArtifactKind, str] = {
        WorkflowArtifactKind.DIGEST_MANIFEST: "digest/manifest.json",
        WorkflowArtifactKind.DIGEST_EXPORT: "digest/peptides.jsonl",
        WorkflowArtifactKind.SEARCH_JOB: "search/submit.json",
        WorkflowArtifactKind.SEARCH_RESULTS: "search/results.tsv",
        WorkflowArtifactKind.NORMALIZED_IDENTIFICATIONS: "identifications.normalized.json",
        WorkflowArtifactKind.FDR_REPORT: "fdr.report.json",
        WorkflowArtifactKind.QUANT_REPORT: "quant.report.json",
        WorkflowArtifactKind.QC_REPORT: "qc.report.json",
        WorkflowArtifactKind.RUN_BUNDLE: "bundle/bundle.manifest.json",
        WorkflowArtifactKind.JOB_DESCRIPTOR: f"jobs/{workflow_id}.slurm",
        WorkflowArtifactKind.CHECKPOINT: f"checkpoints/{workflow_id}.json",
    }
    return mapping.get(artifact_kind, f"{artifact_kind.value}.json")


def _format_policy_float(value: float) -> str:
    return format(value, "g")


def _cache_schema_refs(
    artifacts: tuple[WorkflowArtifactKind, ...],
) -> tuple[str, ...]:
    return tuple(
        _expected_artifact_document_kind(artifact_kind) or artifact_kind.value
        for artifact_kind in artifacts
    )


def _artifact_path_for_kind(
    manifest: ProteomicsWorkflowManifest,
    artifact_kind: WorkflowArtifactKind,
) -> str:
    return str(
        Path(manifest.artifacts_dir)
        / _artifact_relative_path(artifact_kind, manifest.workflow_id)
    )


def _resolve_streaming_mode(
    path: Path, role: WorkflowInputRole, threshold_bytes: int
) -> WorkflowStreamingMode:
    if (
        role
        in {
            WorkflowInputRole.SPECTRA,
            WorkflowInputRole.IDENTIFICATIONS,
            WorkflowInputRole.FEATURES,
        }
        and path.stat().st_size >= threshold_bytes
    ):
        return WorkflowStreamingMode.STREAMING
    if path.suffix.lower() == ".mzml":
        return WorkflowStreamingMode.STREAMING
    return WorkflowStreamingMode.EAGER


def _input_asset(
    path: Path, role: WorkflowInputRole, threshold_bytes: int
) -> WorkflowInputAsset:
    return WorkflowInputAsset(
        role=role,
        path=str(path),
        input_kind=_resolve_input_kind(path, role),
        sha256=_hash_file(path),
        size_bytes=path.stat().st_size,
        streaming_mode=_resolve_streaming_mode(path, role, threshold_bytes),
    )


def _resolve_design_entry(
    design_path: Path | None,
    *,
    sample_id: str | None,
    spectra_path: Path,
) -> ExperimentalDesignEntry | None:
    if design_path is None:
        return None
    report = parse_experimental_design_table(design_path)
    accepted = tuple(report.accepted_entries)
    if sample_id is not None:
        for entry in accepted:
            if entry.sample_id == sample_id:
                return entry
    for entry in accepted:
        if Path(entry.spectra_file).name == spectra_path.name:
            return entry
    return accepted[0] if len(accepted) == 1 else None


def _build_runtime_policies(
    *,
    execution_mode: WorkflowExecutionMode,
    scheduler: WorkflowSchedulerKind,
    search_adapter_kind: SearchAdapterKind,
    default_container_image: str,
    streaming_threshold_bytes: int,
    fdr_q_value_threshold: float,
    has_features: bool,
    has_design: bool,
) -> tuple[str, ...]:
    return (
        "digest:protease=trypsin",
        "digest:digestion-mode=full",
        "digest:missed-cleavages=0",
        "digest:length-window=7-50",
        f"search:adapter={search_adapter_kind.value}",
        f"runtime:execution-mode={execution_mode.value}",
        f"runtime:scheduler={scheduler.value}",
        f"runtime:container-image={default_container_image}",
        f"runtime:streaming-threshold-bytes={streaming_threshold_bytes}",
        f"fdr:q-value-threshold={_format_policy_float(fdr_q_value_threshold)}",
        f"quant:features-enabled={'true' if has_features else 'false'}",
        f"design:table-attached={'true' if has_design else 'false'}",
    )


def _workflow_tool_versions(
    manifest: ProteomicsWorkflowManifest,
) -> tuple[str, ...]:
    return (
        f"bijux-proteomics-core@{manifest.document_schema.schema_version}",
        f"search-adapter:{manifest.search_adapter_kind.value}@builtin",
        f"runtime-image:{manifest.default_container_image}",
    )


def _cache_policy_assumptions(
    manifest: ProteomicsWorkflowManifest,
    surface: str,
) -> tuple[str, ...]:
    prefixes_by_surface = {
        "digestion": ("digest:", "runtime:"),
        "search-normalization": ("search:", "runtime:"),
        "fdr-score": ("runtime:",),
        "quant-parse": ("quant:", "design:", "runtime:"),
        "run-bundle": ("runtime:",),
    }
    prefixes = prefixes_by_surface.get(surface, ("runtime:",))
    return tuple(
        policy
        for policy in manifest.runtime_policies
        if any(policy.startswith(prefix) for prefix in prefixes)
    )


def _cache_parameter_assumptions(
    manifest: ProteomicsWorkflowManifest,
    surface: str,
) -> tuple[str, ...]:
    prefixes_by_surface = {
        "digestion": ("digest:",),
        "search-normalization": ("search:",),
        "fdr-score": ("fdr:",),
        "quant-parse": ("quant:", "design:"),
        "run-bundle": (),
    }
    prefixes = prefixes_by_surface.get(surface, ())
    return tuple(
        policy
        for policy in manifest.runtime_policies
        if any(policy.startswith(prefix) for prefix in prefixes)
    )


def _workflow_cache_surface_specs(
    manifest: ProteomicsWorkflowManifest,
) -> tuple[_WorkflowCacheSurfaceSpec, ...]:
    step_by_kind = {step.kind: step for step in manifest.steps}
    specs = [
        _WorkflowCacheSurfaceSpec(
            surface="digestion",
            producer_step_id=step_by_kind[WorkflowStepKind.DIGEST_DATABASE].step_id,
            source_roles=(WorkflowInputRole.PROTEINS,),
            expected_artifacts=(
                WorkflowArtifactKind.DIGEST_MANIFEST,
                WorkflowArtifactKind.DIGEST_EXPORT,
            ),
            schema_refs=_cache_schema_refs(
                (
                    WorkflowArtifactKind.DIGEST_MANIFEST,
                    WorkflowArtifactKind.DIGEST_EXPORT,
                )
            ),
            parameter_assumptions=_cache_parameter_assumptions(manifest, "digestion"),
            policy_assumptions=_cache_policy_assumptions(manifest, "digestion"),
        ),
        _WorkflowCacheSurfaceSpec(
            surface="search-normalization",
            producer_step_id=step_by_kind[
                WorkflowStepKind.NORMALIZE_IDENTIFICATIONS
            ].step_id,
            source_roles=(
                (WorkflowInputRole.IDENTIFICATIONS,)
                if any(
                    asset.role is WorkflowInputRole.IDENTIFICATIONS
                    for asset in manifest.input_assets
                )
                else (WorkflowInputRole.SPECTRA,)
            ),
            expected_artifacts=(WorkflowArtifactKind.NORMALIZED_IDENTIFICATIONS,),
            schema_refs=_cache_schema_refs(
                (WorkflowArtifactKind.NORMALIZED_IDENTIFICATIONS,)
            ),
            parameter_assumptions=_cache_parameter_assumptions(
                manifest, "search-normalization"
            ),
            policy_assumptions=_cache_policy_assumptions(
                manifest, "search-normalization"
            ),
        ),
        _WorkflowCacheSurfaceSpec(
            surface="fdr-score",
            producer_step_id=step_by_kind[WorkflowStepKind.CALCULATE_FDR].step_id,
            source_roles=(),
            expected_artifacts=(WorkflowArtifactKind.FDR_REPORT,),
            schema_refs=_cache_schema_refs((WorkflowArtifactKind.FDR_REPORT,)),
            parameter_assumptions=_cache_parameter_assumptions(manifest, "fdr-score"),
            policy_assumptions=_cache_policy_assumptions(manifest, "fdr-score"),
            dependency_surfaces=("search-normalization",),
        ),
    ]
    if any(asset.role is WorkflowInputRole.FEATURES for asset in manifest.input_assets):
        quant_roles: list[WorkflowInputRole] = [WorkflowInputRole.FEATURES]
        if any(asset.role is WorkflowInputRole.DESIGN for asset in manifest.input_assets):
            quant_roles.append(WorkflowInputRole.DESIGN)
        specs.append(
            _WorkflowCacheSurfaceSpec(
                surface="quant-parse",
                producer_step_id=step_by_kind[WorkflowStepKind.QUANTIFY_FEATURES].step_id,
                source_roles=tuple(quant_roles),
                expected_artifacts=(WorkflowArtifactKind.QUANT_REPORT,),
                schema_refs=_cache_schema_refs((WorkflowArtifactKind.QUANT_REPORT,)),
                parameter_assumptions=_cache_parameter_assumptions(
                    manifest, "quant-parse"
                ),
                policy_assumptions=_cache_policy_assumptions(manifest, "quant-parse"),
                dependency_surfaces=("search-normalization",),
            )
        )
    bundle_dependency_surfaces = ["search-normalization", "fdr-score"]
    if any(asset.role is WorkflowInputRole.FEATURES for asset in manifest.input_assets):
        bundle_dependency_surfaces.append("quant-parse")
    specs.append(
        _WorkflowCacheSurfaceSpec(
            surface="run-bundle",
            producer_step_id=step_by_kind[WorkflowStepKind.BUILD_RUN_BUNDLE].step_id,
            source_roles=(WorkflowInputRole.SPECTRA, WorkflowInputRole.PROTEINS),
            expected_artifacts=(WorkflowArtifactKind.RUN_BUNDLE,),
            schema_refs=_cache_schema_refs((WorkflowArtifactKind.RUN_BUNDLE,)),
            parameter_assumptions=_cache_parameter_assumptions(manifest, "run-bundle"),
            policy_assumptions=_cache_policy_assumptions(manifest, "run-bundle"),
            dependency_surfaces=tuple(bundle_dependency_surfaces),
        )
    )
    return tuple(specs)


def _build_step(
    step_id: str,
    kind: WorkflowStepKind,
    *,
    label: str,
    depends_on: tuple[str, ...] = (),
    consumes_roles: tuple[WorkflowInputRole, ...] = (),
    produces_artifacts: tuple[WorkflowArtifactKind, ...] = (),
    command_preview: tuple[str, ...] = (),
    cacheable: bool = False,
    blocking: bool = True,
) -> WorkflowExecutionStep:
    return WorkflowExecutionStep(
        step_id=step_id,
        kind=kind,
        label=label,
        depends_on=depends_on,
        consumes_roles=consumes_roles,
        produces_artifacts=produces_artifacts,
        command_preview=command_preview,
        cacheable=cacheable,
        blocking=blocking,
    )


def build_proteomics_workflow_manifest(
    *,
    proteins_path: Path,
    spectra_path: Path,
    identifications_path: Path | None = None,
    features_path: Path | None = None,
    design_path: Path | None = None,
    sample_id: str | None = None,
    search_adapter_kind: SearchAdapterKind = SearchAdapterKind.GENERIC,
    scheduler: WorkflowSchedulerKind = WorkflowSchedulerKind.SLURM,
    default_container_image: str = "ghcr.io/bijux/proteomics-runtime:stable",
    artifacts_dir: Path | None = None,
    streaming_threshold_bytes: int = 8 * 1024 * 1024,
    fdr_q_value_threshold: float = _DEFAULT_FDR_Q_VALUE_THRESHOLD,
) -> ProteomicsWorkflowManifest:
    """Build one workflow manifest over digest/search/FDR/quant/QC surfaces."""
    design_entry = _resolve_design_entry(
        design_path,
        sample_id=sample_id,
        spectra_path=spectra_path,
    )
    resolved_sample_id = sample_id or (design_entry.sample_id if design_entry else None)
    run_id = spectra_path.stem
    workflow_id = _sanitize_identifier(
        f"{resolved_sample_id or run_id}-{search_adapter_kind.value}-workflow"
    )
    output_root = artifacts_dir or Path("artifacts") / "workflows" / workflow_id
    adapter_manifest = get_search_adapter_manifest(search_adapter_kind)

    input_assets = [
        _input_asset(
            proteins_path, WorkflowInputRole.PROTEINS, streaming_threshold_bytes
        ),
        _input_asset(
            spectra_path, WorkflowInputRole.SPECTRA, streaming_threshold_bytes
        ),
    ]
    if identifications_path is not None:
        input_assets.append(
            _input_asset(
                identifications_path,
                WorkflowInputRole.IDENTIFICATIONS,
                streaming_threshold_bytes,
            )
        )
    if features_path is not None:
        input_assets.append(
            _input_asset(
                features_path, WorkflowInputRole.FEATURES, streaming_threshold_bytes
            )
        )
    if design_path is not None:
        input_assets.append(
            _input_asset(
                design_path, WorkflowInputRole.DESIGN, streaming_threshold_bytes
            )
        )

    validate_step_id = f"{workflow_id}-validate-inputs"
    digest_step_id = f"{workflow_id}-digest-database"
    search_step_id = f"{workflow_id}-run-search-engine"
    normalize_step_id = f"{workflow_id}-normalize-identifications"
    fdr_step_id = f"{workflow_id}-calculate-fdr"
    quantify_step_id = f"{workflow_id}-quantify-features"
    qc_step_id = f"{workflow_id}-run-qc"
    bundle_step_id = f"{workflow_id}-build-run-bundle"

    steps = [
        _build_step(
            validate_step_id,
            WorkflowStepKind.VALIDATE_INPUTS,
            label="validate workflow inputs and detect supported proteomics formats",
            consumes_roles=tuple(asset.role for asset in input_assets),
            produces_artifacts=(),
            command_preview=(
                "bijux-proteomics",
                "validate",
                str(spectra_path),
                "--kind",
                "auto",
            ),
            cacheable=False,
        ),
        _build_step(
            digest_step_id,
            WorkflowStepKind.DIGEST_DATABASE,
            label="digest the target-decoy protein database into reproducible peptide space",
            depends_on=(validate_step_id,),
            consumes_roles=(WorkflowInputRole.PROTEINS,),
            produces_artifacts=(
                WorkflowArtifactKind.DIGEST_MANIFEST,
                WorkflowArtifactKind.DIGEST_EXPORT,
            ),
            command_preview=(
                "bijux-proteomics",
                "digest",
                str(proteins_path),
                "--protease",
                "trypsin",
                "--out",
                str(output_root / "digest" / "peptides.jsonl"),
            ),
            cacheable=True,
        ),
    ]

    execution_mode = WorkflowExecutionMode.IMPORT_RESULTS
    if identifications_path is None:
        execution_mode = WorkflowExecutionMode.EXTERNAL_SEARCH
        steps.append(
            _build_step(
                search_step_id,
                WorkflowStepKind.RUN_SEARCH_ENGINE,
                label="submit the search engine against spectra and the digested database",
                depends_on=(validate_step_id, digest_step_id),
                consumes_roles=(WorkflowInputRole.SPECTRA, WorkflowInputRole.PROTEINS),
                produces_artifacts=(
                    WorkflowArtifactKind.SEARCH_JOB,
                    WorkflowArtifactKind.SEARCH_RESULTS,
                ),
                command_preview=(
                    "search-runner",
                    "submit",
                    "--adapter",
                    search_adapter_kind.value,
                    "--spectra",
                    str(spectra_path),
                    "--database",
                    str(output_root / "digest" / "peptides.jsonl"),
                ),
                cacheable=False,
            )
        )
    steps.append(
        _build_step(
            normalize_step_id,
            WorkflowStepKind.NORMALIZE_IDENTIFICATIONS,
            label="normalize search results into stable PSM contracts",
            depends_on=(
                (search_step_id,)
                if execution_mode is WorkflowExecutionMode.EXTERNAL_SEARCH
                else (validate_step_id,)
            ),
            consumes_roles=(
                (WorkflowInputRole.IDENTIFICATIONS,)
                if identifications_path is not None
                else (WorkflowInputRole.SPECTRA,)
            ),
            produces_artifacts=(WorkflowArtifactKind.NORMALIZED_IDENTIFICATIONS,),
            command_preview=(
                "bijux-proteomics",
                "search-adapter",
                "normalize",
                str(identifications_path or (output_root / "search" / "results.tsv")),
                "--adapter",
                search_adapter_kind.value,
            ),
            cacheable=True,
        )
    )
    steps.append(
        _build_step(
            fdr_step_id,
            WorkflowStepKind.CALCULATE_FDR,
            label="score normalized PSMs through target-decoy FDR and q-value assignment",
            depends_on=(normalize_step_id,),
            consumes_roles=(),
            produces_artifacts=(WorkflowArtifactKind.FDR_REPORT,),
            command_preview=(
                "bijux-proteomics",
                "fdr",
                str(output_root / "identifications.normalized.jsonl"),
                "--q-value-threshold",
                _format_policy_float(fdr_q_value_threshold),
                "--out",
                str(output_root / "fdr.report.json"),
            ),
            cacheable=True,
        )
    )
    if features_path is not None:
        steps.append(
            _build_step(
                quantify_step_id,
                WorkflowStepKind.QUANTIFY_FEATURES,
                label="roll MS1 features into normalized quantification tables",
                depends_on=(validate_step_id, normalize_step_id),
                consumes_roles=(WorkflowInputRole.FEATURES,),
                produces_artifacts=(WorkflowArtifactKind.QUANT_REPORT,),
                command_preview=(
                    "bijux-proteomics",
                    "quantify",
                    str(features_path),
                    "--design",
                    str(design_path) if design_path is not None else "design.tsv",
                    "--out",
                    str(output_root / "quant.report.json"),
                ),
                cacheable=True,
            )
        )
    steps.append(
        _build_step(
            qc_step_id,
            WorkflowStepKind.RUN_QC,
            label="build thresholded QC diagnostics over spectra, identifications, and FASTA context",
            depends_on=(normalize_step_id,),
            consumes_roles=(WorkflowInputRole.SPECTRA, WorkflowInputRole.PROTEINS),
            produces_artifacts=(WorkflowArtifactKind.QC_REPORT,),
            command_preview=(
                "bijux-proteomics",
                "qc",
                "report",
                str(spectra_path),
                str(identifications_path or (output_root / "search" / "results.tsv")),
                str(proteins_path),
                "--out",
                str(output_root / "qc.report.json"),
            ),
            cacheable=False,
        )
    )
    bundle_dependencies = [normalize_step_id, fdr_step_id, qc_step_id]
    if features_path is not None:
        bundle_dependencies.append(quantify_step_id)
    steps.append(
        _build_step(
            bundle_step_id,
            WorkflowStepKind.BUILD_RUN_BUNDLE,
            label="materialize a normalized run bundle for archival and downstream transport",
            depends_on=tuple(bundle_dependencies),
            consumes_roles=(WorkflowInputRole.SPECTRA,),
            produces_artifacts=(WorkflowArtifactKind.RUN_BUNDLE,),
            command_preview=(
                "bijux-proteomics",
                "bundle-run",
                "--spectra",
                str(spectra_path),
                "--identifications",
                str(identifications_path or (output_root / "search" / "results.tsv")),
                "--fdr-threshold",
                _format_policy_float(fdr_q_value_threshold),
                "--out-dir",
                str(output_root / "bundle"),
            ),
            cacheable=True,
        )
    )

    payload = ProteomicsWorkflowManifest(
        document_schema=_build_document_schema("proteomics_workflow_manifest"),
        workflow_id=workflow_id,
        workflow_name=f"proteomics workflow for {resolved_sample_id or run_id}",
        execution_mode=execution_mode,
        scheduler=scheduler,
        sample_id=resolved_sample_id,
        run_id=run_id,
        search_adapter_kind=search_adapter_kind,
        search_adapter_name=adapter_manifest.display_name,
        default_container_image=default_container_image,
        artifacts_dir=str(output_root),
        runtime_policies=_build_runtime_policies(
            execution_mode=execution_mode,
            scheduler=scheduler,
            search_adapter_kind=search_adapter_kind,
            default_container_image=default_container_image,
            streaming_threshold_bytes=streaming_threshold_bytes,
            fdr_q_value_threshold=fdr_q_value_threshold,
            has_features=features_path is not None,
            has_design=design_path is not None,
        ),
        input_assets=tuple(input_assets),
        steps=tuple(steps),
        checkpointable_steps=tuple(step.step_id for step in steps),
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_proteomics_dag_plan(
    manifest: ProteomicsWorkflowManifest,
) -> ProteomicsDagPlan:
    """Project a workflow manifest into a DAG-shaped execution plan."""
    nodes = tuple(
        WorkflowDagNode(
            node_id=step.step_id,
            label=step.label,
            step_kind=step.kind,
            depends_on=step.depends_on,
            artifact_kinds=step.produces_artifacts,
            command_preview=step.command_preview,
        )
        for step in manifest.steps
    )
    edges = tuple(
        WorkflowDagEdge(
            edge_id=f"{dependency}->{step.step_id}",
            source_node_id=dependency,
            target_node_id=step.step_id,
            reason="declared workflow dependency",
        )
        for step in manifest.steps
        for dependency in step.depends_on
    )
    payload = ProteomicsDagPlan(
        document_schema=_build_document_schema("proteomics_dag_plan"),
        workflow_id=manifest.workflow_id,
        nodes=nodes,
        edges=edges,
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_reproducible_workflow_blueprint(
    manifest: ProteomicsWorkflowManifest,
) -> ReproducibleWorkflowBlueprint:
    """Project a runtime manifest onto scientific workflow surfaces."""
    surface_by_kind = {
        WorkflowStepKind.VALIDATE_INPUTS: WorkflowScientificSurface.SEQUENCE_INTAKE,
        WorkflowStepKind.DIGEST_DATABASE: WorkflowScientificSurface.SEQUENCE_INTAKE,
        WorkflowStepKind.RUN_SEARCH_ENGINE: WorkflowScientificSurface.SEARCH_INGESTION,
        WorkflowStepKind.NORMALIZE_IDENTIFICATIONS: WorkflowScientificSurface.SEARCH_INGESTION,
        WorkflowStepKind.CALCULATE_FDR: WorkflowScientificSurface.CONFIDENCE_SCORING,
        WorkflowStepKind.QUANTIFY_FEATURES: WorkflowScientificSurface.QUANTIFICATION,
        WorkflowStepKind.RUN_QC: WorkflowScientificSurface.QUALITY_CONTROL,
        WorkflowStepKind.BUILD_RUN_BUNDLE: WorkflowScientificSurface.EVIDENCE_SYNTHESIS,
    }
    note_by_surface = {
        WorkflowScientificSurface.SEQUENCE_INTAKE: "sequence and raw-input intake stays explicit before search interpretation begins",
        WorkflowScientificSurface.SEARCH_INGESTION: "search evidence is normalized before any confidence interpretation is attached",
        WorkflowScientificSurface.CONFIDENCE_SCORING: "target-decoy confidence is separated from raw search ingestion",
        WorkflowScientificSurface.QUANTIFICATION: "quantification remains an explicit scientific surface instead of a runtime side effect",
        WorkflowScientificSurface.QUALITY_CONTROL: "quality control remains inspectable alongside identification and quant outputs",
        WorkflowScientificSurface.EVIDENCE_SYNTHESIS: "reviewable evidence artifacts are assembled only after scientific sub-results exist",
    }
    steps = tuple(
        WorkflowBlueprintStepMapping(
            step_id=step.step_id,
            step_kind=step.kind,
            scientific_surface=surface_by_kind[step.kind],
            required_input_roles=step.consumes_roles,
            produced_artifact_kinds=step.produces_artifacts,
            note=note_by_surface[surface_by_kind[step.kind]],
        )
        for step in manifest.steps
    )
    payload = ReproducibleWorkflowBlueprint(
        document_schema=_build_document_schema("reproducible_workflow_blueprint"),
        workflow_id=manifest.workflow_id,
        execution_mode=manifest.execution_mode,
        input_roles=tuple(asset.role for asset in manifest.input_assets),
        steps=steps,
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_workflow_manifest_explanation_report(
    manifest: ProteomicsWorkflowManifest,
) -> WorkflowManifestExplanationReport:
    """Explain the major manifest choices in plain durable runtime terms."""
    input_roles = ",".join(asset.role.value for asset in manifest.input_assets)
    entries = (
        WorkflowManifestExplanationEntry(
            category="execution_mode",
            selected_value=manifest.execution_mode.value,
            rationale=(
                "external search submission is required because no identification table was attached"
                if manifest.execution_mode is WorkflowExecutionMode.EXTERNAL_SEARCH
                else "existing identification results are imported and normalized instead of launching a search engine"
            ),
        ),
        WorkflowManifestExplanationEntry(
            category="search_adapter",
            selected_value=manifest.search_adapter_kind.value,
            rationale="the selected adapter defines how search evidence is normalized into stable PSM contracts",
        ),
        WorkflowManifestExplanationEntry(
            category="scheduler",
            selected_value=manifest.scheduler.value,
            rationale="the scheduler controls how runtime descriptors and job materialization are emitted",
        ),
        WorkflowManifestExplanationEntry(
            category="inputs",
            selected_value=input_roles,
            rationale="attached inputs determine which scientific surfaces the workflow can materialize",
        ),
        WorkflowManifestExplanationEntry(
            category="quantification",
            selected_value=(
                "enabled"
                if WorkflowInputRole.FEATURES
                in {asset.role for asset in manifest.input_assets}
                else "disabled"
            ),
            rationale=(
                "feature quantification is enabled because an MS1 feature table is available"
                if WorkflowInputRole.FEATURES
                in {asset.role for asset in manifest.input_assets}
                else "quantification is omitted because no feature table was attached"
            ),
        ),
    )
    payload = WorkflowManifestExplanationReport(
        document_schema=_build_document_schema("workflow_manifest_explanation_report"),
        workflow_id=manifest.workflow_id,
        entries=entries,
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_workflow_step_provenance_report(
    manifest: ProteomicsWorkflowManifest,
    *,
    checkpoint: WorkflowCheckpoint,
    replayed_step_ids: tuple[str, ...] = (),
) -> WorkflowStepProvenanceReport:
    """Build per-step provenance that remains valid across resume and replay."""
    checkpoint_by_id = {entry.step_id: entry for entry in checkpoint.steps}
    replayed = set(replayed_step_ids)
    entries = []
    for step in manifest.steps:
        checkpoint_entry = checkpoint_by_id[step.step_id]
        if step.step_id in replayed:
            replay_disposition = WorkflowStepReplayDisposition.REPLAYED
            note = "step is marked for replay even though checkpoint provenance is preserved"
        elif checkpoint_entry.status is WorkflowCheckpointStatus.COMPLETED:
            replay_disposition = WorkflowStepReplayDisposition.REUSED
            note = "completed step may be reused according to checkpoint provenance"
        else:
            replay_disposition = WorkflowStepReplayDisposition.PENDING
            note = "step has not yet been materialized and remains pending or blocked"
        entries.append(
            WorkflowStepProvenanceEntry(
                step_id=step.step_id,
                step_kind=step.kind,
                status=checkpoint_entry.status,
                resume_kind=checkpoint_entry.resume_kind,
                replay_disposition=replay_disposition,
                upstream_step_ids=step.depends_on,
                expected_artifact_ids=checkpoint_entry.expected_artifact_ids,
                note=note,
            )
        )
    payload = WorkflowStepProvenanceReport(
        document_schema=_build_document_schema("workflow_step_provenance_report"),
        workflow_id=manifest.workflow_id,
        entries=tuple(entries),
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_external_tool_capability_report(
    manifest: ProteomicsWorkflowManifest,
) -> ExternalToolCapabilityReport:
    """Check whether the selected external tool can support the planned workflow."""
    adapter_manifest = get_search_adapter_manifest(manifest.search_adapter_kind)
    issues: list[ExternalToolCapabilityIssue] = []
    if manifest.execution_mode is WorkflowExecutionMode.EXTERNAL_SEARCH:
        if not adapter_manifest.supports_external_execution:
            issues.append(
                ExternalToolCapabilityIssue(
                    code="adapter_not_launchable",
                    severity="error",
                    message="selected adapter cannot launch an external search and only supports result normalization",
                )
            )
        if not adapter_manifest.supports_protein_refs:
            issues.append(
                ExternalToolCapabilityIssue(
                    code="missing_protein_reference_support",
                    severity="error",
                    message="selected adapter cannot preserve protein references required by downstream FDR and evidence steps",
                )
            )
        if not adapter_manifest.supports_config_hash:
            issues.append(
                ExternalToolCapabilityIssue(
                    code="missing_config_hash_support",
                    severity="warning",
                    message="selected adapter cannot preserve a native configuration hash for heavy external execution provenance",
                )
            )
    payload = ExternalToolCapabilityReport(
        document_schema=_build_document_schema("external_tool_capability_report"),
        workflow_id=manifest.workflow_id,
        adapter_kind=manifest.search_adapter_kind,
        executable=not any(issue.severity == "error" for issue in issues),
        issues=tuple(issues),
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_workflow_execution_readiness_report(
    manifest: ProteomicsWorkflowManifest,
    *,
    hpc_job: HpcJobDescriptor,
    available_tool_versions: tuple[str, ...],
    available_schedulers: tuple[WorkflowSchedulerKind, ...] = (
        WorkflowSchedulerKind.LOCAL,
        WorkflowSchedulerKind.SLURM,
    ),
    max_cpus: int = 4,
    max_memory_gb: int = 16,
    max_walltime_minutes: int = 120,
) -> WorkflowExecutionReadinessReport:
    """Refuse execution when required tool versions or resource guarantees are absent."""
    issues: list[WorkflowExecutionReadinessIssue] = []
    capability_report = build_external_tool_capability_report(manifest)
    for issue in capability_report.issues:
        if issue.severity == "error":
            issues.append(
                WorkflowExecutionReadinessIssue(
                    code=issue.code,
                    severity=issue.severity,
                    message=issue.message,
                )
            )
    if manifest.scheduler not in available_schedulers:
        issues.append(
            WorkflowExecutionReadinessIssue(
                code="scheduler_unavailable",
                severity="error",
                message="required scheduler is not available for this workflow execution",
            )
        )
    required_tool_versions = set(_workflow_tool_versions(manifest))
    if not required_tool_versions.issubset(set(available_tool_versions)):
        issues.append(
            WorkflowExecutionReadinessIssue(
                code="tool_versions_unavailable",
                severity="error",
                message="required workflow tool versions are not all available in the execution environment",
            )
        )
    if (
        hpc_job.cpus > max_cpus
        or hpc_job.memory_gb > max_memory_gb
        or hpc_job.walltime_minutes > max_walltime_minutes
    ):
        issues.append(
            WorkflowExecutionReadinessIssue(
                code="resource_guarantee_missing",
                severity="error",
                message="available runtime resource guarantees are below the workflow descriptor requirements",
            )
        )
    payload = WorkflowExecutionReadinessReport(
        document_schema=_build_document_schema("workflow_execution_readiness_report"),
        workflow_id=manifest.workflow_id,
        ready=not any(issue.severity == "error" for issue in issues),
        issues=tuple(issues),
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_workflow_diff_report(
    left: ProteomicsWorkflowManifest,
    right: ProteomicsWorkflowManifest,
) -> WorkflowDiffReport:
    """Compare two workflow manifests scientifically and operationally."""
    left_assets = {asset.role: asset for asset in left.input_assets}
    right_assets = {asset.role: asset for asset in right.input_assets}
    entries: list[WorkflowDiffEntry] = []
    for role in sorted(
        set(left_assets) | set(right_assets), key=lambda item: item.value
    ):
        left_asset = left_assets.get(role)
        right_asset = right_assets.get(role)
        left_hash = left_asset.sha256 if left_asset is not None else None
        right_hash = right_asset.sha256 if right_asset is not None else None
        if left_hash != right_hash:
            entries.append(
                WorkflowDiffEntry(
                    field_name=f"input:{role.value}",
                    category=WorkflowDiffCategory.SCIENTIFIC,
                    left_value=left_hash,
                    right_value=right_hash,
                    note="scientific input content changed for this workflow role",
                )
            )
    comparisons = (
        (
            "execution_mode",
            WorkflowDiffCategory.SCIENTIFIC,
            left.execution_mode.value,
            right.execution_mode.value,
            "workflow changed between imported results and external execution semantics",
        ),
        (
            "search_adapter_kind",
            WorkflowDiffCategory.SCIENTIFIC,
            left.search_adapter_kind.value,
            right.search_adapter_kind.value,
            "search interpretation surface changed across workflow manifests",
        ),
        (
            "runtime_policies",
            WorkflowDiffCategory.SCIENTIFIC,
            "|".join(left.runtime_policies),
            "|".join(right.runtime_policies),
            "scientific or runtime policy assumptions changed",
        ),
        (
            "scheduler",
            WorkflowDiffCategory.OPERATIONAL,
            left.scheduler.value,
            right.scheduler.value,
            "scheduler configuration changed",
        ),
        (
            "container_image",
            WorkflowDiffCategory.OPERATIONAL,
            left.default_container_image,
            right.default_container_image,
            "container runtime assumption changed",
        ),
        (
            "artifacts_dir",
            WorkflowDiffCategory.OPERATIONAL,
            left.artifacts_dir,
            right.artifacts_dir,
            "artifact materialization path changed",
        ),
        (
            "step_ids",
            WorkflowDiffCategory.OPERATIONAL,
            "|".join(step.step_id for step in left.steps),
            "|".join(step.step_id for step in right.steps),
            "workflow step graph changed",
        ),
    )
    for field_name, category, left_value, right_value, note in comparisons:
        if left_value != right_value:
            entries.append(
                WorkflowDiffEntry(
                    field_name=field_name,
                    category=category,
                    left_value=left_value,
                    right_value=right_value,
                    note=note,
                )
            )
    payload = WorkflowDiffReport(
        document_schema=_build_document_schema("workflow_diff_report"),
        left_workflow_id=left.workflow_id,
        right_workflow_id=right.workflow_id,
        entries=tuple(entries),
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_proteomics_workflow_template(
    template_kind: WorkflowTemplateKind,
    *,
    scheduler: WorkflowSchedulerKind = WorkflowSchedulerKind.SLURM,
    default_container_image: str = "ghcr.io/bijux/proteomics-runtime:stable",
) -> ProteomicsWorkflowTemplate:
    """Build one reusable workflow template over real proteomics surfaces."""
    if template_kind is WorkflowTemplateKind.IMPORTED_LFQ_REVIEW:
        return ProteomicsWorkflowTemplate(
            template_kind=template_kind,
            template_id="imported-lfq-review",
            display_name="Imported LFQ review workflow",
            execution_mode=WorkflowExecutionMode.IMPORT_RESULTS,
            required_input_roles=(
                WorkflowInputRole.PROTEINS,
                WorkflowInputRole.SPECTRA,
                WorkflowInputRole.IDENTIFICATIONS,
                WorkflowInputRole.FEATURES,
                WorkflowInputRole.DESIGN,
            ),
            optional_input_roles=(),
            recommended_adapter_kind=SearchAdapterKind.GENERIC,
            recommended_scheduler=scheduler,
            default_container_image=default_container_image,
            step_kinds=(
                WorkflowStepKind.VALIDATE_INPUTS,
                WorkflowStepKind.DIGEST_DATABASE,
                WorkflowStepKind.NORMALIZE_IDENTIFICATIONS,
                WorkflowStepKind.CALCULATE_FDR,
                WorkflowStepKind.QUANTIFY_FEATURES,
                WorkflowStepKind.RUN_QC,
                WorkflowStepKind.BUILD_RUN_BUNDLE,
            ),
            note="reuse normalized search results and build quant, QC, and evidence outputs around them",
        )
    return ProteomicsWorkflowTemplate(
        template_kind=template_kind,
        template_id="external-search-lfq-review",
        display_name="External search LFQ review workflow",
        execution_mode=WorkflowExecutionMode.EXTERNAL_SEARCH,
        required_input_roles=(
            WorkflowInputRole.PROTEINS,
            WorkflowInputRole.SPECTRA,
            WorkflowInputRole.FEATURES,
            WorkflowInputRole.DESIGN,
        ),
        optional_input_roles=(WorkflowInputRole.IDENTIFICATIONS,),
        recommended_adapter_kind=SearchAdapterKind.SAGE,
        recommended_scheduler=scheduler,
        default_container_image=default_container_image,
        step_kinds=(
            WorkflowStepKind.VALIDATE_INPUTS,
            WorkflowStepKind.DIGEST_DATABASE,
            WorkflowStepKind.RUN_SEARCH_ENGINE,
            WorkflowStepKind.NORMALIZE_IDENTIFICATIONS,
            WorkflowStepKind.CALCULATE_FDR,
            WorkflowStepKind.QUANTIFY_FEATURES,
            WorkflowStepKind.RUN_QC,
            WorkflowStepKind.BUILD_RUN_BUNDLE,
        ),
        note="launch an external search, then continue through FDR, quantification, QC, and evidence bundling",
    )


def instantiate_proteomics_workflow_template(
    template: ProteomicsWorkflowTemplate,
    *,
    proteins_path: Path,
    spectra_path: Path,
    identifications_path: Path | None = None,
    features_path: Path | None = None,
    design_path: Path | None = None,
    sample_id: str | None = None,
    artifacts_dir: Path | None = None,
    fdr_q_value_threshold: float = _DEFAULT_FDR_Q_VALUE_THRESHOLD,
) -> ProteomicsWorkflowManifest:
    """Instantiate a reusable workflow template into a concrete workflow manifest."""
    attached_roles = {
        WorkflowInputRole.PROTEINS,
        WorkflowInputRole.SPECTRA,
    }
    if identifications_path is not None:
        attached_roles.add(WorkflowInputRole.IDENTIFICATIONS)
    if features_path is not None:
        attached_roles.add(WorkflowInputRole.FEATURES)
    if design_path is not None:
        attached_roles.add(WorkflowInputRole.DESIGN)
    missing_roles = [
        role.value
        for role in template.required_input_roles
        if role not in attached_roles
    ]
    if missing_roles:
        raise ValueError(
            "workflow template is missing required inputs: "
            + ", ".join(sorted(missing_roles))
        )
    return build_proteomics_workflow_manifest(
        proteins_path=proteins_path,
        spectra_path=spectra_path,
        identifications_path=identifications_path,
        features_path=features_path,
        design_path=design_path,
        sample_id=sample_id,
        search_adapter_kind=template.recommended_adapter_kind,
        scheduler=template.recommended_scheduler,
        default_container_image=template.default_container_image,
        artifacts_dir=artifacts_dir,
        fdr_q_value_threshold=fdr_q_value_threshold,
    )


def build_deterministic_execution_contract(
    manifest: ProteomicsWorkflowManifest,
    *,
    container_steps: tuple[ContainerizedStepSpec, ...],
    parallel_plan: ParallelExecutionPlan,
    hpc_job: HpcJobDescriptor,
) -> DeterministicExecutionContract:
    """Bind one workflow manifest to a deterministic runtime execution fingerprint."""
    manifest_sha256 = _stable_model_sha256(manifest)
    input_fingerprint = hashlib.sha256(
        "|".join(
            f"{asset.role.value}:{asset.sha256}" for asset in manifest.input_assets
        ).encode("utf-8")
    ).hexdigest()
    policy_fingerprint = hashlib.sha256(
        "|".join(manifest.runtime_policies).encode("utf-8")
    ).hexdigest()
    container_steps_sha256 = _stable_sequence_sha256(
        tuple(_stable_model_sha256(step) for step in container_steps)
    )
    execution_fingerprint = hashlib.sha256(
        "|".join(
            (
                manifest_sha256,
                input_fingerprint,
                policy_fingerprint,
                container_steps_sha256,
                _stable_model_sha256(parallel_plan),
                _stable_model_sha256(hpc_job),
            )
        ).encode("utf-8")
    ).hexdigest()
    payload = DeterministicExecutionContract(
        document_schema=_build_document_schema("deterministic_execution_contract"),
        workflow_id=manifest.workflow_id,
        manifest_sha256=manifest_sha256,
        input_fingerprint=input_fingerprint,
        policy_fingerprint=policy_fingerprint,
        ordered_step_ids=tuple(step.step_id for step in manifest.steps),
        parallel_group_ids=tuple(group.group_id for group in parallel_plan.groups),
        container_steps_sha256=container_steps_sha256,
        hpc_job_sha256=_stable_model_sha256(hpc_job),
        execution_fingerprint=execution_fingerprint,
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_workflow_runtime_state_manifest(
    manifest: ProteomicsWorkflowManifest,
    *,
    deterministic_execution: DeterministicExecutionContract,
    artifact_registry: ProteomicsArtifactRegistry,
) -> WorkflowRuntimeStateManifest:
    """Connect expected core result surfaces to runtime state materializations."""
    result_bindings = tuple(
        CoreResultRuntimeBinding(
            artifact_id=artifact.artifact_id,
            artifact_kind=artifact.artifact_kind,
            producer_step_id=artifact.producer_step_id,
            runtime_surface=Path(artifact.path).parent.name or "artifacts",
            runtime_path=artifact.path,
            expected_document_kind=_expected_artifact_document_kind(
                artifact.artifact_kind
            ),
        )
        for artifact in artifact_registry.artifacts
    )
    payload = WorkflowRuntimeStateManifest(
        document_schema=_build_document_schema("workflow_runtime_state_manifest"),
        workflow_id=manifest.workflow_id,
        run_id=manifest.run_id,
        manifest_sha256=_stable_model_sha256(manifest),
        deterministic_execution_sha256=_stable_model_sha256(deterministic_execution),
        checkpointable_step_ids=manifest.checkpointable_steps,
        result_bindings=result_bindings,
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_workflow_run_directory_layout(
    manifest: ProteomicsWorkflowManifest,
) -> WorkflowRunDirectoryLayout:
    """Declare the predictable run-directory tree for one workflow."""
    entries = [
        WorkflowRunDirectoryLayoutEntry(
            entry_id=f"{manifest.workflow_id}:cache-dir",
            path_kind=WorkflowPathKind.DIRECTORY,
            relative_path="cache",
            description="cache entries for reusable runtime surfaces",
            required=False,
        ),
        WorkflowRunDirectoryLayoutEntry(
            entry_id=f"{manifest.workflow_id}:checkpoints-dir",
            path_kind=WorkflowPathKind.DIRECTORY,
            relative_path="checkpoints",
            description="checkpoint documents for resumable runtime state",
            required=False,
        ),
        WorkflowRunDirectoryLayoutEntry(
            entry_id=f"{manifest.workflow_id}:jobs-dir",
            path_kind=WorkflowPathKind.DIRECTORY,
            relative_path="jobs",
            description="scheduler scripts and submission descriptors",
            required=False,
        ),
        WorkflowRunDirectoryLayoutEntry(
            entry_id=f"{manifest.workflow_id}:digest-dir",
            path_kind=WorkflowPathKind.DIRECTORY,
            relative_path="digest",
            description="digest outputs and policy manifests",
            producer_step_id=f"{manifest.workflow_id}-digest-database",
        ),
        WorkflowRunDirectoryLayoutEntry(
            entry_id=f"{manifest.workflow_id}:search-dir",
            path_kind=WorkflowPathKind.DIRECTORY,
            relative_path="search",
            description="external search submissions and collected results",
            producer_step_id=f"{manifest.workflow_id}-run-search-engine",
            required=manifest.execution_mode is WorkflowExecutionMode.EXTERNAL_SEARCH,
        ),
        WorkflowRunDirectoryLayoutEntry(
            entry_id=f"{manifest.workflow_id}:bundle-dir",
            path_kind=WorkflowPathKind.DIRECTORY,
            relative_path="bundle",
            description="normalized bundle exports for review and transport",
            producer_step_id=f"{manifest.workflow_id}-build-run-bundle",
        ),
    ]
    for step in manifest.steps:
        for artifact_kind in step.produces_artifacts:
            entries.append(
                WorkflowRunDirectoryLayoutEntry(
                    entry_id=f"{manifest.workflow_id}:{artifact_kind.value}",
                    path_kind=WorkflowPathKind.FILE,
                    relative_path=_artifact_relative_path(
                        artifact_kind, manifest.workflow_id
                    ),
                    description=f"materialized {artifact_kind.value} output",
                    producer_step_id=step.step_id,
                    expected_artifact_kinds=(artifact_kind,),
                )
            )
    payload = WorkflowRunDirectoryLayout(
        document_schema=_build_document_schema("workflow_run_directory_layout"),
        workflow_id=manifest.workflow_id,
        root_dir=manifest.artifacts_dir,
        entries=tuple(entries),
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_containerized_step_specs(
    manifest: ProteomicsWorkflowManifest,
) -> tuple[ContainerizedStepSpec, ...]:
    """Build container execution specs for each workflow step."""
    manifest_sha256 = _stable_model_sha256(manifest)
    mounts = tuple(
        WorkflowContainerMount(
            source_path=asset.path,
            target_path=f"/workspace/inputs/{Path(asset.path).name}",
            read_only=True,
        )
        for asset in manifest.input_assets
    ) + (
        WorkflowContainerMount(
            source_path=manifest.artifacts_dir,
            target_path="/workspace/artifacts",
            read_only=False,
        ),
    )
    container_steps = []
    for step in manifest.steps:
        command_sha256 = _stable_sequence_sha256(step.command_preview)
        descriptor_sha256 = hashlib.sha256(
            "|".join(
                (
                    step.step_id,
                    step.kind.value,
                    manifest.default_container_image,
                    manifest_sha256,
                    command_sha256,
                    _stable_sequence_sha256(
                        tuple(
                            f"{mount.source_path}->{mount.target_path}:{mount.read_only}"
                            for mount in mounts
                        )
                    ),
                    "isolated",
                    "/workspace",
                )
            ).encode("utf-8")
        ).hexdigest()
        container_steps.append(
            ContainerizedStepSpec(
                step_id=step.step_id,
                step_kind=step.kind,
                image=manifest.default_container_image,
                manifest_sha256=manifest_sha256,
                command_sha256=command_sha256,
                descriptor_sha256=descriptor_sha256,
                command=step.command_preview,
                mounts=mounts,
                network_policy="isolated",
                workdir="/workspace",
            )
        )
    return tuple(container_steps)


def build_external_search_tool_contract(
    manifest: ProteomicsWorkflowManifest,
) -> ExternalSearchToolContract:
    """Build a submit/wait/collect contract for the workflow search surface."""
    submit_step_id = next(
        (
            step.step_id
            for step in manifest.steps
            if step.kind is WorkflowStepKind.RUN_SEARCH_ENGINE
        ),
        f"{manifest.workflow_id}-run-search-engine",
    )
    collect_step_id = next(
        step.step_id
        for step in manifest.steps
        if step.kind is WorkflowStepKind.NORMALIZE_IDENTIFICATIONS
    )
    contract = ExternalSearchToolContract(
        document_schema=_build_document_schema("external_search_tool_contract"),
        workflow_id=manifest.workflow_id,
        adapter_kind=manifest.search_adapter_kind,
        tool_name=manifest.search_adapter_name,
        submit_step_id=submit_step_id,
        collect_step_id=collect_step_id,
        submit_command=(
            "search-runner",
            "submit",
            "--workflow-id",
            manifest.workflow_id,
            "--adapter",
            manifest.search_adapter_kind.value,
            "--artifacts-dir",
            manifest.artifacts_dir,
        ),
        wait_command=(
            "search-runner",
            "wait",
            "--workflow-id",
            manifest.workflow_id,
        ),
        collect_command=(
            "search-runner",
            "collect",
            "--workflow-id",
            manifest.workflow_id,
            "--out",
            f"{manifest.artifacts_dir}/search/results.tsv",
        ),
        expected_outputs=(
            WorkflowArtifactKind.SEARCH_JOB,
            WorkflowArtifactKind.SEARCH_RESULTS,
            WorkflowArtifactKind.NORMALIZED_IDENTIFICATIONS,
        ),
    )
    return contract.model_copy(
        update={
            "document_schema": contract.document_schema.with_content_hash(
                contract.to_dict()
            )
        }
    )


def build_workflow_runtime_cache(
    manifest: ProteomicsWorkflowManifest,
    *,
    cache_schema_version: str = _WORKFLOW_CACHE_SCHEMA_VERSION,
) -> WorkflowCacheManifest:
    """Build deterministic cache keys for reusable workflow surfaces."""
    asset_by_role = {asset.role: asset for asset in manifest.input_assets}
    entries_by_surface: dict[str, WorkflowCacheEntry] = {}
    entries: list[WorkflowCacheEntry] = []
    for spec in _workflow_cache_surface_specs(manifest):
        source_hashes = tuple(asset_by_role[role].sha256 for role in spec.source_roles)
        scientific_inputs_sha256 = _stable_sequence_sha256(source_hashes)
        schema_sha256 = _stable_sequence_sha256(spec.schema_refs)
        parameter_sha256 = _stable_sequence_sha256(spec.parameter_assumptions)
        dependency_cache_keys = tuple(
            entries_by_surface[surface].cache_key for surface in spec.dependency_surfaces
        )
        dependency_sha256 = _stable_sequence_sha256(dependency_cache_keys)
        tool_versions = _workflow_tool_versions(manifest)
        policy_assumptions = spec.policy_assumptions
        cache_key = hashlib.sha256(
            "|".join(
                (
                    manifest.workflow_id,
                    spec.surface,
                    cache_schema_version,
                    scientific_inputs_sha256,
                    schema_sha256,
                    parameter_sha256,
                    dependency_sha256,
                    *tool_versions,
                    *policy_assumptions,
                )
            ).encode("utf-8")
        ).hexdigest()
        entry = WorkflowCacheEntry(
            cache_key=cache_key,
            surface=spec.surface,
            producer_step_id=spec.producer_step_id,
            source_roles=spec.source_roles,
            source_hashes=source_hashes,
            scientific_inputs_sha256=scientific_inputs_sha256,
            schema_refs=spec.schema_refs,
            schema_sha256=schema_sha256,
            parameter_assumptions=spec.parameter_assumptions,
            parameter_sha256=parameter_sha256,
            dependency_surfaces=spec.dependency_surfaces,
            dependency_cache_keys=dependency_cache_keys,
            dependency_sha256=dependency_sha256,
            cache_schema_version=cache_schema_version,
            tool_versions=tool_versions,
            policy_assumptions=policy_assumptions,
            expected_artifacts=spec.expected_artifacts,
            cache_path=f"{manifest.artifacts_dir}/cache/{spec.surface}-{cache_key[:12]}.json",
        )
        entries.append(entry)
        entries_by_surface[spec.surface] = entry
    payload = WorkflowCacheManifest(
        document_schema=_build_document_schema("workflow_cache_manifest"),
        workflow_id=manifest.workflow_id,
        entries=tuple(entries),
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_workflow_cache_miss_explanation_report(
    expected: WorkflowCacheManifest,
    observed: WorkflowCacheManifest | None,
) -> WorkflowCacheMissExplanationReport:
    """Explain why an observed cache manifest could or could not be reused."""
    observed_by_surface = (
        {entry.surface: entry for entry in observed.entries}
        if observed is not None
        else {}
    )
    entries: list[WorkflowCacheMissExplanationEntry] = []
    for expected_entry in expected.entries:
        observed_entry = observed_by_surface.get(expected_entry.surface)
        if observed_entry is None:
            entries.append(
                WorkflowCacheMissExplanationEntry(
                    surface=expected_entry.surface,
                    expected_cache_key=expected_entry.cache_key,
                    reason=WorkflowCacheMissReason.ENTRY_MISSING,
                    detail="no observed cache entry exists for this reusable surface",
                )
            )
            continue
        if (
            observed_entry.scientific_inputs_sha256
            != expected_entry.scientific_inputs_sha256
        ):
            reason = WorkflowCacheMissReason.SCIENTIFIC_INPUTS_CHANGED
            detail = (
                "scientifically relevant input hashes changed for this cache surface"
            )
        elif observed_entry.parameter_sha256 != expected_entry.parameter_sha256:
            reason = WorkflowCacheMissReason.PARAMETERS_CHANGED
            detail = (
                "semantic workflow parameters changed for this reusable cache surface"
            )
        elif observed_entry.tool_versions != expected_entry.tool_versions:
            reason = WorkflowCacheMissReason.TOOLCHAIN_CHANGED
            detail = (
                "recorded runtime toolchain identifiers changed for this cache surface"
            )
        elif (
            observed_entry.cache_schema_version != expected_entry.cache_schema_version
            or observed_entry.schema_sha256 != expected_entry.schema_sha256
        ):
            reason = WorkflowCacheMissReason.SCHEMA_CHANGED
            detail = "cache schema or governed output schema changed for this reusable surface"
        elif observed_entry.dependency_sha256 != expected_entry.dependency_sha256:
            reason = WorkflowCacheMissReason.DEPENDENCY_CHANGED
            detail = (
                "an upstream cache surface changed, so this dependent reusable surface must rerun"
            )
        elif observed_entry.policy_assumptions != expected_entry.policy_assumptions:
            reason = WorkflowCacheMissReason.POLICY_CHANGED
            detail = (
                "recorded runtime policy assumptions changed for this cache surface"
            )
        elif observed_entry.cache_path != expected_entry.cache_path:
            reason = WorkflowCacheMissReason.CACHE_LAYOUT_CHANGED
            detail = "the cache path changed even though the surface name matched"
        else:
            continue
        entries.append(
            WorkflowCacheMissExplanationEntry(
                surface=expected_entry.surface,
                expected_cache_key=expected_entry.cache_key,
                observed_cache_key=observed_entry.cache_key,
                reason=reason,
                detail=detail,
            )
        )
    payload = WorkflowCacheMissExplanationReport(
        document_schema=_build_document_schema(
            "workflow_cache_miss_explanation_report"
        ),
        workflow_id=expected.workflow_id,
        reusable=not entries,
        entries=tuple(entries),
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_workflow_cache_reuse_plan(
    manifest: ProteomicsWorkflowManifest,
    *,
    expected: WorkflowCacheManifest,
    observed: WorkflowCacheManifest | None,
) -> WorkflowCacheReusePlan:
    """Plan which cache-aware workflow steps can be reused safely."""
    miss_report = build_workflow_cache_miss_explanation_report(expected, observed)
    miss_by_surface = {entry.surface: entry for entry in miss_report.entries}
    surface_by_step_id = {
        spec.producer_step_id: spec.surface for spec in _workflow_cache_surface_specs(manifest)
    }
    cacheable_steps = tuple(step for step in manifest.steps if step.cacheable)

    reused_step_ids: list[str] = []
    rerun_step_ids: list[str] = []
    decisions: list[WorkflowCacheReuseDecision] = []

    for step in cacheable_steps:
        surface = surface_by_step_id[step.step_id]
        reasons: list[str] = []
        miss_entry = miss_by_surface.get(surface)
        if miss_entry is not None:
            reasons.append(miss_entry.reason.value)
        if miss_entry is None:
            for dependency_step_id in step.depends_on:
                dependency_surface = surface_by_step_id.get(dependency_step_id)
                if dependency_surface is None:
                    continue
                if dependency_step_id in rerun_step_ids:
                    reasons.append(f"upstream:{dependency_surface}")
        if reasons:
            rerun_step_ids.append(step.step_id)
            decisions.append(
                WorkflowCacheReuseDecision(
                    step_id=step.step_id,
                    surface=surface,
                    disposition=WorkflowCacheReuseDisposition.RERUN,
                    reasons=tuple(dict.fromkeys(reasons)),
                )
            )
            continue
        reused_step_ids.append(step.step_id)
        decisions.append(
            WorkflowCacheReuseDecision(
                step_id=step.step_id,
                surface=surface,
                disposition=WorkflowCacheReuseDisposition.REUSED,
                reasons=(),
            )
        )

    return WorkflowCacheReusePlan(
        workflow_id=manifest.workflow_id,
        reused_step_ids=tuple(reused_step_ids),
        rerun_step_ids=tuple(rerun_step_ids),
        decisions=tuple(decisions),
    )


def build_proteomics_artifact_registry(
    manifest: ProteomicsWorkflowManifest,
) -> ProteomicsArtifactRegistry:
    """Build one stable artifact registry over expected workflow outputs."""
    artifacts = []
    step_outputs: dict[str, tuple[str, ...]] = {}
    for step in manifest.steps:
        upstream_artifact_ids = tuple(
            artifact_id
            for dependency in step.depends_on
            for artifact_id in step_outputs.get(dependency, ())
        )
        produced_ids = []
        for artifact_kind in step.produces_artifacts:
            artifact_id = f"{manifest.workflow_id}:{artifact_kind.value}"
            produced_ids.append(artifact_id)
            artifacts.append(
                ArtifactRegistryEntry(
                    artifact_id=artifact_id,
                    artifact_kind=artifact_kind,
                    producer_step_id=step.step_id,
                    path=_artifact_path_for_kind(manifest, artifact_kind),
                    upstream_artifact_ids=upstream_artifact_ids,
                )
            )
        step_outputs[step.step_id] = tuple(produced_ids)
    payload = ProteomicsArtifactRegistry(
        document_schema=_build_document_schema("proteomics_artifact_registry"),
        workflow_id=manifest.workflow_id,
        artifacts=tuple(artifacts),
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_proteomics_artifact_inventory(
    manifest: ProteomicsWorkflowManifest,
    *,
    artifact_registry: ProteomicsArtifactRegistry,
    run_directory_layout: WorkflowRunDirectoryLayout,
) -> ProteomicsArtifactInventory:
    """Bind every produced runtime artifact to one run and one logical step."""
    step_kind_by_id = {step.step_id: step.kind for step in manifest.steps}
    layout_entry_by_path = {
        entry.relative_path: entry
        for entry in run_directory_layout.entries
        if entry.path_kind is WorkflowPathKind.FILE
    }
    artifacts = []
    for artifact in artifact_registry.artifacts:
        relative_path = str(Path(artifact.path).relative_to(manifest.artifacts_dir))
        expected_document_kind = _expected_artifact_document_kind(
            artifact.artifact_kind
        )
        artifacts.append(
            ArtifactInventoryEntry(
                artifact_id=artifact.artifact_id,
                workflow_id=manifest.workflow_id,
                run_id=manifest.run_id,
                producer_step_id=artifact.producer_step_id,
                producer_step_kind=step_kind_by_id[artifact.producer_step_id],
                artifact_kind=artifact.artifact_kind,
                relative_path=relative_path,
                absolute_path=artifact.path,
                provenance_sha256=_artifact_provenance_sha256(
                    workflow_id=manifest.workflow_id,
                    run_id=manifest.run_id,
                    artifact_id=artifact.artifact_id,
                    producer_step_id=artifact.producer_step_id,
                    artifact_kind=artifact.artifact_kind,
                    relative_path=relative_path,
                    expected_document_kind=expected_document_kind,
                    upstream_artifact_ids=artifact.upstream_artifact_ids,
                ),
                layout_entry_id=layout_entry_by_path[relative_path].entry_id,
                expected_document_kind=expected_document_kind,
                upstream_artifact_ids=artifact.upstream_artifact_ids,
            )
        )
    payload = ProteomicsArtifactInventory(
        document_schema=_build_document_schema("proteomics_artifact_inventory"),
        workflow_id=manifest.workflow_id,
        run_id=manifest.run_id,
        artifacts=tuple(artifacts),
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_large_file_streaming_policy(
    manifest: ProteomicsWorkflowManifest,
    *,
    threshold_bytes: int = 8 * 1024 * 1024,
) -> LargeFileStreamingPolicy:
    """Build a large-file policy that makes streaming explicit."""
    entries = []
    for asset in manifest.input_assets:
        mode = (
            WorkflowStreamingMode.STREAMING
            if asset.streaming_mode is WorkflowStreamingMode.STREAMING
            or asset.size_bytes >= threshold_bytes
            else WorkflowStreamingMode.EAGER
        )
        rationale = (
            "stream because file exceeds the eager threshold or benefits from incremental parsing"
            if mode is WorkflowStreamingMode.STREAMING
            else "load eagerly because the input is compact"
        )
        entries.append(
            StreamingPolicyEntry(
                path=asset.path,
                role=asset.role,
                size_bytes=asset.size_bytes,
                mode=mode,
                rationale=rationale,
            )
        )
    payload = LargeFileStreamingPolicy(
        document_schema=_build_document_schema("large_file_streaming_policy"),
        workflow_id=manifest.workflow_id,
        threshold_bytes=threshold_bytes,
        entries=tuple(entries),
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_parallel_execution_plan(
    manifest: ProteomicsWorkflowManifest,
) -> ParallelExecutionPlan:
    """Group workflow steps into deterministic parallel stages."""
    levels: dict[str, int] = {}
    step_by_id = {step.step_id: step for step in manifest.steps}
    unresolved = set(step_by_id)
    while unresolved:
        progressed = False
        for step_id in tuple(unresolved):
            step = step_by_id[step_id]
            if all(dependency in levels for dependency in step.depends_on):
                levels[step_id] = (
                    0
                    if not step.depends_on
                    else max(levels[dependency] for dependency in step.depends_on) + 1
                )
                unresolved.remove(step_id)
                progressed = True
        if not progressed:
            raise ValueError(
                "workflow steps contain a cycle and cannot be parallelized deterministically"
            )
    grouped: dict[int, list[str]] = {}
    for step_id, level in levels.items():
        grouped.setdefault(level, []).append(step_id)
    groups = tuple(
        ParallelExecutionGroup(
            group_id=f"{manifest.workflow_id}-parallel-{level}",
            step_ids=tuple(sorted(step_ids)),
            rationale="steps in this group only depend on completed earlier groups",
        )
        for level, step_ids in sorted(grouped.items())
    )
    payload = ParallelExecutionPlan(
        document_schema=_build_document_schema("parallel_execution_plan"),
        workflow_id=manifest.workflow_id,
        groups=groups,
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_hpc_job_descriptor(
    manifest: ProteomicsWorkflowManifest,
    *,
    scheduler: WorkflowSchedulerKind | None = None,
    queue_name: str = "proteomics",
    resource_class: str = "standard",
) -> HpcJobDescriptor:
    """Export one scheduler-ready descriptor for the workflow bundle."""
    resolved_scheduler = scheduler or manifest.scheduler
    manifest_sha256 = _stable_model_sha256(manifest)
    script_path = f"{manifest.artifacts_dir}/jobs/{manifest.workflow_id}.{resolved_scheduler.value}"
    expected_artifact_paths = tuple(
        _artifact_path_for_kind(manifest, artifact_kind)
        for step in manifest.steps
        for artifact_kind in step.produces_artifacts
    )
    environment_assumptions = (
        f"scheduler:{resolved_scheduler.value}",
        f"container-image:{manifest.default_container_image}",
        f"artifacts-dir:{manifest.artifacts_dir}",
        "filesystem:shared-access-required",
    )
    lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
    if resolved_scheduler is WorkflowSchedulerKind.SLURM:
        lines.extend(
            [
                f"#SBATCH --job-name={manifest.workflow_id}",
                f"#SBATCH --partition={queue_name}",
                "#SBATCH --cpus-per-task=4",
                "#SBATCH --mem=16G",
                "#SBATCH --time=02:00:00",
            ]
        )
    lines.extend(
        [
            f"mkdir -p {manifest.artifacts_dir}",
            f"echo planning workflow {manifest.workflow_id}",
        ]
    )
    for step in manifest.steps:
        if step.command_preview:
            lines.append(" ".join(step.command_preview))
    script_text = "\n".join(lines) + "\n"
    ordered_step_ids = tuple(step.step_id for step in manifest.steps)
    descriptor_sha256 = hashlib.sha256(
        "|".join(
            (
                manifest.workflow_id,
                resolved_scheduler.value,
                manifest_sha256,
                queue_name,
                resource_class,
                manifest.default_container_image,
                *ordered_step_ids,
                script_path,
                script_text,
            )
        ).encode("utf-8")
    ).hexdigest()
    payload = HpcJobDescriptor(
        document_schema=_build_document_schema("hpc_job_descriptor"),
        scheduler=resolved_scheduler,
        workflow_id=manifest.workflow_id,
        job_name=manifest.workflow_id,
        manifest_sha256=manifest_sha256,
        ordered_step_ids=ordered_step_ids,
        descriptor_sha256=descriptor_sha256,
        cpus=4,
        memory_gb=16,
        walltime_minutes=120,
        queue_name=queue_name,
        resource_class=resource_class,
        container_image=manifest.default_container_image,
        working_directory=manifest.artifacts_dir,
        script_path=script_path,
        script_text=script_text,
        expected_artifact_paths=expected_artifact_paths,
        environment_assumptions=environment_assumptions,
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_workflow_checkpoint(
    manifest: ProteomicsWorkflowManifest,
    *,
    artifact_registry: ProteomicsArtifactRegistry,
    cache_manifest: WorkflowCacheManifest,
    completed_step_ids: tuple[str, ...] = (),
) -> WorkflowCheckpoint:
    """Build a resumable checkpoint for one workflow manifest."""
    completed = set(completed_step_ids)
    step_outputs = {
        step.step_id: tuple(
            artifact.artifact_id
            for artifact in artifact_registry.artifacts
            if artifact.producer_step_id == step.step_id
        )
        for step in manifest.steps
    }
    steps: list[WorkflowCheckpointStep] = []
    resumable_step_ids: list[str] = []
    non_resumable_step_ids: list[str] = []
    external_state_step_ids: list[str] = []
    pending_step_ids: list[str] = []
    blocked_step_ids: list[str] = []
    for step in manifest.steps:
        if step.step_id in completed:
            status = WorkflowCheckpointStatus.COMPLETED
        elif all(dependency in completed for dependency in step.depends_on):
            status = WorkflowCheckpointStatus.READY
            pending_step_ids.append(step.step_id)
        elif any(dependency not in completed for dependency in step.depends_on):
            status = WorkflowCheckpointStatus.BLOCKED
            blocked_step_ids.append(step.step_id)
        else:
            status = WorkflowCheckpointStatus.PENDING
            pending_step_ids.append(step.step_id)
        if step.kind is WorkflowStepKind.RUN_SEARCH_ENGINE:
            resume_kind = WorkflowResumeKind.EXTERNAL_STATE
            resume_rationale = "search submission depends on external runtime state and must be reconciled explicitly"
            external_state_step_ids.append(step.step_id)
        elif step.cacheable:
            resume_kind = WorkflowResumeKind.RESUMABLE
            resume_rationale = "step outputs are deterministic and may be resumed from verified artifacts"
            resumable_step_ids.append(step.step_id)
        else:
            resume_kind = WorkflowResumeKind.NON_RESUMABLE
            resume_rationale = "step should be replayed instead of skipped because it is not marked cacheable"
            non_resumable_step_ids.append(step.step_id)
        steps.append(
            WorkflowCheckpointStep(
                step_id=step.step_id,
                status=status,
                resume_kind=resume_kind,
                resume_rationale=resume_rationale,
                expected_artifact_ids=step_outputs.get(step.step_id, ()),
            )
        )
    payload = WorkflowCheckpoint(
        document_schema=_build_document_schema("workflow_checkpoint"),
        workflow_id=manifest.workflow_id,
        completed_step_ids=tuple(
            step_id for step_id in manifest.checkpointable_steps if step_id in completed
        ),
        resumable_step_ids=tuple(resumable_step_ids),
        non_resumable_step_ids=tuple(non_resumable_step_ids),
        external_state_step_ids=tuple(external_state_step_ids),
        pending_step_ids=tuple(pending_step_ids),
        blocked_step_ids=tuple(blocked_step_ids),
        artifact_registry_sha256=_stable_model_sha256(artifact_registry),
        cache_manifest_sha256=_stable_model_sha256(cache_manifest),
        steps=tuple(steps),
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_proteomics_workflow_runtime_bundle(
    *,
    proteins_path: Path,
    spectra_path: Path,
    identifications_path: Path | None = None,
    features_path: Path | None = None,
    design_path: Path | None = None,
    sample_id: str | None = None,
    search_adapter_kind: SearchAdapterKind = SearchAdapterKind.GENERIC,
    scheduler: WorkflowSchedulerKind = WorkflowSchedulerKind.SLURM,
    default_container_image: str = "ghcr.io/bijux/proteomics-runtime:stable",
    artifacts_dir: Path | None = None,
    completed_step_ids: tuple[str, ...] = (),
    fdr_q_value_threshold: float = _DEFAULT_FDR_Q_VALUE_THRESHOLD,
) -> ProteomicsWorkflowRuntimeBundle:
    """Build the complete planning bundle for a proteomics workflow."""
    manifest = build_proteomics_workflow_manifest(
        proteins_path=proteins_path,
        spectra_path=spectra_path,
        identifications_path=identifications_path,
        features_path=features_path,
        design_path=design_path,
        sample_id=sample_id,
        search_adapter_kind=search_adapter_kind,
        scheduler=scheduler,
        default_container_image=default_container_image,
        artifacts_dir=artifacts_dir,
        fdr_q_value_threshold=fdr_q_value_threshold,
    )
    dag_plan = build_proteomics_dag_plan(manifest)
    container_steps = build_containerized_step_specs(manifest)
    search_contract = build_external_search_tool_contract(manifest)
    cache_manifest = build_workflow_runtime_cache(manifest)
    artifact_registry = build_proteomics_artifact_registry(manifest)
    streaming_policy = build_large_file_streaming_policy(manifest)
    parallel_plan = build_parallel_execution_plan(manifest)
    hpc_job = build_hpc_job_descriptor(manifest, scheduler=scheduler)
    deterministic_execution = build_deterministic_execution_contract(
        manifest,
        container_steps=container_steps,
        parallel_plan=parallel_plan,
        hpc_job=hpc_job,
    )
    runtime_state = build_workflow_runtime_state_manifest(
        manifest,
        deterministic_execution=deterministic_execution,
        artifact_registry=artifact_registry,
    )
    run_directory_layout = build_workflow_run_directory_layout(manifest)
    artifact_inventory = build_proteomics_artifact_inventory(
        manifest,
        artifact_registry=artifact_registry,
        run_directory_layout=run_directory_layout,
    )
    checkpoint = build_workflow_checkpoint(
        manifest,
        artifact_registry=artifact_registry,
        cache_manifest=cache_manifest,
        completed_step_ids=completed_step_ids,
    )
    return ProteomicsWorkflowRuntimeBundle(
        manifest=manifest,
        dag_plan=dag_plan,
        deterministic_execution=deterministic_execution,
        runtime_state=runtime_state,
        run_directory_layout=run_directory_layout,
        container_steps=container_steps,
        search_contract=search_contract,
        hpc_job=hpc_job,
        cache_manifest=cache_manifest,
        artifact_registry=artifact_registry,
        artifact_inventory=artifact_inventory,
        streaming_policy=streaming_policy,
        parallel_plan=parallel_plan,
        checkpoint=checkpoint,
    )


def build_workflow_runtime_export_bundle(
    runtime_bundle: ProteomicsWorkflowRuntimeBundle,
) -> WorkflowRuntimeExportBundle:
    """Assemble a deterministic runtime export bundle for review and reproduction."""
    payload = WorkflowRuntimeExportBundle(
        document_schema=_build_document_schema("workflow_runtime_export_bundle"),
        workflow_id=runtime_bundle.manifest.workflow_id,
        export_bundle_sha256="0" * 64,
        manifest=runtime_bundle.manifest,
        dag_plan=runtime_bundle.dag_plan,
        deterministic_execution=runtime_bundle.deterministic_execution,
        runtime_state=runtime_bundle.runtime_state,
        run_directory_layout=runtime_bundle.run_directory_layout,
        container_steps=runtime_bundle.container_steps,
        search_contract=runtime_bundle.search_contract,
        hpc_job=runtime_bundle.hpc_job,
        cache_manifest=runtime_bundle.cache_manifest,
        artifact_registry=runtime_bundle.artifact_registry,
        artifact_inventory=runtime_bundle.artifact_inventory,
        streaming_policy=runtime_bundle.streaming_policy,
        parallel_plan=runtime_bundle.parallel_plan,
        checkpoint=runtime_bundle.checkpoint,
    )
    payload = payload.model_copy(
        update={"export_bundle_sha256": _workflow_runtime_export_bundle_hash(payload)}
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_workflow_runtime_validation_report(
    runtime_bundle: ProteomicsWorkflowRuntimeBundle,
) -> WorkflowRuntimeValidationReport:
    """Validate runtime manifest, artifact, checkpoint, and cache integrity."""
    issues: list[WorkflowRuntimeValidationIssue] = []
    artifacts_root = Path(runtime_bundle.manifest.artifacts_dir)
    export_bundle = build_workflow_runtime_export_bundle(runtime_bundle)

    if runtime_bundle.deterministic_execution.manifest_sha256 != _stable_model_sha256(
        runtime_bundle.manifest
    ):
        issues.append(
            WorkflowRuntimeValidationIssue(
                code="deterministic_manifest_mismatch",
                severity="error",
                message="deterministic execution contract no longer matches the workflow manifest",
            )
        )
    if runtime_bundle.runtime_state.manifest_sha256 != _stable_model_sha256(
        runtime_bundle.manifest
    ):
        issues.append(
            WorkflowRuntimeValidationIssue(
                code="runtime_state_manifest_mismatch",
                severity="error",
                message="runtime state manifest no longer matches the workflow manifest",
            )
        )
    if (
        runtime_bundle.runtime_state.deterministic_execution_sha256
        != _stable_model_sha256(runtime_bundle.deterministic_execution)
    ):
        issues.append(
            WorkflowRuntimeValidationIssue(
                code="runtime_state_execution_mismatch",
                severity="error",
                message="runtime state manifest no longer matches the deterministic execution contract",
            )
        )

    registry_by_id = {
        artifact.artifact_id: artifact
        for artifact in runtime_bundle.artifact_registry.artifacts
    }
    layout_paths = {
        entry.relative_path
        for entry in runtime_bundle.run_directory_layout.entries
        if entry.path_kind is WorkflowPathKind.FILE
    }
    for artifact in runtime_bundle.artifact_inventory.artifacts:
        if artifact.artifact_id not in registry_by_id:
            issues.append(
                WorkflowRuntimeValidationIssue(
                    code="artifact_inventory_registry_mismatch",
                    severity="error",
                    message=f"artifact inventory entry {artifact.artifact_id} is missing from the artifact registry",
                )
            )
        if artifact.relative_path not in layout_paths:
            issues.append(
                WorkflowRuntimeValidationIssue(
                    code="artifact_inventory_layout_mismatch",
                    severity="error",
                    message=f"artifact inventory path {artifact.relative_path} is missing from the run-directory layout",
                )
            )
        if artifacts_root not in Path(artifact.absolute_path).parents:
            issues.append(
                WorkflowRuntimeValidationIssue(
                    code="artifact_inventory_path_outside_root",
                    severity="error",
                    message=f"artifact {artifact.artifact_id} does not live under the declared artifacts root",
                )
            )

    cache_root = artifacts_root / "cache"
    for entry in runtime_bundle.cache_manifest.entries:
        cache_path = Path(entry.cache_path)
        if cache_root not in cache_path.parents:
            issues.append(
                WorkflowRuntimeValidationIssue(
                    code="cache_path_outside_root",
                    severity="error",
                    message=f"cache entry {entry.surface} does not live under the declared cache directory",
                )
            )
        if len(entry.cache_key) != 64:
            issues.append(
                WorkflowRuntimeValidationIssue(
                    code="cache_key_invalid_length",
                    severity="error",
                    message=f"cache entry {entry.surface} does not carry a stable sha256 cache key",
                )
            )

    if runtime_bundle.checkpoint.artifact_registry_sha256 != _stable_model_sha256(
        runtime_bundle.artifact_registry
    ):
        issues.append(
            WorkflowRuntimeValidationIssue(
                code="checkpoint_registry_hash_mismatch",
                severity="error",
                message="checkpoint artifact-registry hash no longer matches the registry payload",
            )
        )
    if runtime_bundle.checkpoint.cache_manifest_sha256 != _stable_model_sha256(
        runtime_bundle.cache_manifest
    ):
        issues.append(
            WorkflowRuntimeValidationIssue(
                code="checkpoint_cache_hash_mismatch",
                severity="error",
                message="checkpoint cache-manifest hash no longer matches the cache payload",
            )
        )
    checkpoint_step_ids = {step.step_id for step in runtime_bundle.checkpoint.steps}
    manifest_step_ids = {step.step_id for step in runtime_bundle.manifest.steps}
    if checkpoint_step_ids != manifest_step_ids:
        issues.append(
            WorkflowRuntimeValidationIssue(
                code="checkpoint_step_coverage_mismatch",
                severity="error",
                message="checkpoint step coverage no longer matches the workflow manifest",
            )
        )

    payload = WorkflowRuntimeValidationReport(
        document_schema=_build_document_schema("workflow_runtime_validation_report"),
        workflow_id=runtime_bundle.manifest.workflow_id,
        valid=not issues,
        checked_surfaces=(
            "manifest",
            "deterministic-execution",
            "runtime-state",
            "run-directory-layout",
            "cache-manifest",
            "artifact-registry",
            "artifact-inventory",
            "checkpoint",
            "export-bundle",
        ),
        export_bundle_sha256=export_bundle.export_bundle_sha256,
        issues=tuple(issues),
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_workflow_replay_proof_report(
    previous_export: WorkflowRuntimeExportBundle,
    current_export: WorkflowRuntimeExportBundle,
) -> WorkflowReplayComparisonReport:
    """Compare two workflow exports and explain whether rerun surfaces changed."""
    if previous_export.workflow_id != current_export.workflow_id:
        raise ValueError("workflow exports must share a workflow_id")
    comparisons = (
        (
            "manifest",
            _stable_model_sha256(previous_export.manifest),
            _stable_model_sha256(current_export.manifest),
            "workflow scientific and operational plan",
        ),
        (
            "deterministic_execution",
            _stable_model_sha256(previous_export.deterministic_execution),
            _stable_model_sha256(current_export.deterministic_execution),
            "deterministic execution assumptions",
        ),
        (
            "runtime_state",
            _stable_model_sha256(previous_export.runtime_state),
            _stable_model_sha256(current_export.runtime_state),
            "runtime lifecycle and result bindings",
        ),
        (
            "artifact_inventory",
            _stable_model_sha256(previous_export.artifact_inventory),
            _stable_model_sha256(current_export.artifact_inventory),
            "exported artifact file inventory",
        ),
        (
            "checkpoint",
            _stable_model_sha256(previous_export.checkpoint),
            _stable_model_sha256(current_export.checkpoint),
            "checkpoint and replay posture",
        ),
    )
    entries = tuple(
        WorkflowReplayProofEntry(
            surface=surface,
            previous_sha256=previous_sha256,
            current_sha256=current_sha256,
            changed=previous_sha256 != current_sha256,
            rationale=(
                f"{description} changed between replayed exports"
                if previous_sha256 != current_sha256
                else f"{description} remained stable across replayed exports"
            ),
        )
        for surface, previous_sha256, current_sha256, description in comparisons
    )
    payload = WorkflowReplayComparisonReport(
        document_schema=_build_document_schema("workflow_replay_proof_report"),
        workflow_id=previous_export.workflow_id,
        equivalent=not any(entry.changed for entry in entries),
        previous_export_bundle_sha256=previous_export.export_bundle_sha256,
        current_export_bundle_sha256=current_export.export_bundle_sha256,
        entries=entries,
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_workflow_runtime_archive_bundle(
    export_bundle: WorkflowRuntimeExportBundle,
    *,
    archive_medium: WorkflowArchiveMedium = WorkflowArchiveMedium.PORTABLE_JSON,
) -> WorkflowRuntimeArchiveBundle:
    """Wrap one runtime export bundle for offline review and long-lived archival."""
    archived_artifacts = tuple(
        ArchivedArtifactDescriptor(
            artifact_id=artifact.artifact_id,
            relative_path=artifact.relative_path,
            provenance_sha256=artifact.provenance_sha256,
            expected_document_kind=artifact.expected_document_kind,
        )
        for artifact in export_bundle.artifact_inventory.artifacts
    )
    payload = WorkflowRuntimeArchiveBundle(
        document_schema=_build_document_schema("workflow_runtime_archive_bundle"),
        workflow_id=export_bundle.workflow_id,
        run_id=export_bundle.artifact_inventory.run_id,
        archive_medium=archive_medium,
        export_bundle_sha256=export_bundle.export_bundle_sha256,
        archive_bundle_sha256="0" * 64,
        archived_artifacts=archived_artifacts,
        export_bundle=export_bundle,
    )
    payload = payload.model_copy(
        update={"archive_bundle_sha256": _workflow_runtime_archive_bundle_hash(payload)}
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def import_workflow_runtime_archive_bundle(
    payload: dict[str, object],
) -> tuple[WorkflowRuntimeExportBundle, WorkflowRuntimeArchiveImportReport]:
    """Validate and restore one portable archival workflow export bundle."""
    archive_bundle = WorkflowRuntimeArchiveBundle.from_dict(payload)
    expected_export_sha256 = _workflow_runtime_export_bundle_hash(
        archive_bundle.export_bundle
    )
    if archive_bundle.export_bundle.export_bundle_sha256 != expected_export_sha256:
        raise ValueError(
            "archived workflow export bundle sha256 does not match content"
        )
    if archive_bundle.export_bundle_sha256 != expected_export_sha256:
        raise ValueError("archive bundle export sha256 does not match archived export")

    archived_artifacts_by_id = {
        artifact.artifact_id: artifact for artifact in archive_bundle.archived_artifacts
    }
    for artifact in archive_bundle.export_bundle.artifact_inventory.artifacts:
        archived = archived_artifacts_by_id.get(artifact.artifact_id)
        if archived is None:
            raise ValueError(
                f"archived artifact descriptor missing for {artifact.artifact_id}"
            )
        if (
            archived.relative_path != artifact.relative_path
            or archived.provenance_sha256 != artifact.provenance_sha256
        ):
            raise ValueError(
                f"archived artifact descriptor drifted for {artifact.artifact_id}"
            )

    expected_archive_sha256 = _workflow_runtime_archive_bundle_hash(archive_bundle)
    if archive_bundle.archive_bundle_sha256 != expected_archive_sha256:
        raise ValueError("archive bundle sha256 does not match archival content")

    report = WorkflowRuntimeArchiveImportReport(
        document_schema=_build_document_schema(
            "workflow_runtime_archive_import_report"
        ),
        workflow_id=archive_bundle.workflow_id,
        run_id=archive_bundle.run_id,
        archive_bundle_sha256=archive_bundle.archive_bundle_sha256,
        imported_export_bundle_sha256=archive_bundle.export_bundle_sha256,
        preserved_artifact_count=len(archive_bundle.archived_artifacts),
        preserved_provenance_fields=(
            "workflow_id",
            "run_id",
            "export_bundle_sha256",
            "artifact_id",
            "relative_path",
            "provenance_sha256",
            "expected_document_kind",
        ),
        portable_review_ready=bool(archive_bundle.archived_artifacts),
    )
    report = report.model_copy(
        update={
            "document_schema": report.document_schema.with_content_hash(
                report.to_dict()
            )
        }
    )
    return archive_bundle.export_bundle, report


def build_workflow_rerun_comparison_artifact(
    previous_archive: WorkflowRuntimeArchiveBundle,
    current_archive: WorkflowRuntimeArchiveBundle,
    *,
    comparison_scope: RerunComparisonScope,
    subject_id: str,
) -> WorkflowRerunComparisonArtifact:
    """Build a portable comparison artifact for repeated workflow executions."""
    if previous_archive.workflow_id != current_archive.workflow_id:
        raise ValueError("rerun comparison requires matching workflow_id values")

    replay_proof = build_workflow_replay_proof_report(
        previous_archive.export_bundle,
        current_archive.export_bundle,
    )
    previous_artifacts = {
        artifact.artifact_id: artifact
        for artifact in previous_archive.archived_artifacts
    }
    current_artifacts = {
        artifact.artifact_id: artifact
        for artifact in current_archive.archived_artifacts
    }
    drifted_artifacts = tuple(
        RerunArtifactDriftEntry(
            artifact_id=artifact_id,
            previous_relative_path=previous_artifacts[artifact_id].relative_path,
            current_relative_path=current_artifacts[artifact_id].relative_path,
            previous_provenance_sha256=previous_artifacts[
                artifact_id
            ].provenance_sha256,
            current_provenance_sha256=current_artifacts[artifact_id].provenance_sha256,
        )
        for artifact_id in sorted(previous_artifacts)
        if artifact_id in current_artifacts
        and (
            previous_artifacts[artifact_id].provenance_sha256
            != current_artifacts[artifact_id].provenance_sha256
            or previous_artifacts[artifact_id].relative_path
            != current_artifacts[artifact_id].relative_path
        )
    )
    changed_surfaces = tuple(
        entry.surface for entry in replay_proof.entries if entry.changed
    )
    stable_surfaces = tuple(
        entry.surface for entry in replay_proof.entries if not entry.changed
    )
    payload = WorkflowRerunComparisonArtifact(
        document_schema=_build_document_schema("workflow_rerun_comparison_artifact"),
        workflow_id=previous_archive.workflow_id,
        comparison_scope=comparison_scope,
        subject_id=subject_id,
        previous_archive_bundle_sha256=previous_archive.archive_bundle_sha256,
        current_archive_bundle_sha256=current_archive.archive_bundle_sha256,
        replay_proof=replay_proof,
        changed_surfaces=changed_surfaces,
        stable_surfaces=stable_surfaces,
        drifted_artifacts=drifted_artifacts,
        summary=(
            f"{comparison_scope.value} rerun changed {len(changed_surfaces)} governed surfaces "
            f"and {len(drifted_artifacts)} archived artifacts"
        ),
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def _workflow_runtime_export_bundle_hash(
    export_bundle: WorkflowRuntimeExportBundle,
) -> str:
    return hashlib.sha256(
        "|".join(
            (
                _stable_model_sha256(export_bundle.manifest),
                _stable_model_sha256(export_bundle.dag_plan),
                _stable_model_sha256(export_bundle.deterministic_execution),
                _stable_model_sha256(export_bundle.runtime_state),
                _stable_model_sha256(export_bundle.run_directory_layout),
                _stable_sequence_sha256(
                    tuple(
                        _stable_model_sha256(step)
                        for step in export_bundle.container_steps
                    )
                ),
                _stable_model_sha256(export_bundle.search_contract),
                _stable_model_sha256(export_bundle.hpc_job),
                _stable_model_sha256(export_bundle.cache_manifest),
                _stable_model_sha256(export_bundle.artifact_registry),
                _stable_model_sha256(export_bundle.artifact_inventory),
                _stable_model_sha256(export_bundle.streaming_policy),
                _stable_model_sha256(export_bundle.parallel_plan),
                _stable_model_sha256(export_bundle.checkpoint),
            )
        ).encode("utf-8")
    ).hexdigest()


def _workflow_runtime_archive_bundle_hash(
    archive_bundle: WorkflowRuntimeArchiveBundle,
) -> str:
    return hashlib.sha256(
        "|".join(
            (
                archive_bundle.workflow_id,
                archive_bundle.run_id,
                archive_bundle.archive_medium.value,
                archive_bundle.export_bundle_sha256,
                _stable_sequence_sha256(
                    tuple(
                        ":".join(
                            (
                                artifact.artifact_id,
                                artifact.relative_path,
                                artifact.provenance_sha256,
                                artifact.expected_document_kind or "",
                            )
                        )
                        for artifact in archive_bundle.archived_artifacts
                    )
                ),
            )
        ).encode("utf-8")
    ).hexdigest()
