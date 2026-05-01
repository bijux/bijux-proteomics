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
