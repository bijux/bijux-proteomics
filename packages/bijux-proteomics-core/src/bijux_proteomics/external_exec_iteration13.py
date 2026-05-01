# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""External execution and environment capability surfaces for iteration 13."""

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
        mounts=tuple(sorted(mounts, key=lambda mount: (mount.host_path, mount.container_path))),
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
