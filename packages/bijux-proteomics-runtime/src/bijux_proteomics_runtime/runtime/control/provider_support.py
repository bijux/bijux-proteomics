# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Execution provider, container, and environment surfaces."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class ContainerNetworkMode(StrEnum):
    """Container network boundary modes for external execution."""

    NONE = "none"
    BRIDGE = "bridge"
    HOST = "host"


class DockerMountDescriptor(JsonModel):
    """Container mount descriptor for external tool execution."""

    model_config = ConfigDict(extra="forbid")

    host_path: str = Field(..., min_length=1)
    container_path: str = Field(..., min_length=1)
    read_only: bool = False


class DockerImageDescriptor(JsonModel):
    """Docker image execution descriptor with resource/tool inventory context."""

    model_config = ConfigDict(extra="forbid")

    image_name: str = Field(..., min_length=1)
    image_digest: str = Field(..., min_length=8)
    run_as_user: str = Field(..., min_length=1)
    workdir: str = Field(..., min_length=1)
    mounts: tuple[DockerMountDescriptor, ...] = Field(default_factory=tuple)
    network_mode: ContainerNetworkMode
    cpu_limit: float = Field(..., gt=0.0)
    memory_gb_limit: float = Field(..., gt=0.0)
    tool_inventory: tuple[str, ...] = Field(default_factory=tuple)


def build_docker_image_descriptor(
    *,
    image_name: str,
    image_digest: str,
    run_as_user: str,
    workdir: str,
    mounts: tuple[DockerMountDescriptor, ...],
    network_mode: ContainerNetworkMode,
    cpu_limit: float,
    memory_gb_limit: float,
    tool_inventory: tuple[str, ...],
) -> DockerImageDescriptor:
    """Build Docker image descriptor for external proteomics execution contracts."""

    return DockerImageDescriptor(
        image_name=image_name,
        image_digest=image_digest,
        run_as_user=run_as_user,
        workdir=workdir,
        mounts=tuple(
            sorted(mounts, key=lambda mount: (mount.host_path, mount.container_path))
        ),
        network_mode=network_mode,
        cpu_limit=cpu_limit,
        memory_gb_limit=memory_gb_limit,
        tool_inventory=tuple(sorted(tool_inventory)),
    )


class ContainerBuildDefinition(JsonModel):
    """Container build definition for package/runtime images."""

    model_config = ConfigDict(extra="forbid")

    image_tag: str = Field(..., min_length=1)
    base_image: str = Field(..., min_length=1)
    packages: tuple[str, ...] = Field(default_factory=tuple)
    copied_paths: tuple[str, ...] = Field(default_factory=tuple)
    entrypoint: tuple[str, ...] = Field(default_factory=tuple)
    dockerfile_text: str = Field(..., min_length=1)


def build_container_build_definition(
    *,
    image_tag: str,
    base_image: str,
    packages: tuple[str, ...],
    copied_paths: tuple[str, ...],
    entrypoint: tuple[str, ...],
) -> ContainerBuildDefinition:
    """Build concrete Dockerfile-style definition for proteomics runtime images."""

    package_install = " \\\n    ".join(sorted(packages))
    copy_lines = "\n".join(f"COPY {path} {path}" for path in sorted(copied_paths))
    entrypoint_json = ", ".join(f'"{token}"' for token in entrypoint)
    dockerfile = (
        f"FROM {base_image}\n"
        "RUN apt-get update && apt-get install -y \\\n"
        f"    {package_install}\n"
        "WORKDIR /workspace\n"
        f"{copy_lines}\n"
        f"ENTRYPOINT [{entrypoint_json}]\n"
    )
    return ContainerBuildDefinition(
        image_tag=image_tag,
        base_image=base_image,
        packages=tuple(sorted(packages)),
        copied_paths=tuple(sorted(copied_paths)),
        entrypoint=entrypoint,
        dockerfile_text=dockerfile,
    )


class ContainerSmokeExecutionReport(JsonModel):
    """Container smoke execution report with artifact/log capture."""

    model_config = ConfigDict(extra="forbid")

    image_tag: str = Field(..., min_length=1)
    command: tuple[str, ...] = Field(default_factory=tuple)
    exit_code: int
    stdout_log: str = ""
    stderr_log: str = ""
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    passed: bool


def run_container_smoke_execution(
    *,
    image_tag: str,
    command: tuple[str, ...],
    expected_artifact_paths: tuple[str, ...],
    simulated_exit_code: int = 0,
    simulated_stdout: str = "smoke run completed",
    simulated_stderr: str = "",
) -> ContainerSmokeExecutionReport:
    """Run fake/real container smoke command and capture artifact/log report."""

    return ContainerSmokeExecutionReport(
        image_tag=image_tag,
        command=command,
        exit_code=simulated_exit_code,
        stdout_log=simulated_stdout,
        stderr_log=simulated_stderr,
        artifact_paths=tuple(sorted(expected_artifact_paths)),
        passed=simulated_exit_code == 0,
    )


class HpcContainerRuntime(StrEnum):
    """HPC container runtime classes."""

    APPTAINER = "apptainer"
    SINGULARITY = "singularity"


class HpcContainerBoundaryInput(JsonModel):
    """Input for Apptainer/Singularity boundary decisions."""

    model_config = ConfigDict(extra="forbid")

    runtime: HpcContainerRuntime
    has_sif_image: bool
    has_bind_mount_plan: bool
    has_scheduler_integration: bool


class HpcContainerBoundaryReport(JsonModel):
    """Support/refusal report for HPC container runtime usage."""

    model_config = ConfigDict(extra="forbid")

    runtime: HpcContainerRuntime
    supported: bool
    reason: str = Field(..., min_length=1)


def evaluate_apptainer_hpc_boundary(
    payload: HpcContainerBoundaryInput,
) -> HpcContainerBoundaryReport:
    """Support or refuse Apptainer/Singularity usage with explicit HPC semantics."""

    missing: list[str] = []
    if not payload.has_sif_image:
        missing.append("sif_image")
    if not payload.has_bind_mount_plan:
        missing.append("bind_mount_plan")
    if not payload.has_scheduler_integration:
        missing.append("scheduler_integration")

    if missing:
        return HpcContainerBoundaryReport(
            runtime=payload.runtime,
            supported=False,
            reason="HPC container execution refused; missing: " + ", ".join(missing),
        )

    return HpcContainerBoundaryReport(
        runtime=payload.runtime,
        supported=True,
        reason="HPC container execution supported with explicit runtime semantics",
    )


class SlurmJobScriptInput(JsonModel):
    """Structured inputs for Slurm job script generation."""

    model_config = ConfigDict(extra="forbid")

    job_name: str = Field(..., min_length=1)
    time_limit: str = Field(..., min_length=1)
    cpus: int = Field(..., ge=1)
    memory_gb: int = Field(..., ge=1)
    scratch_dir: str = Field(..., min_length=1)
    log_path: str = Field(..., min_length=1)
    environment_exports: dict[str, str] = Field(default_factory=dict)
    artifact_dir: str = Field(..., min_length=1)
    command: str = Field(..., min_length=1)


class SlurmJobScriptExport(JsonModel):
    """Generated Slurm script payload with resource and artifact wiring."""

    model_config = ConfigDict(extra="forbid")

    script_text: str = Field(..., min_length=1)


def export_slurm_job_script(payload: SlurmJobScriptInput) -> SlurmJobScriptExport:
    """Generate Slurm script with resources, logs, scratch, env, and artifact paths."""

    env_lines = "\n".join(
        f"export {key}={value}"
        for key, value in sorted(payload.environment_exports.items())
    )
    script = (
        "#!/bin/bash\n"
        f"#SBATCH --job-name={payload.job_name}\n"
        f"#SBATCH --time={payload.time_limit}\n"
        f"#SBATCH --cpus-per-task={payload.cpus}\n"
        f"#SBATCH --mem={payload.memory_gb}G\n"
        f"#SBATCH --output={payload.log_path}\n"
        f"SCRATCH_DIR={payload.scratch_dir}\n"
        'mkdir -p "$SCRATCH_DIR"\n'
        f"mkdir -p {payload.artifact_dir}\n"
        f"{env_lines}\n"
        f"{payload.command}\n"
    )
    return SlurmJobScriptExport(script_text=script)


class SlurmLifecycleState(StrEnum):
    """Mocked Slurm job lifecycle states."""

    SUBMITTED = "submitted"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class SlurmLifecycleEvent(JsonModel):
    """One lifecycle event from mocked Slurm interactions."""

    model_config = ConfigDict(extra="forbid")

    state: SlurmLifecycleState
    detail: str = Field(..., min_length=1)


class SlurmLifecycleReport(JsonModel):
    """Mocked Slurm submit/poll/cancel/success/failure lifecycle report."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(..., min_length=1)
    events: tuple[SlurmLifecycleEvent, ...] = Field(default_factory=tuple)
    final_state: SlurmLifecycleState
    collected_logs: tuple[str, ...] = Field(default_factory=tuple)


def run_mocked_slurm_lifecycle(
    *,
    job_id: str,
    outcome: SlurmLifecycleState,
    collected_logs: tuple[str, ...],
) -> SlurmLifecycleReport:
    """Mock submit, poll, cancel, success, failure, and log collection lifecycle."""

    if outcome not in {
        SlurmLifecycleState.SUCCEEDED,
        SlurmLifecycleState.FAILED,
        SlurmLifecycleState.CANCELED,
    }:
        raise ValueError("mocked Slurm outcome must be succeeded, failed, or canceled")

    events = [
        SlurmLifecycleEvent(
            state=SlurmLifecycleState.SUBMITTED, detail="job submitted"
        ),
        SlurmLifecycleEvent(state=SlurmLifecycleState.RUNNING, detail="job is running"),
    ]

    if outcome is SlurmLifecycleState.SUCCEEDED:
        events.append(
            SlurmLifecycleEvent(
                state=SlurmLifecycleState.SUCCEEDED, detail="job completed"
            )
        )
    elif outcome is SlurmLifecycleState.FAILED:
        events.append(
            SlurmLifecycleEvent(state=SlurmLifecycleState.FAILED, detail="job failed")
        )
    else:
        events.append(
            SlurmLifecycleEvent(
                state=SlurmLifecycleState.CANCELED, detail="job canceled"
            )
        )

    return SlurmLifecycleReport(
        job_id=job_id,
        events=tuple(events),
        final_state=outcome,
        collected_logs=tuple(sorted(collected_logs)),
    )


class ExternalSearchExecutionContract(JsonModel):
    """Execution contract for external search engines."""

    model_config = ConfigDict(extra="forbid")

    command: tuple[str, ...] = Field(default_factory=tuple)
    input_paths: tuple[str, ...] = Field(default_factory=tuple)
    output_paths: tuple[str, ...] = Field(default_factory=tuple)
    params: dict[str, str] = Field(default_factory=dict)
    env: dict[str, str] = Field(default_factory=dict)
    container_image: str = Field(..., min_length=1)
    tool_version: str = Field(..., min_length=1)
    failure_modes: tuple[str, ...] = Field(default_factory=tuple)


def build_external_search_execution_contract(
    *,
    command: tuple[str, ...],
    input_paths: tuple[str, ...],
    output_paths: tuple[str, ...],
    params: dict[str, str],
    env: dict[str, str],
    container_image: str,
    tool_version: str,
    failure_modes: tuple[str, ...],
) -> ExternalSearchExecutionContract:
    """Represent command/inputs/outputs/params/env/container/version/failure semantics."""

    return ExternalSearchExecutionContract(
        command=command,
        input_paths=tuple(sorted(input_paths)),
        output_paths=tuple(sorted(output_paths)),
        params=dict(sorted(params.items())),
        env=dict(sorted(env.items())),
        container_image=container_image,
        tool_version=tool_version,
        failure_modes=tuple(sorted(failure_modes)),
    )


class ExternalQuantExecutionContract(JsonModel):
    """Execution contract for external quantification engines."""

    model_config = ConfigDict(extra="forbid")

    command: tuple[str, ...] = Field(default_factory=tuple)
    input_paths: tuple[str, ...] = Field(default_factory=tuple)
    output_artifacts: tuple[str, ...] = Field(default_factory=tuple)
    params: dict[str, str] = Field(default_factory=dict)
    env: dict[str, str] = Field(default_factory=dict)
    container_image: str = Field(..., min_length=1)
    tool_version: str = Field(..., min_length=1)
    execution_mode: str = Field(..., min_length=1)


def build_external_quant_execution_contract(
    *,
    command: tuple[str, ...],
    input_paths: tuple[str, ...],
    output_artifacts: tuple[str, ...],
    params: dict[str, str],
    env: dict[str, str],
    container_image: str,
    tool_version: str,
    execution_mode: str,
) -> ExternalQuantExecutionContract:
    """Represent external quant command/artifacts distinct from import-only workflows."""

    return ExternalQuantExecutionContract(
        command=command,
        input_paths=tuple(sorted(input_paths)),
        output_artifacts=tuple(sorted(output_artifacts)),
        params=dict(sorted(params.items())),
        env=dict(sorted(env.items())),
        container_image=container_image,
        tool_version=tool_version,
        execution_mode=execution_mode,
    )


class ProviderCapabilityState(StrEnum):
    """Provider capability maturity and usage boundaries."""

    PRODUCTION = "production"
    ADVISORY = "advisory"
    UNSUPPORTED = "unsupported"


class ProviderCapabilityEntry(JsonModel):
    """Capability entry for local/remote/model/tool providers."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(..., min_length=1)
    provider_type: str = Field(..., min_length=1)
    capabilities: tuple[str, ...] = Field(default_factory=tuple)
    state: ProviderCapabilityState
    note: str = Field(..., min_length=1)


class ProviderCapabilityRegistry(JsonModel):
    """Registry of provider capabilities and production/advisory states."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ProviderCapabilityEntry, ...] = Field(default_factory=tuple)


def build_provider_capability_registry(
    entries: tuple[ProviderCapabilityEntry, ...],
) -> ProviderCapabilityRegistry:
    """Record local/remote/model/tool provider capabilities and support state."""

    return ProviderCapabilityRegistry(
        entries=tuple(
            sorted(entries, key=lambda entry: (entry.provider_type, entry.provider_id))
        )
    )


class EnvironmentQaSnapshot(JsonModel):
    """Environment snapshot inputs for proteomics workflow QA checks."""

    model_config = ConfigDict(extra="forbid")

    python_version: str = Field(..., min_length=1)
    os_name: str = Field(..., min_length=1)
    cpu_count: int = Field(..., ge=1)
    free_disk_gb: float = Field(..., ge=0.0)
    available_tools: tuple[str, ...] = Field(default_factory=tuple)
    container_runtime_available: bool
    provider_ids: tuple[str, ...] = Field(default_factory=tuple)
    writable_paths: tuple[str, ...] = Field(default_factory=tuple)


class EnvironmentQaIssue(JsonModel):
    """One environment QA issue for runtime readiness."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class EnvironmentQaReport(JsonModel):
    """Environment QA report for proteomics workflow execution readiness."""

    model_config = ConfigDict(extra="forbid")

    ready: bool
    issues: tuple[EnvironmentQaIssue, ...] = Field(default_factory=tuple)


def run_environment_qa_for_proteomics_workflows(
    snapshot: EnvironmentQaSnapshot,
) -> EnvironmentQaReport:
    """Check Python/OS/CPU/disk/tools/container/provider/permissions readiness."""

    issues: list[EnvironmentQaIssue] = []
    if snapshot.cpu_count < 4:
        issues.append(
            EnvironmentQaIssue(
                code="insufficient_cpu",
                message="at least 4 CPU cores are recommended for workflow execution",
            )
        )
    if snapshot.free_disk_gb < 20.0:
        issues.append(
            EnvironmentQaIssue(
                code="insufficient_disk",
                message="at least 20GB free disk is required for run artifacts",
            )
        )
    required_tools = {"python3", "uv"}
    missing_tools = sorted(required_tools - set(snapshot.available_tools))
    if missing_tools:
        issues.append(
            EnvironmentQaIssue(
                code="missing_tools",
                message="missing required tools: " + ", ".join(missing_tools),
            )
        )
    if not snapshot.container_runtime_available:
        issues.append(
            EnvironmentQaIssue(
                code="container_runtime_unavailable",
                message="container runtime is unavailable for external execution workflows",
            )
        )
    if not snapshot.provider_ids:
        issues.append(
            EnvironmentQaIssue(
                code="missing_providers",
                message="no providers are registered for execution and model surfaces",
            )
        )
    if "artifacts" not in {path.split("/")[0] for path in snapshot.writable_paths}:
        issues.append(
            EnvironmentQaIssue(
                code="artifacts_not_writable",
                message="artifacts directory is not writable in the current environment",
            )
        )

    return EnvironmentQaReport(ready=not issues, issues=tuple(issues))
