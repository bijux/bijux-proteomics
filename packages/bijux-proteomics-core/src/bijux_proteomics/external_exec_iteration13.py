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
