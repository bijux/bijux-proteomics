# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.external_exec_iteration13 import (
    ContainerNetworkMode,
    DockerMountDescriptor,
    build_docker_image_descriptor,
)


def test_build_docker_image_descriptor_tracks_mounts_resources_and_tools() -> None:
    descriptor = build_docker_image_descriptor(
        image_name="ghcr.io/bijux/proteomics-runtime",
        image_digest="sha256:" + "a" * 64,
        run_as_user="1000:1000",
        workdir="/workspace",
        mounts=(
            DockerMountDescriptor(
                host_path="/data/input",
                container_path="/workspace/input",
                read_only=True,
            ),
        ),
        network_mode=ContainerNetworkMode.NONE,
        cpu_limit=8.0,
        memory_gb_limit=32.0,
        tool_inventory=("sage", "diann", "python"),
    )

    assert descriptor.image_name.endswith("proteomics-runtime")
    assert descriptor.network_mode.value == "none"
    assert descriptor.tool_inventory[0] == "diann"
