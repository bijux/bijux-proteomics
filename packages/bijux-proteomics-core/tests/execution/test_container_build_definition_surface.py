# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.providers.environment import build_container_build_definition


def test_build_container_build_definition_renders_dockerfile_text() -> None:
    definition = build_container_build_definition(
        image_tag="bijux-proteomics:runtime",
        base_image="ubuntu:24.04",
        packages=("python3", "curl"),
        copied_paths=("packages", "configs"),
        entrypoint=("python3", "-m", "bijux_proteomics.interfaces.cli"),
    )

    assert definition.image_tag == "bijux-proteomics:runtime"
    assert "FROM ubuntu:24.04" in definition.dockerfile_text
    assert "ENTRYPOINT" in definition.dockerfile_text
