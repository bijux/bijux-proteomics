# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Workflow-runtime planning contracts for proteomics operator flows."""

from __future__ import annotations

from enum import StrEnum
import hashlib
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.formats import (
    ExperimentalDesignEntry,
    detect_proteomics_format,
    parse_experimental_design_table,
)
from bijux_proteomics.qc import _stable_sha256 as _stable_model_sha256
from bijux_proteomics.search_adapters import (
    SearchAdapterKind,
    get_search_adapter_manifest,
)
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


class ContainerMount(JsonModel):
    """One stable mount binding for a containerized workflow step."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    target_path: str = Field(..., min_length=1)
    read_only: bool = True


class ContainerizedStepSpec(JsonModel):
    """Container execution plan for one workflow step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    image: str = Field(..., min_length=1)
    command: tuple[str, ...] = Field(default_factory=tuple)
    mounts: tuple[ContainerMount, ...] = Field(default_factory=tuple)
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
    cpus: int = Field(..., ge=1)
    memory_gb: int = Field(..., ge=1)
    walltime_minutes: int = Field(..., ge=1)
    working_directory: str = Field(..., min_length=1)
    script_path: str = Field(..., min_length=1)
    script_text: str = Field(..., min_length=1)


class WorkflowCacheEntry(JsonModel):
    """One deterministic cache materialization contract."""

    model_config = ConfigDict(extra="forbid")

    cache_key: str = Field(..., min_length=64, max_length=64)
    surface: str = Field(..., min_length=1)
    source_roles: tuple[WorkflowInputRole, ...] = Field(default_factory=tuple)
    source_hashes: tuple[str, ...] = Field(default_factory=tuple)
    expected_artifacts: tuple[WorkflowArtifactKind, ...] = Field(default_factory=tuple)
    cache_path: str = Field(..., min_length=1)


class WorkflowCacheManifest(JsonModel):
    """Workflow-level cache contract over deterministic reusable surfaces."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    entries: tuple[WorkflowCacheEntry, ...] = Field(default_factory=tuple)


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
    expected_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowCheckpoint(JsonModel):
    """Checkpoint payload for resuming a workflow after completed steps."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    workflow_id: str = Field(..., min_length=1)
    completed_step_ids: tuple[str, ...] = Field(default_factory=tuple)
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
    streaming_policy: LargeFileStreamingPolicy
    parallel_plan: ParallelExecutionPlan
    checkpoint: WorkflowCheckpoint


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


def _sanitize_identifier(value: str) -> str:
    return (
        "".join(character if character.isalnum() else "-" for character in value)
        .strip("-")
        .lower()
    )


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
    if artifact_kind is WorkflowArtifactKind.DIGEST_MANIFEST:
        return "digest/manifest.json"
    if artifact_kind is WorkflowArtifactKind.DIGEST_EXPORT:
        return "digest/peptides.jsonl"
    if artifact_kind is WorkflowArtifactKind.SEARCH_JOB:
        return "search/submit.json"
    if artifact_kind is WorkflowArtifactKind.SEARCH_RESULTS:
        return "search/results.tsv"
    if artifact_kind is WorkflowArtifactKind.NORMALIZED_IDENTIFICATIONS:
        return "identifications.normalized.json"
    if artifact_kind is WorkflowArtifactKind.FDR_REPORT:
        return "fdr.report.json"
    if artifact_kind is WorkflowArtifactKind.QUANT_REPORT:
        return "quant.report.json"
    if artifact_kind is WorkflowArtifactKind.QC_REPORT:
        return "qc.report.json"
    if artifact_kind is WorkflowArtifactKind.RUN_BUNDLE:
        return "bundle/bundle.manifest.json"
    if artifact_kind is WorkflowArtifactKind.JOB_DESCRIPTOR:
        return f"jobs/{workflow_id}.slurm"
    if artifact_kind is WorkflowArtifactKind.CHECKPOINT:
        return f"checkpoints/{workflow_id}.json"
    return f"{artifact_kind.value}.json"


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
                "--out-dir",
                str(output_root / "bundle"),
            ),
            cacheable=False,
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
        "|".join(
            (
                manifest.execution_mode.value,
                manifest.scheduler.value,
                manifest.search_adapter_kind.value,
                manifest.default_container_image,
            )
        ).encode("utf-8")
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
        deterministic_execution_sha256=_stable_model_sha256(
            deterministic_execution
        ),
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
    mounts = tuple(
        ContainerMount(
            source_path=asset.path,
            target_path=f"/workspace/inputs/{Path(asset.path).name}",
            read_only=True,
        )
        for asset in manifest.input_assets
    ) + (
        ContainerMount(
            source_path=manifest.artifacts_dir,
            target_path="/workspace/artifacts",
            read_only=False,
        ),
    )
    return tuple(
        ContainerizedStepSpec(
            step_id=step.step_id,
            image=manifest.default_container_image,
            command=step.command_preview,
            mounts=mounts,
            network_policy="isolated",
            workdir="/workspace",
        )
        for step in manifest.steps
    )


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
) -> WorkflowCacheManifest:
    """Build deterministic cache keys for reusable workflow surfaces."""
    asset_by_role = {asset.role: asset for asset in manifest.input_assets}
    entries: list[WorkflowCacheEntry] = []
    cache_specs = [
        (
            "digestion",
            (WorkflowInputRole.PROTEINS,),
            (
                WorkflowArtifactKind.DIGEST_MANIFEST,
                WorkflowArtifactKind.DIGEST_EXPORT,
            ),
        ),
        (
            "search-normalization",
            (
                (WorkflowInputRole.IDENTIFICATIONS,)
                if WorkflowInputRole.IDENTIFICATIONS in asset_by_role
                else (WorkflowInputRole.SPECTRA,)
            ),
            (WorkflowArtifactKind.NORMALIZED_IDENTIFICATIONS,),
        ),
        (
            "spectra-parse",
            (WorkflowInputRole.SPECTRA,),
            (WorkflowArtifactKind.QC_REPORT,),
        ),
    ]
    if WorkflowInputRole.FEATURES in asset_by_role:
        cache_specs.append(
            (
                "quant-parse",
                (WorkflowInputRole.FEATURES,),
                (WorkflowArtifactKind.QUANT_REPORT,),
            )
        )
    for surface, roles, artifacts in cache_specs:
        source_hashes = tuple(asset_by_role[role].sha256 for role in roles)
        cache_key = hashlib.sha256(
            "|".join((manifest.workflow_id, surface, *source_hashes)).encode("utf-8")
        ).hexdigest()
        entries.append(
            WorkflowCacheEntry(
                cache_key=cache_key,
                surface=surface,
                source_roles=roles,
                source_hashes=source_hashes,
                expected_artifacts=artifacts,
                cache_path=f"{manifest.artifacts_dir}/cache/{surface}-{cache_key[:12]}.json",
            )
        )
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
) -> HpcJobDescriptor:
    """Export one scheduler-ready descriptor for the workflow bundle."""
    resolved_scheduler = scheduler or manifest.scheduler
    script_path = f"{manifest.artifacts_dir}/jobs/{manifest.workflow_id}.{resolved_scheduler.value}"
    lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
    if resolved_scheduler is WorkflowSchedulerKind.SLURM:
        lines.extend(
            [
                f"#SBATCH --job-name={manifest.workflow_id}",
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
    payload = HpcJobDescriptor(
        document_schema=_build_document_schema("hpc_job_descriptor"),
        scheduler=resolved_scheduler,
        workflow_id=manifest.workflow_id,
        job_name=manifest.workflow_id,
        cpus=4,
        memory_gb=16,
        walltime_minutes=120,
        working_directory=manifest.artifacts_dir,
        script_path=script_path,
        script_text=script_text,
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
        steps.append(
            WorkflowCheckpointStep(
                step_id=step.step_id,
                status=status,
                expected_artifact_ids=step_outputs.get(step.step_id, ()),
            )
        )
    payload = WorkflowCheckpoint(
        document_schema=_build_document_schema("workflow_checkpoint"),
        workflow_id=manifest.workflow_id,
        completed_step_ids=tuple(
            step_id for step_id in manifest.checkpointable_steps if step_id in completed
        ),
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
        streaming_policy=streaming_policy,
        parallel_plan=parallel_plan,
        checkpoint=checkpoint,
    )
